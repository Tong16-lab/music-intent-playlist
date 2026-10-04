"""Offline proof of the five-enum-only formal request change and preflight gate."""

import contextlib
import copy
import hashlib
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

from music_intent.intent import (  # noqa: E402
    DOMAINS, SYSTEM_PROMPT, InvalidIntent, response_schema, validate_intent,
)
from music_intent.openrouter_client import build_request  # noqa: E402
import music_intent.openrouter_client as client  # noqa: E402

SPEC = importlib.util.spec_from_file_location("connection_test", ROOT / "scripts" / "connection_test.py")
connection_test = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(connection_test)

MODEL = "google/gemini-3.5-flash-lite"
OLD_SCHEMA_SHA256 = "facad50f460470808b00794b64dd279f64eee3e1cfceb1dbfc9d6b9c7b4dd9cb"
OLD_PROMPT_SHA256 = "165d09ceb53c7f8b4d69102d115c6ebc3e112c8fba365f4bf9e91714d625dcae"
NUMERIC_FIELDS = (
    "current_valence", "current_arousal", "target_valence", "target_arousal",
    "target_melodic_surprise",
)
SENTENCE = connection_test.SYNTHETIC_SENTENCE
VALID = {
    "current_valence": -1, "current_arousal": None,
    "target_valence": None, "target_arousal": 1,
    "target_melodic_surprise": None, "trajectory": "single_target",
    "requires_melody_present": True,
    "evidence": {
        "current_valence": "somewhat annoyed", "current_arousal": None,
        "target_valence": None, "target_arousal": "quiet",
        "target_melodic_surprise": None,
        "trajectory": "I want to listen to some quiet music with a clear melody",
        "requires_melody_present": "clear melody present",
    },
    "constraints": [],
}


