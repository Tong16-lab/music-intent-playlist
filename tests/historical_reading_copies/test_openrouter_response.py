"""Offline response fixtures; no credentials or network calls."""

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from music_intent.openrouter_client import (  # noqa: E402
    OpenRouterFailure, parse_response, required_structure_complete,
)
from music_intent.intent import response_schema  # noqa: E402


UTTERANCE = "I am a bit anxious right now, and want to listen to a calmer song."
MODEL = "google/gemini-3.5-flash-lite"
VALID = {
    "current_valence": -1,
    "current_arousal": None,
    "target_valence": None,
    "target_arousal": 1,
    "target_melodic_surprise": None,
    "trajectory": {"type": "from_to", "arousal": {"from": 3, "to": 1}},
    "requires_melody_present": None,
    "evidence": {
        "current_valence": "anxious",
        "current_arousal": None,
        "target_valence": None,
        "target_arousal": "calmer",
        "target_melodic_surprise": None,
        "trajectory": "I am a bit anxious right now, and want to listen to a calmer song",
        "requires_melody_present": None,
    },
    "constraints": [],
}


def envelope(intent=VALID):
    return {
        "model": MODEL,
        "choices": [{"finish_reason": "stop", "message": {"content": json.dumps(intent)}}],
        "usage": {"prompt_tokens": 100, "completion_tokens": 40, "total_tokens": 140},
    }


