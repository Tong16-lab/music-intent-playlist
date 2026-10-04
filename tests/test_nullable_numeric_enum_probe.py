"""Offline regression tests for the five-enum diagnostic request and safe handling."""

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
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location(
    "probe_nullable_numeric_enum", ROOT / "scripts" / "probe_nullable_numeric_enum.py")
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)

from music_intent.intent import response_schema  # noqa: E402
from probe_intermediate_schema import (  # noqa: E402
    build_probe_request as build_intermediate_request,
    inspect_response,
)

VALID = {
    "current_valence": -1, "current_arousal": None,
    "target_valence": None, "target_arousal": 1,
    "target_melodic_surprise": None, "trajectory": "single_target",
    "requires_melody_present": True, "evidence": "安静", "constraints": [],
}


def envelope(item=VALID):
    return {"model": probe.MODEL,
            "choices": [{"finish_reason": "stop", "message": {
                "content": json.dumps(item, ensure_ascii=False)}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 40, "total_tokens": 140,
                      "completion_tokens_details": {"reasoning_tokens": 0}}}


class NullableNumericEnumProbeTests(unittest.TestCase):
    def test_only_five_enum_keys_are_removed_from_request(self):
        before = build_intermediate_request()
        original = copy.deepcopy(before)
        after = probe.build_probe_request()
        expected = copy.deepcopy(before)
        before_fields = before["response_format"]["json_schema"]["schema"]["properties"]
        after_fields = after["response_format"]["json_schema"]["schema"]["properties"]
        for name in probe.NUMERIC_FIELDS:
            self.assertEqual(before_fields[name]["type"], ["integer", "null"])
            self.assertIn("enum", before_fields[name])
            self.assertNotIn("enum", after_fields[name])
            expected["response_format"]["json_schema"]["schema"]["properties"][name].pop("enum")
        self.assertEqual(after, expected)
        self.assertEqual(before, original)  # The earlier diagnostic request is not mutated.
        self.assertEqual(after["response_format"]["json_schema"]["schema"]["required"],
                         response_schema()["required"])
        self.assertEqual(len(after["response_format"]["json_schema"]["schema"]["required"]), 9)
        self.assertEqual(set(probe.NUMERIC_FIELDS), {
            "current_valence", "current_arousal", "target_valence", "target_arousal",
            "target_melodic_surprise"})
        self.assertEqual(after["messages"], before["messages"])
        self.assertEqual(after["model"], "google/gemini-3.5-flash-lite")
        self.assertEqual(after["max_tokens"], 2048)
        self.assertEqual(after["reasoning"], {"effort": "minimal"})
        self.assertNotIn("temperature", after)

    def test_local_numeric_domains_remain_strict(self):
        invalid = copy.deepcopy(VALID)
        invalid["target_arousal"] = 99
        result = inspect_response(envelope(invalid))
        self.assertTrue(result["json_complete"])
        self.assertTrue(result["required_fields_present"])
        self.assertFalse(result["schema_valid"])
        self.assertEqual(result["category"], "invalid_field_value")
        self.assertEqual(result["field"], "target_arousal")
        valid = inspect_response(envelope())
        self.assertTrue(valid["schema_valid"])
        self.assertTrue(valid["evidence_valid"])

    def test_missing_names_only_from_fixed_required_set_and_no_unknown_output(self):
        secret = "untrusted generated private value"
        result = inspect_response(envelope({"unknown_private_name": secret}))
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            probe.report(result)
        self.assertEqual(result["category"], "missing_field")
        self.assertEqual(set(result["missing_fields"]), set(response_schema()["required"]))
        self.assertNotIn("unknown_private_name", output.getvalue())
        self.assertNotIn(secret, output.getvalue())
        self.assertNotIn(probe.SYNTHETIC_SENTENCE, output.getvalue())

    def test_no_paid_flag_makes_no_call_and_no_marker(self):
        marker = ROOT / "data" / "connection_preflight.json"
        original = marker.read_bytes() if marker.exists() else None
        output = io.StringIO()
        with (patch.object(probe, "get_settings", side_effect=AssertionError("settings read")),
              patch.object(probe, "urlopen", side_effect=AssertionError("network called")),
              contextlib.redirect_stdout(output)):
            self.assertEqual(probe.main([]), 2)
        self.assertIn("authorization_required", output.getvalue())
        self.assertEqual(marker.read_bytes() if marker.exists() else None, original)

    def test_one_simulated_call_does_not_create_formal_marker(self):
        marker = ROOT / "data" / "connection_preflight.json"
        original = marker.read_bytes() if marker.exists() else None
        fake_key = "sk-fixture-never-print"
        body = json.dumps(envelope()).encode("utf-8")
        output = io.StringIO()
        with (patch.object(probe, "get_settings", return_value=(fake_key, probe.MODEL)),
              patch.object(probe, "urlopen", return_value=io.BytesIO(body)) as mocked,
              contextlib.redirect_stdout(output)):
            self.assertEqual(probe.main(["--allow-paid-probe"]), 0)
        self.assertEqual(mocked.call_count, 1)
        self.assertEqual(marker.read_bytes() if marker.exists() else None, original)
        self.assertIn("field_values_valid=true", output.getvalue())
        self.assertIn("evidence_valid=true", output.getvalue())
        self.assertNotIn(fake_key, output.getvalue())


if __name__ == "__main__":
    unittest.main()
