"""No paid calls: prompt-only request diff and v2 stop/report guards."""

from __future__ import annotations

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
sys.path.insert(0, str(ROOT / "prototypes"))
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location("evaluate_compact_dev_v2", ROOT / "scripts" / "evaluate_compact_dev_v2.py")
v2 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(v2)

from compact_dev_request import build_candidate_request, load_versioned_format  # noqa: E402
from compact_dev_v2_request import ADDITIONS, build_v2_request, expected_prompt_v2, load_v2_format  # noqa: E402
from music_intent.openrouter_client import OpenRouterFailure  # noqa: E402


class CompactPromptV2Tests(unittest.TestCase):
    def test_only_prompt_changes_relative_to_v1_request(self):
        v1_prompt, v1_schema, v1_digests = load_versioned_format()
        v2_prompt, v2_schema, v2_digests = load_v2_format()
        self.assertEqual(v2_prompt, expected_prompt_v2(v1_prompt))
        self.assertEqual(v2_schema, v1_schema)
        self.assertEqual(v2_digests["schema_sha256"], v1_digests["schema_sha256"])
        self.assertEqual(v2_digests["v1_prompt_sha256"], v1_digests["prompt_sha256"])
        self.assertEqual(len(ADDITIONS), 5)
        answers, _ = v2.v1_runner.read_dev_data()
        self.assertEqual(len(answers), 12)
        for row in answers:
            before = build_candidate_request(row["utterance"], v2.MODEL, v1_prompt, v1_schema)
            after = build_v2_request(row["utterance"], v2.MODEL, v2_prompt, v2_schema)
            self.assertEqual(after["messages"][1], before["messages"][1])
            self.assertEqual(after["response_format"], before["response_format"])
            before["messages"][0]["content"] = v2_prompt
            self.assertEqual(after, before)
            self.assertEqual(after["model"], "google/gemini-3.5-flash-lite")
            self.assertEqual(after["reasoning"], {"effort": "minimal"})
            self.assertEqual(after["max_tokens"], 2048)
            self.assertNotIn("temperature", after)
            self.assertNotIn("review_status", json.dumps(after, ensure_ascii=False))
            self.assertNotIn("case_id", json.dumps(after, ensure_ascii=False))

    def test_cost_estimate_and_private_git_guard(self):
        v1_prompt, _, _ = load_versioned_format()
        v2_prompt, _, _ = load_v2_format()
        v1_result = json.loads(v2.V1_JSON.read_text(encoding="utf-8"))
        estimate = v2.estimate_run_cost(v1_result, v1_prompt, v2_prompt)
        self.assertGreater(estimate["estimated_cost_usd"], 0)
        self.assertLess(estimate["estimated_cost_usd"], v2.MAX_ESTIMATED_COST_USD)
        v2.v1_runner.verify_private_path(v2.PRIVATE_DIR / "future_probe_v2.jsonl")
        self.assertNotEqual(v2.PRIVATE_FILE, v2.v1_runner.PRIVATE_FILE)

    def test_no_flag_never_reads_settings_or_calls_api(self):
        output = io.StringIO()
        with (patch.object(v2, "get_settings", side_effect=AssertionError("settings read")),
              patch.object(v2.v1_runner, "call_candidate_once", side_effect=AssertionError("API called")),
              contextlib.redirect_stdout(output)):
            self.assertEqual(v2.main([]), 2)
        self.assertIn("authorization_required", output.getvalue())

    def test_three_consecutive_structure_failures_stop_at_three(self):
        failure = OpenRouterFailure("missing_field", usage={"prompt_tokens": 10, "completion_tokens": 1},
                                    model=v2.MODEL, field="constraints",
                                    json_complete=True, required_structure_complete=False)
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            private_dir = folder / "private_dev_predictions"
            private_file = private_dir / "compact_dev_v2_predictions.jsonl"
            patches = (patch.object(v2, "REPORTS", folder),
                       patch.object(v2, "PRIVATE_DIR", private_dir),
                       patch.object(v2, "PRIVATE_FILE", private_file),
                       patch.object(v2, "PUBLIC_JSON", folder / "compact_dev_v2_evaluation.json"),
                       patch.object(v2, "PUBLIC_MD", folder / "compact_dev_v2_evaluation.md"),
                       patch.object(v2.v1_runner, "verify_private_path"),
                       patch.object(v2, "get_settings", return_value=("sk-fixture-secret", v2.MODEL)),
                       patch.object(v2.v1_runner, "call_candidate_once", side_effect=failure))
            with contextlib.ExitStack() as stack:
                mocks = [stack.enter_context(item) for item in patches]
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    result = v2.run()
            self.assertEqual(mocks[-1].call_count, 3)
            self.assertEqual(result["attempted_calls"], 3)
            self.assertTrue(result["stopped_early"])
            self.assertEqual(result["failure_groups"], {"structure": 3})
            self.assertEqual(result["scores"]["end_to_end"]["denominator"], 3)
            self.assertEqual(result["scores"]["valid_only"]["denominator"], 0)
            self.assertEqual(len(private_file.read_text(encoding="utf-8").splitlines()), 3)
            self.assertEqual(private_file.stat().st_mode & 0o777, 0o600)
            self.assertEqual(private_dir.stat().st_mode & 0o777, 0o700)
            for text in (output.getvalue(), private_file.read_text(encoding="utf-8"),
                         (folder / "compact_dev_v2_evaluation.md").read_text(encoding="utf-8")):
                self.assertNotIn("sk-fixture-secret", text)


if __name__ == "__main__":
    unittest.main()
