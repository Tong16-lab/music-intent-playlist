"""Only labeled fixture songs; never presented as real catalog outcomes."""

import csv
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from music_intent.evaluation import decode_answer, score_records
from music_intent.recommender import select_tracks


def intent(**overrides):
    result = {"current_valence": None, "current_arousal": None,
              "target_valence": None, "target_arousal": None,
              "target_melodic_surprise": None, "requires_melody_present": None,
              "trajectory": "none", "evidence": {}, "constraints": []}
    result.update(overrides)
    return result


def fixture(track_id, arousal, valence=0, melody="yes", artist=None):
    return {"track_id": track_id, "artist": artist or track_id,
            "link_identity_status": "matched", "label_status": "verified",
            "arousal": arousal, "valence": valence, "melodic_surprise": 2,
            "melody_present": melody, "fixture_only": True}


class SelectionTests(unittest.TestCase):
    def test_exact_three_step_arousal_path(self):
        tracks = [fixture("high", 3), fixture("mid", 2), fixture("low", 1)]
        request = intent(target_arousal=1,
                         trajectory={"type": "from_to", "arousal": {"from": 3, "to": 1}})
        self.assertEqual([r["track_id"] for r in select_tracks(request, tracks)["tracks"]],
                         ["high", "mid", "low"])
        tracks[1]["arousal"] = "unknown"
        self.assertEqual(select_tracks(request, tracks)["status"], "insufficient_catalog")

    def test_range_melody_and_unknown_cannot_satisfy_hard_requirements(self):
        tracks = [fixture("negative", 1, valence=-1), fixture("zero", 2, valence=0),
                  fixture("positive", 1, valence=1), fixture("unknown", 1, valence="unknown"),
                  fixture("no_melody", 1, valence=0, melody="no")]
        request = intent(target_valence={"relation": "at_least", "value": 0},
                         target_arousal={"relation": "at_most", "value": 2},
                         requires_melody_present=True, trajectory="single_target")
        outcome = select_tracks(request, tracks)
        self.assertEqual(outcome["status"], "insufficient_catalog")
        self.assertEqual({r["track_id"] for r in outcome["tracks"]}, {"zero", "positive"})
        tracks.append(fixture("third", 2, valence=0))
        self.assertEqual({r["track_id"] for r in select_tracks(request, tracks)["tracks"]},
                         {"zero", "positive", "third"})

    def test_unsupported_and_unverified(self):
        tracks = [fixture("a", 1), fixture("b", 2), fixture("c", 3)]
        request = intent(constraints=[{"evidence": "English song", "classification": "unsupported_constraint",
                                       "polarity": "exclude"}])
        self.assertEqual(select_tracks(request, tracks)["status"], "cannot_guarantee_constraint")
        tracks[0]["label_status"] = "unknown"
        tracks[1]["link_identity_status"] = "not_checked"
        self.assertEqual(select_tracks(intent(), tracks)["status"], "insufficient_catalog")


class EvaluationTests(unittest.TestCase):
    def test_formal_run_requires_freeze_before_settings_or_api(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        import evaluate
        with (patch.object(evaluate, "verify_manifest", side_effect=ValueError("freeze_required")),
              patch.object(evaluate, "get_settings", side_effect=AssertionError("settings read")),
              patch.object(evaluate.candidate_runner, "call_candidate_once",
                           side_effect=AssertionError("API called"))):
            with self.assertRaisesRegex(ValueError, "freeze_required"):
                evaluate.run()

    def test_metrics_are_fixed_and_include_failed_calls(self):
        with (ROOT / "data" / "synthetic_intents_test.csv").open(encoding="utf-8", newline="") as handle:
            answers = list(csv.DictReader(handle))[:2]
        with (ROOT / "data" / "unsupported_conditions_test.csv").open(encoding="utf-8", newline="") as handle:
            unsupported = list(csv.DictReader(handle))[:2]
        truth = decode_answer(answers[0])
        truth["constraints"] = []
        records = [{"case_id": answers[0]["case_id"], "utterance": answers[0]["utterance"], "intent": truth},
                   {"case_id": answers[1]["case_id"], "utterance": answers[1]["utterance"],
                    "intent": None, "error_category": "missing_content"}]
        scores = score_records(records, answers, unsupported)
        self.assertEqual((scores["attempted_calls"], scores["valid_responses"], scores["failed_calls"]), (2, 1, 1))
        self.assertEqual((scores["end_to_end"]["denominator"], scores["valid_only"]["denominator"]), (2, 1))
        self.assertEqual(scores["end_to_end"]["core_cards"], 1)
        self.assertEqual(scores["valid_only"]["requires_melody_present"], 1)
        self.assertEqual(scores["end_to_end"]["unsupported_exact_sets"], 1)
        self.assertEqual(scores["end_to_end"]["cannot_guarantee_constraint_status"], 1)
        self.assertEqual(scores["failures"][0]["reason"], "missing_content")

    def test_test_003_failed_call_unfulfills_three_conditions_without_model_false_negatives(self):
        with (ROOT / "data" / "synthetic_intents_test.csv").open(encoding="utf-8", newline="") as handle:
            answer = next(row for row in csv.DictReader(handle) if row["case_id"] == "test_003")
        with (ROOT / "data" / "unsupported_conditions_test.csv").open(encoding="utf-8", newline="") as handle:
            conditions = next(row for row in csv.DictReader(handle) if row["case_id"] == "test_003")
        self.assertEqual(len(json.loads(conditions["unsupported_condition_phrases"])), 3)
        record = {"case_id": "test_003", "utterance": answer["utterance"],
                  "intent": None, "error_category": "output_token_limit"}
        scores = score_records([record], [answer], [conditions])
        self.assertEqual(scores["failed_calls"], 1)
        self.assertEqual(scores["end_to_end"]["denominator"], 1)
        self.assertEqual(scores["end_to_end"]["unsupported_exact_sets"], 0)
        self.assertEqual(scores["end_to_end"]["cannot_guarantee_constraint_status"], 0)
        self.assertEqual(scores["end_to_end"]["unsupported_expected_phrases"], 3)
        self.assertEqual(scores["end_to_end"]["unsupported_unfulfilled_phrases"], 3)
        self.assertEqual(scores["end_to_end"]["unsupported_unfulfilled_due_to_call_failure"], 3)
        self.assertEqual(scores["valid_only"]["denominator"], 0)
        self.assertIsNone(scores["valid_only"]["unsupported_missed_phrases"])
        self.assertEqual(scores["failures"][0]["failure_type"], "no_valid_response")
        sys.path.insert(0, str(ROOT / "scripts"))
        from evaluate_legacy_full_schema import render_report
        report = render_report({"scores": scores, "model": "fixture-model",
                                "started_at": "fixture-time", "tokens": {
                                    "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                                "estimated_cost_usd": 0, "usage_unavailable_calls": 1})
        self.assertIn("Failed call 1", report)
        self.assertIn("3 incomplete; 3 of which are from call failures", report)
        self.assertIn("Model original word recognition metric not evaluated", report)
        valid_but_missing = {"case_id": "test_003", "utterance": answer["utterance"],
                             "intent": {**decode_answer(answer), "constraints": []}}
        model_miss = score_records([valid_but_missing], [answer], [conditions])
        self.assertEqual(model_miss["failed_calls"], 0)
        self.assertEqual(model_miss["valid_only"]["unsupported_missed_phrases"], 3)
        self.assertEqual(model_miss["end_to_end"]["unsupported_unfulfilled_due_to_call_failure"], 0)


if __name__ == "__main__":
    unittest.main()
