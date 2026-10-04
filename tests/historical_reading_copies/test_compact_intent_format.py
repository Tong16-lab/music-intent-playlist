"""Offline representability and rejection tests; no inference API is called."""

from __future__ import annotations

import copy
import csv
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "prototypes"))
sys.path.insert(0, str(ROOT / "src"))

from compact_intent_format import candidate_schema, convert_candidate  # noqa: E402
from music_intent.intent import EVIDENCE_FIELDS, InvalidIntent, response_schema, route_status  # noqa: E402

SENTENCE = "I am annoyed now and want quieter music with a clear melody, without English-language songs."
BASE = {
    "current_valence": -1, "current_arousal": None,
    "target_valence": None, "target_arousal": "=1",
    "target_melodic_surprise": None, "trajectory": "single_target",
    "requires_melody_present": True,
    "evidence": {
        "current_valence": "annoyed", "current_arousal": None,
        "target_valence": None, "target_arousal": "quieter",
        "target_melodic_surprise": None, "trajectory": None,
        "requires_melody_present": "clear melody",
    },
    "constraints": [{"evidence": "without English-language songs", "classification": "unsupported_constraint",
                     "polarity": "exclude"}],
}


def _source_card(row: dict[str, str], polarity: str) -> tuple[dict, dict]:
    """Test-only encoding of approved values; polarity is not approved in V2."""
    evidence_source = json.loads(row["evidence_json"])
    original: dict = {}
    candidate: dict = {}
    for field in ("current_valence", "current_arousal", "target_melodic_surprise"):
        original[field] = int(row[field]) if row[field] else None
        candidate[field] = original[field]
    for field in ("target_valence", "target_arousal"):
        raw = row[field]
        original[field] = json.loads(raw) if raw.startswith("{") else (int(raw) if raw else None)
        if isinstance(original[field], dict):
            operator = ">=" if original[field]["relation"] == "at_least" else "<="
            candidate[field] = f"{operator}{original[field]['value']}"
        else:
            candidate[field] = f"={original[field]}" if original[field] is not None else None
    original["requires_melody_present"] = True if row["requires_melody_present"] == "true" else None
    candidate["requires_melody_present"] = original["requires_melody_present"]
    raw_path = row["trajectory"]
    original["trajectory"] = json.loads(raw_path) if raw_path.startswith("{") else raw_path
    if isinstance(original["trajectory"], dict):
        sections = []
        for dimension in ("valence", "arousal"):
            if dimension in original["trajectory"]:
                path = original["trajectory"][dimension]
                sections.append(f"{dimension}:{path['from']}->{path['to']}")
        candidate["trajectory"] = ";".join(sections)
    else:
        candidate["trajectory"] = original["trajectory"]
    evidence = {field: evidence_source.get(field) or None for field in EVIDENCE_FIELDS}
    original["evidence"] = copy.deepcopy(evidence)
    candidate["evidence"] = copy.deepcopy(evidence)
    # V2 approves phrase text, but has no per-phrase polarity. Both legal
    # transport variants are checked without claiming either is ground truth.
    phrases = json.loads(row["unsupported_condition_phrases"])
    constraints = [{"evidence": phrase, "classification": "unsupported_constraint",
                    "polarity": polarity} for phrase in phrases]
    original["constraints"] = copy.deepcopy(constraints)
    candidate["constraints"] = copy.deepcopy(constraints)
    return original, candidate


