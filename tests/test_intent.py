import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from music_intent.intent import InvalidIntent, response_schema, route_status, validate_intent
from music_intent.openrouter_client import build_request, classify_http_error

UTTERANCE = "我现在烦，想听安静一点、有清楚旋律的音乐，不要英文歌。"
VALID = {
    "current_valence": -1, "current_arousal": None,
    "target_valence": None, "target_arousal": 1,
    "target_melodic_surprise": None, "trajectory": "single_target",
    "requires_melody_present": True,
    "evidence": {
        "current_valence": "烦", "current_arousal": None,
        "target_valence": None, "target_arousal": "安静一点",
        "target_melodic_surprise": None, "trajectory": "想听安静一点、有清楚旋律的音乐",
        "requires_melody_present": "有清楚旋律",
    },
    "constraints": [{"evidence": "不要英文歌", "classification": "unsupported_constraint", "polarity": "exclude"}],
}


class IntentTests(unittest.TestCase):
    def test_valid_and_unsupported_route(self):
        self.assertEqual(validate_intent(copy.deepcopy(VALID), UTTERANCE), VALID)
        self.assertEqual(route_status(VALID), "cannot_guarantee_constraint")

    def test_ranges_and_music_path(self):
        sentence = "先听热烈的音乐，然后逐渐安静下来，别太悲。"
        intent = copy.deepcopy(VALID)
        intent.update({"current_valence": None, "target_valence": {"relation": "at_least", "value": 0},
                       "target_arousal": 1, "trajectory": {"type": "from_to", "arousal": {"from": 3, "to": 1}},
                       "requires_melody_present": None, "constraints": []})
        intent["evidence"] = {"current_valence": None, "current_arousal": None,
                              "target_valence": "别太悲", "target_arousal": "安静下来",
                              "target_melodic_surprise": None,
                              "trajectory": "先听热烈的音乐，然后逐渐安静下来",
                              "requires_melody_present": None}
        self.assertEqual(validate_intent(intent, sentence), intent)
        intent["trajectory"]["arousal"]["to"] = 2
        with self.assertRaises(InvalidIntent):
            validate_intent(intent, sentence)

    def test_bad_evidence_values_and_constraints(self):
        bad = copy.deepcopy(VALID)
        bad["evidence"]["target_arousal"] = "不存在的短语"
        with self.assertRaisesRegex(InvalidIntent, "evidence_not_in_utterance:target_arousal"):
            validate_intent(bad, UTTERANCE)
        bad = copy.deepcopy(VALID)
        bad["requires_melody_present"] = False
        with self.assertRaisesRegex(InvalidIntent, "invalid_field_value:requires_melody_present"):
            validate_intent(bad, UTTERANCE)
        bad = copy.deepcopy(VALID)
        bad["constraints"][0]["polarity"] = []
        with self.assertRaisesRegex(InvalidIntent, "invalid_constraint_format"):
            validate_intent(bad, UTTERANCE)

    def test_trajectory_evidence_policy(self):
        single = copy.deepcopy(VALID)
        single["evidence"]["trajectory"] = None
        self.assertEqual(validate_intent(single, UTTERANCE), single)
        single["evidence"]["trajectory"] = "不是原句"
        with self.assertRaisesRegex(InvalidIntent, "evidence_not_in_utterance:trajectory"):
            validate_intent(single, UTTERANCE)
        single["evidence"]["trajectory"] = ""
        with self.assertRaisesRegex(InvalidIntent, "invalid_evidence_value:trajectory"):
            validate_intent(single, UTTERANCE)
        no_music_target = copy.deepcopy(VALID)
        no_music_target["target_arousal"] = None
        no_music_target["evidence"]["target_arousal"] = None
        no_music_target["evidence"]["trajectory"] = None
        with self.assertRaisesRegex(InvalidIntent, "invalid_field_value:trajectory"):
            validate_intent(no_music_target, UTTERANCE)
        none = copy.deepcopy(VALID)
        none["trajectory"] = "none"
        none["evidence"]["trajectory"] = "想听安静一点"
        with self.assertRaisesRegex(InvalidIntent, "unexpected_evidence:trajectory"):
            validate_intent(none, UTTERANCE)
        none["evidence"]["trajectory"] = None
        self.assertEqual(validate_intent(none, UTTERANCE), none)
        ordered = copy.deepcopy(VALID)
        ordered["trajectory"] = {"type": "from_to", "arousal": {"from": 3, "to": 1}}
        ordered["evidence"]["trajectory"] = None
        with self.assertRaisesRegex(InvalidIntent, "missing_evidence:trajectory"):
            validate_intent(ordered, UTTERANCE)

    def test_request_schema(self):
        payload = build_request(UTTERANCE, "google/gemini-3.5-flash-lite")
        self.assertEqual(payload["response_format"]["type"], "json_schema")
        self.assertIs(payload["response_format"]["json_schema"]["strict"], True)
        self.assertEqual(payload["provider"], {"require_parameters": True})
        self.assertEqual(set(response_schema()["required"]), set(VALID))
        self.assertEqual(payload["max_tokens"], 2048)
        self.assertEqual(payload["reasoning"], {"effort": "minimal"})
        self.assertNotIn("temperature", payload)
        self.assertEqual(payload["model"], "google/gemini-3.5-flash-lite")
        self.assertEqual([message["role"] for message in payload["messages"]], ["system", "user"])
        self.assertEqual(payload["usage"], {"include": True})
        self.assertEqual(classify_http_error(402), "insufficient_credits")


if __name__ == "__main__":
    unittest.main()
