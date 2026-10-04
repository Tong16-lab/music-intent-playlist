"""Scoring fixtures only; no formal test answers or model predictions are read."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from music_intent.evaluation import decode_answer, keyword_baseline  # noqa: E402
from music_intent.intent import CORE_FIELDS  # noqa: E402
from music_intent.scoring_v3 import SCORE_VERSION, explicit_gold, score_detailed  # noqa: E402


def answer(case_id: str, utterance: str, **values) -> dict[str, str]:
    row = {"case_id": case_id, "utterance": utterance,
           "current_valence": "", "current_arousal": "", "target_valence": "",
           "target_arousal": "", "target_melodic_surprise": "",
           "trajectory": "none", "requires_melody_present": ""}
    for key, value in values.items():
        row[key] = (json.dumps(value, ensure_ascii=False, separators=(",", ":"))
                    if isinstance(value, dict) else str(value))
    return row


def unsupported(row: dict[str, str], phrases: list[str] | None = None) -> dict[str, str]:
    words = phrases or []
    return {"case_id": row["case_id"], "utterance": row["utterance"],
            "unsupported_condition_phrases": json.dumps(words, ensure_ascii=False),
            "expected_cannot_guarantee_constraint": "true" if words else "false"}


def intent(row: dict[str, str], **changes):
    result = decode_answer(row)
    result.update({"evidence": {}, "constraints": []})
    result.update(changes)
    return result


def record(row: dict[str, str], prediction: dict | None, **stages):
    default = {"api_success": True, "json_complete": True,
               "required_structure_complete": True, "conversion_complete": True}
    default.update(stages)
    return {"case_id": row["case_id"], "utterance": row["utterance"],
            "intent": prediction, **default}


class ScoringV3Tests(unittest.TestCase):
    def test_explicit_nullable_range_and_unspoken_false_fill(self):
        first = answer("dev_001", "I want to hear some songs that aren't too sad", target_valence={"relation": "at_least", "value": 0},
                       trajectory="single_target")
        second = answer("dev_002", "Play some music, whatever.")
        records = [record(first, intent(first, target_valence=0)),
                   record(second, intent(second, target_valence=1))]
        scores = score_detailed(records, [first, second], [unsupported(first), unsupported(second)])
        field = scores["fields"]["target_valence"]
        self.assertEqual(scores["score_version"], SCORE_VERSION)
        self.assertEqual((field["explicit"]["gold_cases"], field["explicit"]["valid_cases"],
                          field["explicit"]["ai_valid_correct"]), (1, 1, 0))
        self.assertEqual((field["unspoken"]["gold_cases"], field["unspoken"]["valid_cases"],
                          field["unspoken"]["ai_false_fills"]), (1, 1, 1))
        self.assertEqual(field["end_to_end"], {"correct": 0, "denominator": 2})
        self.assertEqual(field["valid_only"], {"correct": 0, "denominator": 2})

    def test_only_from_to_is_explicit_order(self):
        path = {"type": "from_to", "arousal": {"from": 3, "to": 1}}
        first = answer("dev_001", "the song is passionate then quiet", target_arousal=1, trajectory=path)
        second = answer("dev_002", "I want to hear quiet songs", target_arousal=1, trajectory="single_target")
        third = answer("dev_003", "Play some music")
        rows = [first, second, third]
        records = [record(first, intent(first)),
                   record(second, intent(second, trajectory="none")),
                   record(third, intent(third, target_arousal=1, trajectory=path))]
        scores = score_detailed(records, rows, [unsupported(x) for x in rows])
        trajectory = scores["fields"]["trajectory"]
        self.assertTrue(explicit_gold("trajectory", path))
        self.assertFalse(explicit_gold("trajectory", "single_target"))
        self.assertFalse(explicit_gold("trajectory", "none"))
        self.assertEqual((trajectory["explicit"]["gold_cases"], trajectory["explicit"]["ai_valid_correct"]), (1, 1))
        self.assertEqual((trajectory["unspoken"]["gold_cases"], trajectory["unspoken"]["ai_valid_exact"]), (2, 0))
        self.assertEqual(trajectory["unspoken"]["ai_false_fills"], 1)
        self.assertEqual(trajectory["unspoken"]["ai_no_order_classification_errors"], 1)

    def test_failures_are_end_to_end_incomplete_even_when_gold_is_null_or_has_constraints(self):
        first = answer("dev_001", "no vocal English rock")
        second = answer("dev_002", "Play some music, whatever.")
        records = [record(first, None, api_success=False, json_complete=False,
                          required_structure_complete=False, conversion_complete=False),
                   record(second, None, api_success=True, json_complete=True,
                          required_structure_complete=False, conversion_complete=False)]
        scores = score_detailed(records, [first, second],
                                [unsupported(first, ["no vocals", "English", "rock"]), unsupported(second)])
        self.assertEqual((scores["total_cases"], scores["valid_responses"], scores["failed_calls"]), (2, 0, 2))
        self.assertEqual(scores["stages"], {"api_success": 1, "json_complete": 1,
                                            "required_structure_complete": 0,
                                            "conversion_complete": 0, "local_valid": 0})
        self.assertEqual(scores["fields"]["target_valence"]["end_to_end"],
                         {"correct": 0, "denominator": 2})
        self.assertEqual(scores["fields"]["target_valence"]["unspoken"]["ai_false_fills"], 0)
        self.assertEqual(scores["fields"]["target_valence"]["unspoken"]["invalid_or_missing_cases"], 2)
        self.assertEqual(scores["unsupported"]["status_end_to_end_correct"], 0)
        self.assertEqual(scores["unsupported"]["exact_set_end_to_end_correct"], 0)
        self.assertEqual(scores["unsupported"]["unfulfilled_phrases_due_to_invalid"], 3)
        self.assertEqual(scores["unsupported"]["valid_missed_phrases"], None)
        self.assertEqual(scores["core_cards"]["end_to_end_correct"], 0)

    def test_valid_constraints_status_and_exact_words_are_distinct(self):
        row = answer("dev_001", "No English or rock music")
        conditions = unsupported(row, ["English", "rock"])
        prediction = intent(row, constraints=[{"evidence": "English", "classification": "unsupported_constraint",
                                               "polarity": "exclude"}])
        scores = score_detailed([record(row, prediction)], [row], [conditions])
        self.assertEqual(scores["unsupported"]["status_end_to_end_correct"], 1)
        self.assertEqual(scores["unsupported"]["exact_set_end_to_end_correct"], 0)
        self.assertEqual(scores["unsupported"]["valid_true_positive_phrases"], 1)
        self.assertEqual(scores["unsupported"]["valid_missed_phrases"], 1)
        self.assertEqual(scores["core_cards"]["end_to_end_correct"], 1)

    def test_baseline_uses_same_sentences_and_gold_without_structure_metrics(self):
        rows = [answer("dev_001", "I'm annoyed right now, I want to listen to quiet songs", current_valence=-1,
                       target_arousal=1, trajectory="single_target"),
                answer("dev_002", "Play some random music")]
        scores = score_detailed([record(row, intent(row)) for row in rows], rows,
                                [unsupported(row) for row in rows])
        for field in CORE_FIELDS:
            expected = sum(keyword_baseline(row["utterance"])[field] == decode_answer(row)[field]
                           for row in rows)
            self.assertEqual(scores["fields"][field]["baseline"],
                             {"correct": expected, "denominator": 2})
        self.assertEqual(scores["stages"]["api_success"], 2)
        self.assertNotIn("baseline_api_success", scores["stages"])
        self.assertEqual(scores["core_cards"]["baseline_correct"],
                         sum(all(keyword_baseline(row["utterance"])[field] == decode_answer(row)[field]
                                 for field in CORE_FIELDS) for row in rows))

    def test_rejects_misalignment_and_fabricated_valid_stage(self):
        row = answer("dev_001", "Play some random music")
        with self.assertRaisesRegex(ValueError, "scoring_case_alignment"):
            score_detailed([], [row], [unsupported(row)])
        with self.assertRaisesRegex(ValueError, "valid_intent_without_complete_stages"):
            score_detailed([record(row, intent(row), conversion_complete=False)],
                           [row], [unsupported(row)])

    def test_rejects_unrecognized_approved_constraint_status(self):
        row = answer("dev_001", "Play some random music")
        condition = unsupported(row)
        condition["expected_cannot_guarantee_constraint"] = ""
        with self.assertRaisesRegex(ValueError, "scoring_unsupported_status_invalid"):
            score_detailed([record(row, intent(row))], [row], [condition])


if __name__ == "__main__":
    unittest.main()