class CompactFormatTests(unittest.TestCase):
    def test_only_three_schema_properties_change(self):
        formal = response_schema()
        candidate = candidate_schema()
        self.assertEqual(candidate["required"], formal["required"])
        self.assertEqual(set(candidate["properties"]), set(formal["properties"]))
        self.assertEqual(candidate["additionalProperties"], formal["additionalProperties"])
        changed = {"target_valence", "target_arousal", "trajectory"}
        for field in set(formal["properties"]) - changed:
            self.assertEqual(candidate["properties"][field], formal["properties"][field])
        for field in changed:
            self.assertNotEqual(candidate["properties"][field], formal["properties"][field])
            self.assertNotIn("anyOf", candidate["properties"][field])

    def test_all_approved_cards_are_losslessly_representable(self):
        with (ROOT / "data" / "user_intents_v2_review.tsv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle, delimiter="\t"))
        self.assertEqual(len(rows), 42)
        self.assertEqual({row["case_id"] for row in rows},
                         {f"dev_{n:03d}" for n in range(1, 13)} |
                         {f"test_{n:03d}" for n in range(1, 31)})
        self.assertEqual(sum(row["split"] == "dev" for row in rows), 12)
        self.assertEqual(sum(row["split"] == "test" for row in rows), 30)
        for row in rows:
            self.assertEqual(row["review_status"], "approved")
            for fixture_polarity in ("include", "exclude"):
                with self.subTest(case_id=row["case_id"], fixture_polarity=fixture_polarity):
                    expected, wire = _source_card(row, fixture_polarity)
                    actual = convert_candidate(wire, row["utterance"])
                    self.assertEqual(actual, expected)
                    self.assertEqual(route_status(actual),
                                     "cannot_guarantee_constraint" if expected["constraints"] else "ready")

    def test_exact_range_and_path_are_distinct(self):
        sentence = "I want to listen to some quiet music that isn't too sorrowful."
        wire = copy.deepcopy(BASE)
        wire.update({"current_valence": None, "target_valence": ">=0", "target_arousal": "<=2",
                     "requires_melody_present": None, "constraints": []})
        wire["evidence"] = {field: None for field in EVIDENCE_FIELDS}
        wire["evidence"].update({"target_valence": "Don't be too melodramatic", "target_arousal": "A bit quieter"})
        converted = convert_candidate(wire, sentence)
        self.assertEqual(converted["target_valence"], {"relation": "at_least", "value": 0})
        self.assertEqual(converted["target_arousal"], {"relation": "at_most", "value": 2})
        wire["target_valence"] = "=0"
        self.assertEqual(convert_candidate(wire, sentence)["target_valence"], 0)

        sentence = "First listen to enthusiastic music, and then gradually calm down."
        wire = copy.deepcopy(BASE)
        wire.update({"current_valence": None, "target_arousal": "=1", "trajectory": "arousal:3->1",
                     "requires_melody_present": None, "constraints": []})
        wire["evidence"] = {field: None for field in EVIDENCE_FIELDS}
        wire["evidence"].update({"target_arousal": "calm down", "trajectory": "listen to lively music first, then gradually calm down"})
        self.assertEqual(convert_candidate(wire, sentence)["trajectory"],
                         {"type": "from_to", "arousal": {"from": 3, "to": 1}})

        sentence = "First listen to sad and passionate music, then become calm and cheerful."
        wire.update({"target_valence": "=1", "trajectory": "valence:-1->1;arousal:3->1"})
        wire["evidence"].update({"target_valence": "cheerful", "target_arousal": "calm",
                                 "trajectory": "first listen to sad and passionate music, then become calm and cheerful"})
        self.assertEqual(convert_candidate(wire, sentence)["trajectory"],
                         {"type": "from_to", "valence": {"from": -1, "to": 1},
                          "arousal": {"from": 3, "to": 1}})

    def test_rejects_missing_extra_malformed_and_out_of_range(self):
        cases = [
            (lambda x: x.pop("target_arousal"), "missing_field"),
            (lambda x: x.update({"new_field": 1}), "extra_field"),
            (lambda x: x.update({"target_arousal": 1}), "invalid_field_value"),
            (lambda x: x.update({"target_arousal": "<=9"}), "numeric_out_of_range"),
            (lambda x: x.update({"target_arousal": "<=2 "}), "invalid_field_value"),
            (lambda x: x.update({"target_arousal": "=01"}), "invalid_field_value"),
            (lambda x: x.update({"target_arousal": "3->1"}), "invalid_field_value"),
            (lambda x: x.update({"trajectory": "arousal:3->3"}), "invalid_field_value"),
            (lambda x: x.update({"trajectory": "arousal:3->9"}), "numeric_out_of_range"),
            (lambda x: x.update({"trajectory": "arousal:3->1;arousal:2->1"}), "invalid_field_value"),
            (lambda x: x.update({"trajectory": "arousal:3->1;valence:-1->1"}), "invalid_field_value"),
            (lambda x: x.update({"requires_melody_present": False}), "invalid_field_value"),
            (lambda x: x["evidence"].pop("target_arousal"), "missing_field"),
            (lambda x: x["evidence"].update({"target_arousal": None}), "missing_evidence"),
            (lambda x: x["evidence"].update({"target_arousal": "not in original"}), "evidence_not_in_utterance"),
            (lambda x: x.update({"constraints": [{"evidence": "No English songs"}]}), "invalid_constraint_format"),
            (lambda x: x["constraints"][0].update({"evidence": "not in original"}), "evidence_not_in_utterance"),
        ]
        for mutate, category in cases:
            wire = copy.deepcopy(BASE)
            mutate(wire)
            with self.subTest(category=category), self.assertRaises(InvalidIntent) as raised:
                convert_candidate(wire, SENTENCE)
            self.assertEqual(raised.exception.category, category)

    def test_trajectory_evidence_and_conflicting_endpoint(self):
        wire = copy.deepcopy(BASE)
        wire["trajectory"] = "arousal:3->1"
        with self.assertRaises(InvalidIntent) as raised:
            convert_candidate(wire, SENTENCE)
        self.assertEqual(raised.exception.category, "missing_evidence")
        wire["evidence"]["trajectory"] = "want to listen to something quieter"
        self.assertEqual(convert_candidate(wire, SENTENCE)["trajectory"]["arousal"]["to"], 1)
        wire["target_arousal"] = "=2"
        with self.assertRaises(InvalidIntent) as raised:
            convert_candidate(wire, SENTENCE)
        self.assertEqual(raised.exception.field, "trajectory.arousal")
        wire["trajectory"] = "none"
        with self.assertRaises(InvalidIntent) as raised:
            convert_candidate(wire, SENTENCE)
        self.assertEqual(raised.exception.category, "unexpected_evidence")


if __name__ == "__main__":
    unittest.main()
