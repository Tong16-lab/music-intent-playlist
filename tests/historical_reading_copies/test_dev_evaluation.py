"""All development-run tests use simulated responses; no paid requests."""

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
SPEC = importlib.util.spec_from_file_location("evaluate_dev", ROOT / "scripts" / "evaluate_dev.py")
dev = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(dev)

from music_intent.openrouter_client import OpenRouterFailure, build_request  # noqa: E402


class DevelopmentEvaluationTests(unittest.TestCase):
    def test_incomplete_structure_takes_priority_over_value_category(self):
        self.assertEqual(dev.failure_group("invalid_field_value", False), "structure")
        self.assertEqual(dev.failure_group("invalid_field_value", True), "field_value")
        self.assertEqual(dev.failure_group("missing_evidence", True), "evidence")
        self.assertEqual(dev.valid_answer_mismatch_count([
            {"intent_valid": False},
            {"intent_valid": True, "wrong_core_fields": [],
             "requires_melody_present_wrong": False, "unsupported_exact_set_wrong": False,
             "cannot_guarantee_constraint_wrong": False},
            {"intent_valid": True, "wrong_core_fields": ["target_arousal"],
             "requires_melody_present_wrong": False, "unsupported_exact_set_wrong": False,
             "cannot_guarantee_constraint_wrong": False},
        ]), 1)

    def test_only_approved_dev_rows_and_v2_answers_are_loaded(self):
        answers, unsupported = dev.read_dev_data()
        self.assertEqual(len(answers), 12)
        self.assertEqual(len(unsupported), 12)
        self.assertEqual({row["case_id"] for row in answers}, dev.EXPECTED_IDS)
        self.assertTrue(all(row["split"] == "dev" and row["review_status"] == "approved"
                            for row in answers))
        self.assertTrue(all(row["case_id"].startswith("dev_") for row in unsupported))

    def test_no_flag_cannot_read_settings_or_call_api(self):
        output = io.StringIO()
        with (patch.object(dev, "get_settings", side_effect=AssertionError("settings read")),
              patch.object(dev, "parse_once", side_effect=AssertionError("API called")),
              contextlib.redirect_stdout(output)):
            self.assertEqual(dev.main([]), 2)
        self.assertIn("authorization_required", output.getvalue())

    def test_three_consecutive_structure_failures_stop_at_three_calls(self):
        error = OpenRouterFailure("missing_field", usage={"prompt_tokens": 10, "completion_tokens": 1},
                                  model="fixture/model", field="constraints", finish_reason="stop",
                                  json_complete=True, required_structure_complete=False)
        with tempfile.TemporaryDirectory() as directory:
            report_dir = Path(directory)
            output = io.StringIO()
            with (patch.object(dev, "get_settings", return_value=("sk-fixture-never-print", "fixture/model")),
                  patch.object(dev, "parse_once", side_effect=error) as mocked,
                  contextlib.redirect_stdout(output)):
                result = dev.run(report_dir)
            self.assertEqual(mocked.call_count, 3)
            self.assertTrue(result["stopped_early"])
            self.assertEqual(result["attempted_calls"], 3)
            self.assertEqual(result["json_complete_calls"], 3)
            self.assertEqual(result["required_structure_complete_calls"], 0)
            self.assertEqual(result["locally_valid_calls"], 0)
            self.assertEqual(result["failure_groups"], {"structure": 3})
            self.assertEqual(result["scores"]["end_to_end"]["denominator"], 3)
            self.assertEqual(result["scores"]["valid_only"]["denominator"], 0)
            self.assertIn("Correct／12", (report_dir / "dev_evaluation.md").read_text(encoding="utf-8"))
            self.assertNotIn("sk-fixture-never-print", output.getvalue())
            self.assertNotIn("utterance", (report_dir / "dev_evaluation.trace.jsonl").read_text())
            self.assertFalse((ROOT / "data" / "connection_preflight.json").exists())

    def test_three_incomplete_structures_stop_even_with_field_value_category(self):
        error = OpenRouterFailure("invalid_field_value", usage={"prompt_tokens": 10},
                                  model="fixture/model", field="target_arousal", finish_reason="stop",
                                  json_complete=True, required_structure_complete=False)
        with tempfile.TemporaryDirectory() as directory:
            with (patch.object(dev, "get_settings", return_value=("sk-fixture", "fixture/model")),
                  patch.object(dev, "parse_once", side_effect=error) as mocked,
                  contextlib.redirect_stdout(io.StringIO())):
                result = dev.run(Path(directory))
            self.assertEqual(mocked.call_count, 3)
            self.assertTrue(result["stopped_early"])
            self.assertEqual(result["failure_groups"], {"structure": 3})

    def test_safe_reclassification_does_not_call_api(self):
        error = OpenRouterFailure("invalid_field_value", usage={"prompt_tokens": 10},
                                  model="fixture/model", field="target_arousal", finish_reason="stop",
                                  json_complete=True, required_structure_complete=False)
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            with (patch.object(dev, "get_settings", return_value=("sk-fixture", "fixture/model")),
                  patch.object(dev, "parse_once", side_effect=error),
                  contextlib.redirect_stdout(io.StringIO())):
                dev.run(folder)
            trace_path = folder / "dev_evaluation.trace.jsonl"
            result_path = folder / "dev_evaluation.json"
            trace = [json.loads(line) for line in trace_path.read_text().splitlines()]
            result = json.loads(result_path.read_text())
            for row in trace:
                row["failure_group"] = "field_value"
            for case in result["case_summaries"]:
                case["failure_group"] = "field_value"
            result["failure_groups"] = {"field_value": 3}
            trace_path.write_text("".join(json.dumps(row) + "\n" for row in trace))
            result_path.write_text(json.dumps(result))
            with patch.object(dev, "parse_once", side_effect=AssertionError("API called")):
                corrected = dev.reconcile_safe_classification(folder)
            self.assertEqual(corrected["failure_groups"], {"structure": 3})
            self.assertTrue(corrected["classification_corrected_from_safe_trace"])

    def test_evidence_failure_does_not_trigger_structure_stop(self):
        error = OpenRouterFailure("missing_evidence", usage={"prompt_tokens": 10,
                                   "completion_tokens": 5}, model="fixture/model",
                                  field="trajectory", finish_reason="stop", json_complete=True,
                                  required_structure_complete=True)
        with tempfile.TemporaryDirectory() as directory:
            with (patch.object(dev, "get_settings", return_value=("sk-fixture", "fixture/model")),
                  patch.object(dev, "parse_once", side_effect=error) as mocked,
                  contextlib.redirect_stdout(io.StringIO())):
                result = dev.run(Path(directory))
            self.assertEqual(mocked.call_count, 12)
            self.assertFalse(result["stopped_early"])
            self.assertEqual(result["required_structure_complete_calls"], 12)
            self.assertEqual(result["failure_groups"], {"evidence": 12})

    def test_requests_use_only_dev_utterances_and_fixed_runtime_prompt(self):
        answers, _ = dev.read_dev_data()
        model = "google/gemini-3.5-flash-lite"
        for row in answers:
            request = build_request(row["utterance"], model)
            self.assertEqual(len(request["messages"]), 2)
            self.assertEqual(request["messages"][1], {"role": "user", "content": row["utterance"]})
            self.assertNotIn("review_status", json.dumps(request, ensure_ascii=False))
            self.assertNotIn("case_id", json.dumps(request, ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()
