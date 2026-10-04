"""The independent two-field probe is tested with simulated responses only."""

import contextlib
import importlib.util
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
SPEC = importlib.util.spec_from_file_location("probe_minimal_schema",
                                               ROOT / "scripts" / "probe_minimal_schema.py")
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)

from music_intent.openrouter_client import build_request  # noqa: E402


def envelope(content, finish_reason="stop"):
    return {"model": probe.MODEL,
            "choices": [{"finish_reason": finish_reason, "message": {"content": content}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120,
                      "completion_tokens_details": {"reasoning_tokens": 0}}}


class MinimalSchemaProbeTests(unittest.TestCase):
    def test_only_prompt_and_schema_differ_from_formal_request(self):
        formal = build_request(probe.SYNTHETIC_SENTENCE, probe.MODEL)
        minimal = probe.build_probe_request()
        self.assertEqual({key: value for key, value in minimal.items()
                          if key not in {"messages", "response_format"}},
                         {key: value for key, value in formal.items()
                          if key not in {"messages", "response_format"}})
        self.assertEqual(minimal["messages"][1], formal["messages"][1])
        self.assertNotEqual(minimal["messages"][0], formal["messages"][0])
        self.assertEqual(set(probe.PROBE_SCHEMA["required"]), {"mood", "constraints"})
        self.assertEqual(minimal["response_format"]["type"], "json_schema")
        self.assertIs(minimal["response_format"]["json_schema"]["strict"], True)
        self.assertNotIn("temperature", minimal)

    def test_valid_and_extremely_short_json(self):
        valid = probe.inspect_response(envelope('{"mood":"calm","constraints":[]}'))
        self.assertTrue(valid["required_fields_present"])
        self.assertTrue(valid["schema_valid"])
        self.assertEqual(valid["category"], "none")
        self.assertEqual(valid["usage"]["reasoning_tokens"], 0)
        empty = probe.inspect_response(envelope("{}"))
        self.assertFalse(empty["required_fields_present"])
        self.assertFalse(empty["schema_valid"])
        self.assertEqual(empty["category"], "missing_field:constraints,mood")

    def test_no_unknown_model_field_names_or_values_in_diagnostics(self):
        secret = "private model output"
        result = probe.inspect_response(envelope(json.dumps({"mood": "calm", "constraints": [],
                                                              "invented_private_field": secret})))
        self.assertEqual(result["category"], "extra_field")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            probe.report(result)
        self.assertNotIn("invented_private_field", output.getvalue())
        self.assertNotIn(secret, output.getvalue())
        self.assertNotIn(probe.SYNTHETIC_SENTENCE, output.getvalue())

    def test_length_and_bad_json_are_not_valid(self):
        truncated = probe.inspect_response(envelope('{"mood":"calm","constraints":[]}', "length"))
        self.assertTrue(truncated["required_fields_present"])
        self.assertFalse(truncated["schema_valid"])
        self.assertEqual(truncated["category"], "output_token_limit")
        malformed = probe.inspect_response(envelope("{bad json"))
        self.assertFalse(malformed["schema_valid"])
        self.assertEqual(malformed["category"], "invalid_content_json")

    def test_main_sends_one_simulated_call_without_formal_marker(self):
        fake_key = "sk-synthetic-never-print"
        body = json.dumps(envelope('{"mood":"calm","constraints":[]}')).encode("utf-8")
        output = io.StringIO()
        marker = ROOT / "data" / "connection_preflight.json"
        existed_before = marker.exists()
        with (patch.object(probe, "get_settings", return_value=(fake_key, probe.MODEL)),
              patch.object(probe, "urlopen", return_value=io.BytesIO(body)) as mocked,
              contextlib.redirect_stdout(output)):
            self.assertEqual(probe.main(), 0)
        self.assertEqual(mocked.call_count, 1)
        self.assertEqual(marker.exists(), existed_before)
        self.assertIn("schema_valid=true", output.getvalue())
        self.assertNotIn(fake_key, output.getvalue())
        self.assertNotIn(probe.SYNTHETIC_SENTENCE, output.getvalue())


if __name__ == "__main__":
    unittest.main()
