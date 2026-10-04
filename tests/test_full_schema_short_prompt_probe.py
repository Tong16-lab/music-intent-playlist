"""Offline fixtures for the unchanged-schema, short-prompt diagnostic."""

import contextlib
import copy
import importlib.util
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
SPEC = importlib.util.spec_from_file_location(
    "probe_full_schema_short_prompt", ROOT / "scripts" / "probe_full_schema_short_prompt.py")
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)

from music_intent.intent import SYSTEM_PROMPT, response_schema  # noqa: E402
from music_intent.openrouter_client import build_request  # noqa: E402

VALID = {
    "current_valence": -1, "current_arousal": None,
    "target_valence": None, "target_arousal": 1,
    "target_melodic_surprise": None, "trajectory": "single_target",
    "requires_melody_present": True,
    "evidence": {
        "current_valence": "有点烦", "current_arousal": None,
        "target_valence": None, "target_arousal": "安静",
        "target_melodic_surprise": None,
        "trajectory": "想听一首安静、有清楚旋律的音乐",
        "requires_melody_present": "有清楚旋律",
    },
    "constraints": [],
}


def envelope(intent=VALID, finish_reason="stop"):
    content = intent if isinstance(intent, str) else json.dumps(intent, ensure_ascii=False)
    return {"model": probe.MODEL,
            "choices": [{"finish_reason": finish_reason, "message": {"content": content}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 40, "total_tokens": 140,
                      "completion_tokens_details": {"reasoning_tokens": 0}}}


class FullSchemaShortPromptTests(unittest.TestCase):
    def test_historical_request_keeps_recorded_prompt_and_enumerated_schema(self):
        formal = build_request(probe.SYNTHETIC_SENTENCE, probe.MODEL)
        diagnostic = probe.build_probe_request()
        expected = copy.deepcopy(formal)
        expected["messages"][0]["content"] = probe.PROMPT_FILE.read_text(encoding="utf-8")
        expected["response_format"]["json_schema"]["schema"] = probe.historical_schema()
        self.assertEqual(diagnostic, expected)
        self.assertEqual(diagnostic["response_format"]["json_schema"]["schema"],
                         probe.historical_schema())
        self.assertEqual(diagnostic["response_format"]["json_schema"]["strict"], True)
        self.assertEqual(diagnostic["provider"], {"require_parameters": True})
        self.assertEqual(diagnostic["reasoning"], {"effort": "minimal"})
        self.assertEqual(diagnostic["max_tokens"], 2048)
        self.assertNotIn("temperature", diagnostic)
        self.assertEqual(formal["messages"][0]["content"], SYSTEM_PROMPT)
        self.assertLess(len(expected["messages"][0]["content"]), len(SYSTEM_PROMPT))

    def test_all_known_required_fields_including_nested_are_reported(self):
        schema = response_schema()
        self.assertEqual(set(probe.missing_known_required(schema, {})), set(schema["required"]))
        item = copy.deepcopy(VALID)
        item["evidence"] = {}
        item["constraints"] = [{}]
        item["target_valence"] = {}
        self.assertEqual(set(probe.missing_known_required(schema, item)),
                         {*(f"evidence.{name}" for name in VALID["evidence"]),
                          "constraints[0].evidence", "constraints[0].classification",
                          "constraints[0].polarity", "target_valence.relation",
                          "target_valence.value"})

    def test_json_structure_and_local_evidence_are_separate(self):
        valid = probe.inspect_response(envelope())
        self.assertTrue(valid["json_complete"])
        self.assertTrue(valid["required_fields_present"])
        self.assertEqual(valid["local_validation"], "passed")
        self.assertEqual(valid["usage"]["reasoning_tokens"], 0)
        missing = probe.inspect_response(envelope({}))
        self.assertTrue(missing["json_complete"])
        self.assertFalse(missing["required_fields_present"])
        self.assertEqual(len(missing["missing_fields"]), 9)
        self.assertEqual(missing["local_validation"], "not_run")
        invalid_evidence = copy.deepcopy(VALID)
        invalid_evidence["evidence"]["target_arousal"] = "absent from sentence"
        result = probe.inspect_response(envelope(invalid_evidence))
        self.assertTrue(result["json_complete"])
        self.assertTrue(result["required_fields_present"])
        self.assertEqual(result["local_validation"], "failed")
        self.assertEqual(result["category"], "evidence_not_in_utterance")
        self.assertEqual(result["field"], "target_arousal")

    def test_unknown_fields_and_values_never_enter_report(self):
        secret = "untrusted generated text"
        item = copy.deepcopy(VALID)
        item["model_private_field"] = secret
        result = probe.inspect_response(envelope(item))
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            probe.report(result)
        self.assertEqual(result["local_validation"], "failed")
        self.assertEqual(result["category"], "extra_field")
        self.assertNotIn("model_private_field", output.getvalue())
        self.assertNotIn(secret, output.getvalue())
        self.assertNotIn(probe.SYNTHETIC_SENTENCE, output.getvalue())

    def test_incomplete_json_does_not_run_formal_validation(self):
        result = probe.inspect_response(envelope(VALID, finish_reason="length"))
        self.assertFalse(result["json_complete"])
        self.assertTrue(result["required_fields_present"])
        self.assertEqual(result["local_validation"], "not_run")
        self.assertEqual(result["category"], "output_token_limit")
        malformed = probe.inspect_response(envelope("{bad json"))
        self.assertFalse(malformed["json_complete"])
        self.assertIsNone(malformed["required_fields_present"])
        self.assertEqual(malformed["category"], "invalid_content_json")

    def test_main_uses_one_simulated_call_and_no_formal_marker(self):
        fake_key = "sk-fixture-never-print"
        output = io.StringIO()
        body = json.dumps(envelope()).encode("utf-8")
        marker = ROOT / "data" / "connection_preflight.json"
        before = marker.exists()
        with (patch.object(probe, "get_settings", return_value=(fake_key, probe.MODEL)),
              patch.object(probe, "urlopen", return_value=io.BytesIO(body)) as mocked,
              contextlib.redirect_stdout(output)):
            self.assertEqual(probe.main(), 0)
        self.assertEqual(mocked.call_count, 1)
        self.assertEqual(marker.exists(), before)
        self.assertIn("local_validation=passed", output.getvalue())
        self.assertNotIn(fake_key, output.getvalue())


if __name__ == "__main__":
    unittest.main()
