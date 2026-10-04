"""Offline-only tests for the independent paid comparison runner."""

from __future__ import annotations

import contextlib
import copy
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
sys.path.insert(0, str(ROOT / "prototypes"))
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location("evaluate_compact_dev", ROOT / "scripts" / "evaluate_compact_dev.py")
candidate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(candidate)

from compact_dev_request import build_candidate_request, load_versioned_format  # noqa: E402
from music_intent.openrouter_client import OpenRouterFailure, build_request  # noqa: E402


def response(content: object) -> dict:
    return {"model": candidate.MODEL,
            "usage": {"prompt_tokens": 20, "completion_tokens": 10, "total_tokens": 30,
                      "completion_tokens_details": {"reasoning_tokens": 0}},
            "choices": [{"finish_reason": "stop", "message": {"content": content}}]}


class CompactDevelopmentEvaluationTests(unittest.TestCase):
    def test_candidate_request_changes_only_prompt_and_schema(self):
        prompt, schema, digests = load_versioned_format()
        self.assertEqual(len(digests["prompt_sha256"]), 64)
        self.assertEqual(len(digests["schema_sha256"]), 64)
        answers, _ = candidate.read_dev_data()
        for answer in answers:
            original = build_request(answer["utterance"], candidate.MODEL)
            changed = build_candidate_request(answer["utterance"], candidate.MODEL, prompt, schema)
            self.assertEqual(changed["messages"][1], {"role": "user", "content": answer["utterance"]})
            self.assertEqual(changed["messages"][0]["role"], "system")
            expected = copy.deepcopy(original)
            expected["messages"][0]["content"] = prompt
            expected["response_format"]["json_schema"]["schema"] = schema
            self.assertEqual(changed, expected)
            self.assertEqual(changed["model"], candidate.MODEL)
            self.assertEqual(changed["max_tokens"], 2048)
            self.assertEqual(changed["reasoning"], {"effort": "minimal"})
            self.assertNotIn("temperature", changed)
            self.assertNotIn("review_status", json.dumps(changed, ensure_ascii=False))
            self.assertNotIn("case_id", json.dumps(changed, ensure_ascii=False))

    def test_response_stages_are_separate_and_raw_is_private_only(self):
        _, schema, _ = load_versioned_format()
        utterance = "I want to listen to quiet music"
        wire = {"current_valence": None, "current_arousal": None,
                "target_valence": None, "target_arousal": "=1",
                "target_melodic_surprise": None, "trajectory": "single_target",
                "requires_melody_present": None,
                "evidence": {name: None for name in candidate.CORE_FIELDS + ("requires_melody_present",)},
                "constraints": []}
        wire["evidence"]["target_arousal"] = "quiet"
        content = json.dumps(wire, ensure_ascii=False)
        record, private = candidate.inspect_candidate_response(
            response(content), "dev_001", utterance, candidate.MODEL, schema)
        self.assertTrue(record["json_complete"])
        self.assertTrue(record["required_structure_complete"])
        self.assertTrue(record["conversion_complete"])
        self.assertIsNotNone(record["intent"])
        self.assertEqual(record["usage"]["reasoning_tokens"], 0)
        self.assertEqual(private["raw_prediction"], content)
        self.assertNotIn("raw_prediction", record)
        self.assertEqual(private["converted_v2"]["target_arousal"], 1)

        malformed = copy.deepcopy(wire)
        malformed["target_arousal"] = "1"
        record, private = candidate.inspect_candidate_response(
            response(json.dumps(malformed, ensure_ascii=False)), "dev_001", utterance,
            candidate.MODEL, schema)
        self.assertTrue(record["required_structure_complete"])
        self.assertFalse(record["conversion_complete"])
        self.assertEqual(record["failure_group"], "structure")
        self.assertEqual(record["failure_stage"], "conversion")
        self.assertIsNone(private["converted_v2"])

        wrong_evidence = copy.deepcopy(wire)
        wrong_evidence["evidence"]["target_arousal"] = "Not present in sentence"
        record, private = candidate.inspect_candidate_response(
            response(json.dumps(wrong_evidence, ensure_ascii=False)), "dev_001", utterance,
            candidate.MODEL, schema)
        self.assertTrue(record["conversion_complete"])
        self.assertEqual(record["failure_group"], "evidence")
        self.assertIsNotNone(private["converted_v2"])

        record, private = candidate.inspect_candidate_response(response("{}"), "dev_001", utterance,
                                                                candidate.MODEL, schema)
        self.assertTrue(record["json_complete"])
        self.assertFalse(record["required_structure_complete"])
        self.assertEqual(record["failure_group"], "structure")
        self.assertEqual(private["raw_prediction"], "{}")

    def test_private_path_is_ignored_untracked_and_absent(self):
        candidate.verify_private_path(candidate.PRIVATE_DIR / "future_probe.jsonl")
        with tempfile.TemporaryDirectory(dir=ROOT / "reports") as directory:
            # A path outside the ignored directory is rejected before writing.
            with self.assertRaises(ValueError):
                candidate.verify_private_path(Path(directory) / "prediction.jsonl")

    def test_no_flag_never_loads_settings_or_calls_api(self):
        output = io.StringIO()
        with (patch.object(candidate, "get_settings", side_effect=AssertionError("settings read")),
              patch.object(candidate, "call_candidate_once", side_effect=AssertionError("API called")),
              contextlib.redirect_stdout(output)):
            self.assertEqual(candidate.main([]), 2)
        self.assertIn("authorization_required", output.getvalue())

    def test_three_structure_failures_stop_and_private_file_has_no_credentials(self):
        error = OpenRouterFailure("missing_field", usage={"prompt_tokens": 10, "completion_tokens": 1},
                                  model=candidate.MODEL, field="constraints",
                                  json_complete=True, required_structure_complete=False)
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            private_dir = folder / "private_dev_predictions"
            private_path = private_dir / "compact_dev_predictions.jsonl"
            patches = (patch.object(candidate, "REPORTS", folder),
                       patch.object(candidate, "PRIVATE_DIR", private_dir),
                       patch.object(candidate, "PRIVATE_FILE", private_path),
                       patch.object(candidate, "PUBLIC_JSON", folder / "compact_dev_evaluation.json"),
                       patch.object(candidate, "PUBLIC_MD", folder / "compact_dev_evaluation.md"),
                       patch.object(candidate, "verify_private_path"),
                       patch.object(candidate, "get_settings", return_value=("sk-fixture-secret", candidate.MODEL)),
                       patch.object(candidate, "call_candidate_once", side_effect=error))
            with contextlib.ExitStack() as stack:
                mocks = [stack.enter_context(item) for item in patches]
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    result = candidate.run()
            self.assertEqual(mocks[-1].call_count, 3)
            self.assertEqual(result["attempted_calls"], 3)
            self.assertTrue(result["stopped_early"])
            self.assertEqual(result["scores"]["end_to_end"]["denominator"], 3)
            self.assertEqual(result["scores"]["valid_only"]["denominator"], 0)
            self.assertEqual(result["failure_groups"], {"structure": 3})
            self.assertEqual(len(private_path.read_text(encoding="utf-8").splitlines()), 3)
            self.assertEqual(private_path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(private_dir.stat().st_mode & 0o777, 0o700)
            for text in (output.getvalue(), private_path.read_text(encoding="utf-8"),
                         (folder / "compact_dev_evaluation.md").read_text(encoding="utf-8")):
                self.assertNotIn("sk-fixture-secret", text)


if __name__ == "__main__":
    unittest.main()