class ResponseTests(unittest.TestCase):
    def assert_failure(self, payload, category, field=None):
        with self.assertRaises(OpenRouterFailure) as context:
            parse_response(payload, UTTERANCE, MODEL)
        error = context.exception
        self.assertEqual(error.category, category)
        self.assertEqual(error.field, field)
        self.assertNotIn(UTTERANCE, str(error))
        return error

    def test_valid_response(self):
        intent, info = parse_response(envelope(), UTTERANCE, MODEL)
        self.assertEqual(intent, VALID)
        self.assertEqual(info["usage"]["total_tokens"], 140)
        self.assertEqual(info["finish_reason"], "stop")
        self.assertTrue(info["json_complete"])
        self.assertTrue(info["required_structure_complete"])

    def test_structure_and_local_evidence_are_distinct(self):
        item = copy.deepcopy(VALID)
        item["trajectory"] = "single_target"
        item["evidence"]["trajectory"] = None
        _, info = parse_response(envelope(item), UTTERANCE, MODEL)
        self.assertTrue(info["required_structure_complete"])
        item["trajectory"] = {"type": "from_to", "arousal": {"from": 3, "to": 1}}
        error = self.assert_failure(envelope(item), "missing_evidence", "trajectory")
        self.assertTrue(error.json_complete)
        self.assertTrue(error.required_structure_complete)
        self.assertTrue(required_structure_complete(response_schema(), item))
        del item["evidence"]["target_arousal"]
        error = self.assert_failure(envelope(item), "missing_field", "evidence.target_arousal")
        self.assertFalse(error.required_structure_complete)

    def test_safe_reasoning_usage_on_success(self):
        payload = envelope()
        payload["usage"]["completion_tokens_details"] = {"reasoning_tokens": 31}
        _, info = parse_response(payload, UTTERANCE, MODEL)
        self.assertEqual(info["usage"]["reasoning_tokens"], 31)
        payload["usage"]["completion_tokens_details"] = {"reasoning_tokens": "secret-like-text"}
        _, info = parse_response(payload, UTTERANCE, MODEL)
        self.assertNotIn("reasoning_tokens", info["usage"])
        del payload["usage"]["completion_tokens_details"]
        payload["usage"]["reasoning_tokens"] = 17
        _, info = parse_response(payload, UTTERANCE, MODEL)
        self.assertEqual(info["usage"]["reasoning_tokens"], 17)

    def test_missing_content_and_bad_json(self):
        self.assert_failure({"choices": []}, "missing_content")
        payload = envelope()
        del payload["choices"][0]["message"]["content"]
        self.assert_failure(payload, "missing_content")
        payload = envelope()
        payload["choices"][0]["message"]["content"] = "{bad json"
        error = self.assert_failure(payload, "invalid_content_json")
        self.assertEqual(error.usage["total_tokens"], 140)

    def test_missing_extra_and_invalid_fields(self):
        intent = copy.deepcopy(VALID)
        del intent["target_valence"]
        self.assert_failure(envelope(intent), "missing_field", "target_valence")
        intent = copy.deepcopy(VALID)
        intent["invented"] = "untrusted text"
        self.assert_failure(envelope(intent), "extra_field")
        intent = copy.deepcopy(VALID)
        intent["target_arousal"] = 4
        self.assert_failure(envelope(intent), "numeric_out_of_range", "target_arousal")
        intent["target_arousal"] = "4"
        self.assert_failure(envelope(intent), "invalid_numeric_type", "target_arousal")

    def test_empty_json_reports_all_fixed_required_fields_without_model_text(self):
        expected = ",".join(sorted(response_schema()["required"]))
        error = self.assert_failure(envelope({}), "missing_field", expected)
        self.assertEqual(len(error.field.split(",")), 9)
        self.assertEqual(error.finish_reason, "stop")
        intent = {"invented_private_field": "private model value"}
        error = self.assert_failure(envelope(intent), "missing_field", expected)
        self.assertNotIn("invented_private_field", str(error))
        self.assertNotIn("private model value", str(error))

    def test_nested_evidence_reports_every_missing_fixed_field(self):
        intent = copy.deepcopy(VALID)
        intent["evidence"] = {}
        expected = ",".join(f"evidence.{name}" for name in sorted(VALID["evidence"]))
        self.assert_failure(envelope(intent), "missing_field", expected)

    def test_evidence_and_constraint_errors(self):
        intent = copy.deepcopy(VALID)
        intent["evidence"]["target_arousal"] = "Text not in the original sentence"
        self.assert_failure(envelope(intent), "evidence_not_in_utterance", "target_arousal")
        intent = copy.deepcopy(VALID)
        intent["constraints"] = [{"evidence": "rock", "classification": "unsupported_constraint"}]
        self.assert_failure(envelope(intent), "invalid_constraint_format", "constraints[0]")
        intent["constraints"][0]["polarity"] = "include"
        self.assert_failure(envelope(intent), "evidence_not_in_utterance", "constraints[0].evidence")

    def test_token_limit_and_untrusted_usage(self):
        payload = envelope()
        payload["choices"][0]["finish_reason"] = "length"
        payload["usage"]["total_tokens"] = "untrusted"
        payload["usage"]["completion_tokens_details"] = {"reasoning_tokens": 37}
        error = self.assert_failure(payload, "output_token_limit")
        self.assertNotIn("total_tokens", error.usage)
        self.assertEqual(error.usage["reasoning_tokens"], 37)
        self.assertEqual(error.finish_reason, "length")
        self.assertEqual(error.content_shape["content_empty"], False)
        self.assertEqual(error.content_shape["content_chars"], len(json.dumps(VALID)))
        self.assertFalse(error.content_shape["repeated_suffix"])

    def test_token_limit_reports_empty_or_obviously_repeated_content_without_text(self):
        payload = envelope()
        payload["choices"][0]["finish_reason"] = "length"
        payload["choices"][0]["message"]["content"] = ""
        error = self.assert_failure(payload, "output_token_limit")
        self.assertEqual(error.content_shape,
                         {"content_empty": True, "content_chars": 0, "repeated_suffix": False})
        repeated_text = "abcdefghijklmnop" * 4
        payload["choices"][0]["message"]["content"] = repeated_text
        error = self.assert_failure(payload, "output_token_limit")
        self.assertEqual(error.content_shape["content_chars"], len(repeated_text))
        self.assertTrue(error.content_shape["repeated_suffix"])
        self.assertNotIn(repeated_text, str(error))
        del payload["choices"][0]["message"]["content"]
        error = self.assert_failure(payload, "output_token_limit")
        self.assertIsNone(error.content_shape["content_chars"])

    def test_untrusted_finish_reason_is_not_echoed(self):
        payload = envelope()
        payload["choices"][0]["finish_reason"] = "provider private response text"
        error = self.assert_failure(payload, "incomplete_response")
        self.assertEqual(error.finish_reason, "other")
        self.assertNotIn("provider private", str(error))
        payload["choices"][0]["finish_reason"] = []
        error = self.assert_failure(payload, "incomplete_response")
        self.assertEqual(error.finish_reason, "other")


if __name__ == "__main__":
    unittest.main()