def envelope(intent):
    return {"model": MODEL,
            "choices": [{"finish_reason": "stop", "message": {
                "content": json.dumps(intent, ensure_ascii=False)}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 40, "total_tokens": 140,
                      "completion_tokens_details": {"reasoning_tokens": 0}}}


class FormalSchemaRevisionTests(unittest.TestCase):
    def test_model_guard_stops_before_network_or_marker(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "connection_preflight.json"
            output = io.StringIO()
            with (patch.object(connection_test, "PREFLIGHT", marker),
                  patch.object(connection_test, "get_settings", return_value=("sk-offline", "other/model")),
                  patch.object(client, "urlopen", side_effect=AssertionError("network called")),
                  patch.object(sys, "argv", ["connection_test.py", "--expected-model", MODEL]),
                  contextlib.redirect_stdout(output)):
                self.assertEqual(connection_test.main(), 2)
            self.assertFalse(marker.exists())
            self.assertIn("category=model_mismatch", output.getvalue())

    def test_only_five_nullable_numeric_enums_changed_from_old_schema(self):
        new = response_schema()
        rebuilt_old = copy.deepcopy(new)
        self.assertEqual(len(new["required"]), 9)
        for name in NUMERIC_FIELDS:
            node = (new["properties"][name]["anyOf"][0]
                    if name in {"target_valence", "target_arousal"}
                    else new["properties"][name])
            old_node = (rebuilt_old["properties"][name]["anyOf"][0]
                        if name in {"target_valence", "target_arousal"}
                        else rebuilt_old["properties"][name])
            self.assertEqual(node["type"], ["integer", "null"])
            self.assertNotIn("enum", node)
            old_node["enum"] = [*sorted(DOMAINS[name]), None]
        raw = json.dumps(rebuilt_old, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        self.assertEqual(hashlib.sha256(raw.encode()).hexdigest(), OLD_SCHEMA_SHA256)
        new_tail = ("The trajectory for from_to must have verbatim evidence from the original sentence; the trajectory evidence for none must be null."
                    "single_target is an unordered target derived from a clear musical goal, whose trajectory evidence can be null;"
                    "If filled in, it must still be a verbatim fragment of the original sentence. Other non-empty intent fields and each constraint must have verbatim evidence from the original sentence."
                    "Do not output extra fields, explanations, or songs.")
        old_tail = ("All nonempty intent fields and each constraint's evidence must be a verbatim contiguous span of the original sentence."
                    "Do not output extra fields, explanations, or songs.")
        self.assertTrue(SYSTEM_PROMPT.endswith(new_tail))
        old_prompt = SYSTEM_PROMPT[:-len(new_tail)] + old_tail
        self.assertEqual(hashlib.sha256(old_prompt.encode()).hexdigest(), OLD_PROMPT_SHA256)
        # Range-object enums, trajectory, nested evidence and constraints are untouched.
        self.assertEqual(new["properties"]["target_arousal"]["anyOf"][1]
                         ["properties"]["value"]["enum"], [1, 2, 3])

    def test_runtime_request_uses_full_prompt_and_original_settings(self):
        request = build_request(SENTENCE, MODEL)
        self.assertEqual(request["messages"], [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": SENTENCE},
        ])
        self.assertEqual(request["response_format"]["json_schema"]["schema"], response_schema())
        self.assertIs(request["response_format"]["json_schema"]["strict"], True)
        self.assertEqual(request["provider"], {"require_parameters": True})
        self.assertEqual(request["reasoning"], {"effort": "minimal"})
        self.assertEqual(request["max_tokens"], 2048)
        self.assertNotIn("temperature", request)

    def test_local_numeric_type_and_range_are_still_rejected(self):
        self.assertEqual(validate_intent(copy.deepcopy(VALID), SENTENCE), VALID)
        for field in NUMERIC_FIELDS:
            invalid = copy.deepcopy(VALID)
            invalid[field] = "1"
            with self.subTest(field=field, category="type"):
                with self.assertRaises(InvalidIntent) as raised:
                    validate_intent(invalid, SENTENCE)
                self.assertEqual((raised.exception.category, raised.exception.field),
                                 ("invalid_numeric_type", field))
            invalid[field] = 99
            with self.subTest(field=field, category="range"):
                with self.assertRaises(InvalidIntent) as raised:
                    validate_intent(invalid, SENTENCE)
                self.assertEqual((raised.exception.category, raised.exception.field),
                                 ("numeric_out_of_range", field))
        invalid = copy.deepcopy(VALID)
        invalid["target_arousal"] = {"relation": "at_most", "value": 99}
        with self.assertRaises(InvalidIntent) as raised:
            validate_intent(invalid, SENTENCE)
        self.assertEqual((raised.exception.category, raised.exception.field),
                         ("numeric_out_of_range", "target_arousal.value"))

    def test_marker_only_after_complete_values_and_literal_evidence_pass(self):
        fake_key = "sk-offline-fixture-never-print"
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "connection_preflight.json"
            cases = []
            missing = copy.deepcopy(VALID)
            del missing["constraints"]
            cases.append((missing, "missing_field"))
            out_of_range = copy.deepcopy(VALID)
            out_of_range["target_arousal"] = 99
            cases.append((out_of_range, "numeric_out_of_range"))
            bad_evidence = copy.deepcopy(VALID)
            bad_evidence["evidence"]["target_arousal"] = "Fragment not in original sentence"
            cases.append((bad_evidence, "evidence_not_in_utterance"))
            for intent, category in cases:
                output = io.StringIO()
                with (patch.object(connection_test, "PREFLIGHT", marker),
                      patch.object(connection_test, "get_settings", return_value=(fake_key, MODEL)),
                      patch.object(client, "urlopen", return_value=io.BytesIO(
                          json.dumps(envelope(intent)).encode("utf-8"))),
                      patch.object(sys, "argv", ["connection_test.py"]),
                      contextlib.redirect_stdout(output)):
                    self.assertEqual(connection_test.main(), 1)
                self.assertFalse(marker.exists())
                self.assertIn("category=" + category, output.getvalue())
                self.assertNotIn(fake_key, output.getvalue())
                self.assertNotIn(SENTENCE, output.getvalue())
            output = io.StringIO()
            with (patch.object(connection_test, "PREFLIGHT", marker),
                  patch.object(connection_test, "get_settings", return_value=(fake_key, MODEL)),
                  patch.object(client, "urlopen", return_value=io.BytesIO(
                      json.dumps(envelope(VALID)).encode("utf-8"))),
                  patch.object(sys, "argv", ["connection_test.py"]),
                  contextlib.redirect_stdout(output)):
                self.assertEqual(connection_test.main(), 0)
            self.assertTrue(marker.exists())
            self.assertIn("preflight_marker=recorded", output.getvalue())
            self.assertNotIn(fake_key, output.getvalue())


if __name__ == "__main__":
    unittest.main()
