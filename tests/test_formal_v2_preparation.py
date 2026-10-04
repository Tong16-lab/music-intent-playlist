"""Only artificial fixtures; never call the API or run the 30 formal sentences."""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "prototypes"))
sys.path.insert(0, str(ROOT / "scripts"))

import evaluate  # noqa: E402
from compact_dev_request import build_candidate_request, load_versioned_format  # noqa: E402
from compact_dev_v2_request import VERSION, build_v2_request, load_v2_format  # noqa: E402
from music_intent.intent import EVIDENCE_FIELDS  # noqa: E402
from music_intent.openrouter_client import OpenRouterFailure  # noqa: E402
from music_intent.scoring_v3 import SCORE_VERSION  # noqa: E402


class FormalV2PreparationTests(unittest.TestCase):
    def test_version_is_exactly_v2_and_request_diff_is_prompt_only(self):
        v1_prompt, v1_schema, _ = load_versioned_format()
        v2_prompt, v2_schema, digests = load_v2_format()
        utterance = "人工合成的离线夹具句"
        v1_request = build_candidate_request(utterance, evaluate.MODEL, v1_prompt, v1_schema)
        v2_request = build_v2_request(utterance, evaluate.MODEL, v2_prompt, v2_schema)
        self.assertEqual(VERSION, "compact-dev-v2")
        self.assertEqual(evaluate.CANDIDATE_VERSION, VERSION)
        self.assertEqual(evaluate.SCORE_VERSION, SCORE_VERSION)
        self.assertEqual(v1_schema, v2_schema)
        self.assertEqual(v1_request["response_format"], v2_request["response_format"])
        self.assertNotEqual(v1_request["messages"][0]["content"], v2_request["messages"][0]["content"])
        v1_request["messages"][0]["content"] = v2_prompt
        self.assertEqual(v1_request, v2_request)
        self.assertEqual(len(digests["prompt_sha256"]), 64)
        evaluate.verify_candidate_format(digests)
        with self.assertRaisesRegex(ValueError, "compact_dev_v2_format_changed"):
            evaluate.verify_candidate_format({**digests, "prompt_sha256": "0" * 64})
        with self.assertRaisesRegex(ValueError, "compact_dev_v2_format_changed"):
            evaluate.verify_candidate_format({**digests, "schema_sha256": "0" * 64})
        self.assertEqual(v2_request["max_tokens"], 2048)
        self.assertEqual(v2_request["reasoning"], {"effort": "minimal"})
        self.assertNotIn("temperature", v2_request)

    def test_paid_entry_points_are_inert_without_explicit_flags(self):
        output = io.StringIO()
        with (patch.object(evaluate, "get_settings", side_effect=AssertionError("settings read")),
              patch.object(evaluate.candidate_runner, "call_candidate_once",
                           side_effect=AssertionError("API called")),
              contextlib.redirect_stdout(output)):
            self.assertEqual(evaluate.main([]), 2)
        self.assertIn("authorization_required", output.getvalue())

    def test_second_run_cli_selects_new_paths_without_touching_first(self):
        with (patch.object(evaluate, "run", return_value={}) as runner,
              contextlib.redirect_stdout(io.StringIO())):
            self.assertEqual(evaluate.main(["--allow-paid-formal", "--run-id", "second"]), 0)
        runner.assert_called_once_with(
            output_dir=evaluate.SECOND_REPORTS,
            private_path=evaluate.SECOND_PRIVATE_FILE,
            run_label="冻结后第二次正式运行")
        self.assertNotEqual(evaluate.SECOND_REPORTS, evaluate.REPORTS)
        self.assertNotEqual(evaluate.SECOND_PRIVATE_FILE, evaluate.PRIVATE_FILE)

    def test_previous_failed_run_is_pinned_without_exposing_prediction_text(self):
        previous = evaluate.verify_previous_run()
        self.assertEqual(previous["attempted_calls"], 3)
        self.assertEqual(previous["valid_responses"], 0)
        self.assertEqual(previous["stop_category"], "three_consecutive_network_failures")
        self.assertIn("reports/evaluation.json", previous["files_sha256"])
        self.assertIn("reports/private_formal_predictions/compact_v2_formal_predictions.jsonl",
                      previous["files_sha256"])
        self.assertNotIn("raw_prediction", str(previous))

    def test_formal_runner_counts_one_failed_artificial_fixture_without_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            private_dir = folder / "private_formal_predictions"
            private_file = private_dir / "predictions.jsonl"
            answers = []
            conditions = []
            for number in range(1, 31):
                case_id = f"test_{number:03d}"
                utterance = f"离线夹具编号 {number:02d}"
                answers.append({"case_id": case_id, "utterance": utterance,
                                "split": "test", "review_status": "approved",
                                "current_valence": "", "current_arousal": "",
                                "target_valence": "", "target_arousal": "",
                                "target_melodic_surprise": "", "trajectory": "none",
                                "requires_melody_present": ""})
                conditions.append({"case_id": case_id, "utterance": utterance,
                                   "review_status": "approved",
                                   "unsupported_condition_phrases": "[]",
                                   "expected_cannot_guarantee_constraint": "false"})
            wire = {"current_valence": None, "current_arousal": None,
                    "target_valence": None, "target_arousal": None,
                    "target_melodic_surprise": None, "trajectory": "none",
                    "requires_melody_present": None,
                    "evidence": {name: None for name in EVIDENCE_FIELDS},
                    "constraints": []}
            content = json.dumps(wire, ensure_ascii=False)
            payload = {"model": evaluate.MODEL,
                       "usage": {"prompt_tokens": 10, "completion_tokens": 5,
                                 "total_tokens": 15,
                                 "completion_tokens_details": {"reasoning_tokens": 0}},
                       "choices": [{"finish_reason": "stop", "message": {"content": content}}]}
            manifest = folder / "fixture_freeze.json"
            manifest.write_text(json.dumps({"files": {"fixture": "sha"}}), encoding="utf-8")
            def fixture_csv(path):
                return answers if path.name == "synthetic_intents_test.csv" else conditions
            patches = (
                patch.object(evaluate, "verify_manifest"), patch.object(evaluate, "validate_all"),
                patch.object(evaluate, "get_settings", return_value=("sk-fixture-secret", evaluate.MODEL)),
                patch.object(evaluate, "read_csv", side_effect=fixture_csv),
                patch.object(evaluate, "code_hashes", return_value={"fixture": "sha"}),
                patch.object(evaluate, "REPORTS", folder),
                patch.object(evaluate, "STARTED", folder / "started.json"),
                patch.object(evaluate, "TRACE", folder / "safe_trace.jsonl"),
                patch.object(evaluate, "RESULT", folder / "result.json"),
                patch.object(evaluate, "MARKDOWN", folder / "result.md"),
                patch.object(evaluate, "PRIVATE_DIR", private_dir),
                patch.object(evaluate, "PRIVATE_FILE", private_file),
                patch.object(evaluate, "MANIFEST", manifest),
                patch.object(evaluate.candidate_runner, "verify_private_path"),
                patch.object(evaluate.candidate_runner, "call_candidate_once",
                             side_effect=[OpenRouterFailure("missing_content", model=evaluate.MODEL)]
                             + [payload] * 29),
            )
            with contextlib.ExitStack() as stack:
                mocks = [stack.enter_context(p) for p in patches]
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    result = evaluate.run()
            self.assertEqual(mocks[-1].call_count, 30)
            self.assertEqual(result["candidate_version"], "compact-dev-v2")
            self.assertEqual(result["scores"]["score_version"], SCORE_VERSION)
            self.assertEqual(result["scores"]["stages"], {
                "api_success": 29, "json_complete": 29,
                "required_structure_complete": 29, "conversion_complete": 29,
                "local_valid": 29})
            self.assertEqual(result["scores"]["core_cards"]["end_to_end_correct"], 29)
            self.assertEqual(result["scores"]["core_cards"]["end_to_end_denominator"], 30)
            self.assertEqual(result["scores"]["core_cards"]["valid_denominator"], 29)
            self.assertEqual(result["scores"]["unsupported"]["status_end_to_end_correct"], 29)
            self.assertEqual(result["scores"]["unsupported"]["exact_set_end_to_end_correct"], 29)
            self.assertEqual(private_file.stat().st_mode & 0o777, 0o600)
            self.assertEqual(private_dir.stat().st_mode & 0o777, 0o700)
            self.assertEqual(len(private_file.read_text(encoding="utf-8").splitlines()), 30)
            trace = (folder / "safe_trace.jsonl").read_text(encoding="utf-8")
            self.assertNotIn("raw_prediction", trace)
            self.assertNotIn("utterance", trace)
            self.assertNotIn(content, trace)
            self.assertNotIn("sk-fixture-secret", trace + output.getvalue())

    def test_three_consecutive_api_failures_stop_and_keep_all_thirty_in_denominator(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            answers = [{"case_id": f"test_{number:03d}", "utterance": f"离线夹具 {number}",
                        "review_status": "approved", "current_valence": "", "current_arousal": "",
                        "target_valence": "", "target_arousal": "", "target_melodic_surprise": "",
                        "trajectory": "none", "requires_melody_present": ""}
                       for number in range(1, 31)]
            conditions = [{"case_id": row["case_id"], "utterance": row["utterance"],
                           "review_status": "approved", "unsupported_condition_phrases": "[]",
                           "expected_cannot_guarantee_constraint": "false"} for row in answers]
            manifest = folder / "freeze.json"
            manifest.write_text(json.dumps({"files": {"fixture": "sha"}}), encoding="utf-8")
            private = folder / "private_formal_predictions" / "predictions.jsonl"
            patches = (
                patch.object(evaluate, "verify_manifest"), patch.object(evaluate, "validate_all"),
                patch.object(evaluate, "get_settings", return_value=("fixture-secret", evaluate.MODEL)),
                patch.object(evaluate, "read_csv",
                             side_effect=lambda path: answers if path.name == "synthetic_intents_test.csv" else conditions),
                patch.object(evaluate, "REPORTS", folder),
                patch.object(evaluate, "STARTED", folder / "started.json"),
                patch.object(evaluate, "TRACE", folder / "trace.jsonl"),
                patch.object(evaluate, "RESULT", folder / "result.json"),
                patch.object(evaluate, "MARKDOWN", folder / "result.md"),
                patch.object(evaluate, "PRIVATE_DIR", private.parent),
                patch.object(evaluate, "PRIVATE_FILE", private),
                patch.object(evaluate, "MANIFEST", manifest),
                patch.object(evaluate.candidate_runner, "verify_private_path"),
                patch.object(evaluate.candidate_runner, "call_candidate_once",
                             side_effect=[OpenRouterFailure("network", model=evaluate.MODEL) for _ in range(3)]),
            )
            with contextlib.ExitStack() as stack:
                mocks = [stack.enter_context(patch_item) for patch_item in patches]
                with contextlib.redirect_stdout(io.StringIO()):
                    result = evaluate.run()
            self.assertEqual(mocks[-1].call_count, 3)
            self.assertTrue(result["stopped_early"])
            self.assertEqual(result["scores"]["attempted_calls"], 3)
            self.assertEqual(result["scores"]["total_cases"], 30)
            self.assertEqual(result["scores"]["valid_responses"], 0)
            self.assertEqual(result["scores"]["fields"]["target_valence"]["end_to_end"],
                             {"correct": 0, "denominator": 30})
            self.assertEqual(result["scores"]["case_summaries"][-1]["error_category"],
                             "not_attempted_after_stop")
            self.assertEqual(len(private.read_text(encoding="utf-8").splitlines()), 3)
            self.assertEqual(len((folder / "trace.jsonl").read_text(encoding="utf-8").splitlines()), 3)


if __name__ == "__main__":
    unittest.main()
