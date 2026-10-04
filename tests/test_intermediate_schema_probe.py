"""Offline comparison and safety tests for the isolated nine-field probe."""

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
    "probe_intermediate_schema", ROOT / "scripts" / "probe_intermediate_schema.py")
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)

from music_intent.intent import response_schema  # noqa: E402

VALID = {
    "current_valence": -1, "current_arousal": None,
    "target_valence": None, "target_arousal": 1,
    "target_melodic_surprise": None, "trajectory": "single_target",
    "requires_melody_present": True, "evidence": "安静", "constraints": [],
}


def envelope(item=VALID, finish_reason="stop"):
    content = item if isinstance(item, str) else json.dumps(item, ensure_ascii=False)
    return {"model": probe.MODEL,
            "choices": [{"finish_reason": finish_reason, "message": {"content": content}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 40, "total_tokens": 140,
                      "completion_tokens_details": {"reasoning_tokens": 0}}}


def contains_keyword(node, keyword):
    if isinstance(node, dict):
        return keyword in node or any(contains_keyword(value, keyword) for value in node.values())
    if isinstance(node, list):
        return any(contains_keyword(value, keyword) for value in node)
    return False


class IntermediateSchemaProbeTests(unittest.TestCase):
    def test_exact_schema_differences_and_nine_required_fields(self):
        current_formal = response_schema()
        formal = copy.deepcopy(current_formal)
        for name in ("current_valence", "current_arousal", "target_valence",
                     "target_arousal", "target_melodic_surprise"):
            node = (formal["properties"][name]["anyOf"][0]
                    if name in {"target_valence", "target_arousal"}
                    else formal["properties"][name])
            node["enum"] = [*sorted(probe.DOMAINS[name]), None]
        intermediate = probe.intermediate_schema()
        self.assertEqual(intermediate["required"], formal["required"])
        self.assertEqual(len(intermediate["required"]), 9)
        self.assertEqual(intermediate["type"], "object")
        self.assertIs(intermediate["additionalProperties"], False)
        self.assertEqual(set(intermediate["properties"]), set(formal["properties"]))
        changed = {name for name in formal["properties"]
                   if formal["properties"][name] != intermediate["properties"][name]}
        self.assertEqual(changed, {"target_valence", "target_arousal", "trajectory",
                                   "evidence", "constraints"})
        for name in ("target_valence", "target_arousal", "trajectory"):
            self.assertEqual(intermediate["properties"][name],
                             formal["properties"][name]["anyOf"][0])
        self.assertEqual(intermediate["properties"]["evidence"]["type"], ["string", "null"])
        self.assertEqual(intermediate["properties"]["constraints"]["items"], {"type": "string"})
        self.assertFalse(contains_keyword(intermediate, "anyOf"))
        self.assertNotIn('"type": "object"',
                         json.dumps(list(intermediate["properties"].values()), ensure_ascii=False))
        self.assertEqual(response_schema(), current_formal)  # No mutation of current runtime schema.

    def test_request_only_changes_schema_from_previous_short_prompt_probe(self):
        previous_spec = importlib.util.spec_from_file_location(
            "probe_full_schema_short_prompt", ROOT / "scripts" / "probe_full_schema_short_prompt.py")
        previous = importlib.util.module_from_spec(previous_spec)
        previous_spec.loader.exec_module(previous)
        request = probe.build_probe_request()
        expected = copy.deepcopy(previous.build_probe_request())
        expected["response_format"]["json_schema"]["schema"] = probe.intermediate_schema()
        self.assertEqual(request, expected)
        self.assertEqual(request["messages"][1]["content"], probe.SYNTHETIC_SENTENCE)
        self.assertEqual(request["response_format"]["json_schema"]["strict"], True)
        self.assertEqual(request["provider"], {"require_parameters": True})
        self.assertEqual(request["reasoning"], {"effort": "minimal"})
        self.assertEqual(request["max_tokens"], 2048)
        self.assertNotIn("temperature", request)

    def test_required_fields_schema_and_evidence_are_reported_separately(self):
        good = probe.inspect_response(envelope())
        self.assertTrue(good["json_complete"])
        self.assertTrue(good["required_fields_present"])
        self.assertTrue(good["schema_valid"])
        self.assertTrue(good["evidence_valid"])
        self.assertEqual(good["category"], "none")
        self.assertEqual(good["usage"]["reasoning_tokens"], 0)
        missing = probe.inspect_response(envelope({}))
        self.assertEqual(set(missing["missing_fields"]), set(response_schema()["required"]))
        self.assertFalse(missing["schema_valid"])
        self.assertEqual(missing["category"], "missing_field")
        no_evidence = copy.deepcopy(VALID)
        no_evidence["evidence"] = "not from user text"
        result = probe.inspect_response(envelope(no_evidence))
        self.assertTrue(result["schema_valid"])
        self.assertFalse(result["evidence_valid"])
        self.assertEqual(result["category"], "evidence_not_in_utterance")

    def test_unknown_content_never_enters_safe_report(self):
        secret = "untrusted private output"
        item = copy.deepcopy(VALID)
        item["unknown_private_key"] = secret
        result = probe.inspect_response(envelope(item))
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            probe.report(result)
        self.assertEqual(result["category"], "extra_field")
        self.assertNotIn("unknown_private_key", output.getvalue())
        self.assertNotIn(secret, output.getvalue())
        self.assertNotIn(probe.SYNTHETIC_SENTENCE, output.getvalue())

    def test_no_call_without_future_authorization_and_no_formal_marker(self):
        marker = ROOT / "data" / "connection_preflight.json"
        original = marker.read_bytes() if marker.exists() else None
        output = io.StringIO()
        with (patch.object(probe, "get_settings", side_effect=AssertionError("settings were read")),
              patch.object(probe, "urlopen", side_effect=AssertionError("network was called")),
              contextlib.redirect_stdout(output)):
            self.assertEqual(probe.main([]), 2)
        self.assertIn("authorization_required", output.getvalue())
        self.assertEqual(marker.read_bytes() if marker.exists() else None, original)

    def test_one_simulated_call_and_no_formal_marker(self):
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
        self.assertIn("schema_valid=true", output.getvalue())
        self.assertNotIn(fake_key, output.getvalue())


if __name__ == "__main__":
    unittest.main()
