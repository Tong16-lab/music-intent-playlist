"""Fixed metrics and a simple keyword baseline for synthetic intent evaluation."""

from __future__ import annotations

import json
from typing import Any

from .intent import CORE_FIELDS, route_status


def decode_answer(row: dict[str, str]) -> dict[str, Any]:
    answer = {}
    for field in (*CORE_FIELDS, "requires_melody_present"):
        text = row[field]
        if not text:
            answer[field] = None
        elif field == "requires_melody_present":
            answer[field] = True if text == "true" else text
        elif field == "trajectory":
            answer[field] = json.loads(text) if text.startswith("{") else text
        else:
            answer[field] = json.loads(text) if text.startswith("{") else int(text)
    return answer


def keyword_baseline(utterance: str) -> dict[str, Any]:
    """Predeclared generic lexicon; never reads test answers or song titles."""
    text = utterance
    current_valence = None
    if any(term in text for term in ("annoyed", "upset", "down", "anxious", "panicked", "lonely")):
        current_valence = -1
    elif any(term in text for term in ("happy", "glad", "in a good mood")):
        current_valence = 1
    current_arousal = 1 if any(term in text for term in ("I am sleepy now", "so sleepy", "drowsy")) else None
    target_valence = None
    if any(term in text for term in ("want to hear sad", "want to hear sorrowful", "want to hear melancholy")):
        target_valence = -1
    elif any(term in text for term in ("cheerful", "happy song", "sunny song")):
        target_valence = 1
    elif any(term in text for term in ("neither sad nor happy", "calm song")):
        target_valence = 0
    target_arousal = None
    if any(term in text for term in ("quiet", "calm", "soothing")):
        target_arousal = 1
    elif any(term in text for term in ("refreshing", "energetic", "strong kick", "intense")):
        target_arousal = 3
    target_melodic_surprise = None
    if any(term in text for term in ("don't be too complex", "not too fancy", "not too convoluted")):
        target_melodic_surprise = 1
    elif any(term in text for term in ("surprise", "unexpected", "did not expect")):
        target_melodic_surprise = 3
    has_target = any(value is not None for value in (target_valence, target_arousal))
    return {"current_valence": current_valence, "current_arousal": current_arousal,
            "target_valence": target_valence, "target_arousal": target_arousal,
            "target_melodic_surprise": target_melodic_surprise,
            "trajectory": "single_target" if has_target else "none"}


def score_records(records: list[dict[str, Any]], answers: list[dict[str, str]],
                  unsupported: list[dict[str, str]]) -> dict[str, Any]:
    expected = {row["case_id"]: decode_answer(row) for row in answers}
    unsupported_by_id = {row["case_id"]: row for row in unsupported}
    if (len(expected) != len(answers) or len(unsupported_by_id) != len(unsupported)
            or set(expected) != set(unsupported_by_id)
            or len(records) != len(answers)
            or {record["case_id"] for record in records} != set(expected)):
        raise ValueError("evaluation_case_alignment")
    count = len(records)
    fields = {field: 0 for field in CORE_FIELDS}
    baseline_fields = {field: 0 for field in CORE_FIELDS}
    cards = baseline_cards = melody = condition_sets = routes = tp = fp = fn = 0
    failed_calls = failed_expected_phrases = 0
    expected_phrase_total = 0
    valid_expected_phrase_total = 0
    failures = []
    for record in records:
        case_id = record["case_id"]
        truth = expected[case_id]
        prediction = record.get("intent")
        expected_phrases = set(json.loads(unsupported_by_id[case_id]["unsupported_condition_phrases"]))
        expected_phrase_total += len(expected_phrases)
        baseline = keyword_baseline(record["utterance"])
        baseline_correct = [field for field in CORE_FIELDS if baseline[field] == truth[field]]
        for field in baseline_correct:
            baseline_fields[field] += 1
        baseline_cards += len(baseline_correct) == len(CORE_FIELDS)
        if prediction is None:
            failed_calls += 1
            failed_expected_phrases += len(expected_phrases)
            failures.append({"case_id": case_id, "reason": record.get("error_category", "no_valid_intent"),
                             "failure_type": "no_valid_response",
                             "expected_unsupported_phrases_unfulfilled": sorted(expected_phrases)})
            continue
        valid_expected_phrase_total += len(expected_phrases)
        correct = [field for field in CORE_FIELDS if prediction[field] == truth[field]]
        for field in correct:
            fields[field] += 1
        cards += len(correct) == len(CORE_FIELDS)
        melody += prediction["requires_melody_present"] == truth["requires_melody_present"]
        found = {item["evidence"] for item in prediction["constraints"]}
        condition_sets += found == expected_phrases
        tp += len(found & expected_phrases)
        fp += len(found - expected_phrases)
        fn += len(expected_phrases - found)
        route_expected = unsupported_by_id[case_id]["expected_cannot_guarantee_constraint"] == "true"
        routes += (route_status(prediction) == "cannot_guarantee_constraint") == route_expected
        if len(correct) != len(CORE_FIELDS) or prediction["requires_melody_present"] != truth["requires_melody_present"] or found != expected_phrases or (
            (route_status(prediction) == "cannot_guarantee_constraint") != route_expected
        ):
            failures.append({"case_id": case_id, "failure_type": "valid_response_mismatch",
                             "wrong_core_fields": [field for field in CORE_FIELDS if field not in correct],
                             "requires_melody_present_wrong": prediction["requires_melody_present"] != truth["requires_melody_present"],
                             "unsupported_missing": sorted(expected_phrases - found),
                             "unsupported_extra": sorted(found - expected_phrases)})
    valid_count = count - failed_calls
    common = {"core_fields": fields, "core_cards": cards,
              "requires_melody_present": melody, "unsupported_exact_sets": condition_sets,
              "cannot_guarantee_constraint_status": routes}
    return {
        "attempted_calls": count, "valid_responses": valid_count, "failed_calls": failed_calls,
        "end_to_end": {"denominator": count, **common,
                       "unsupported_expected_phrases": expected_phrase_total,
                       "unsupported_unfulfilled_phrases": fn + failed_expected_phrases,
                       "unsupported_unfulfilled_due_to_call_failure": failed_expected_phrases},
        "valid_only": {"denominator": valid_count, **common,
                       "unsupported_expected_phrases": valid_expected_phrase_total,
                       "unsupported_true_positive_phrases": tp if valid_count else None,
                       "unsupported_false_positive_phrases": fp if valid_count else None,
                       "unsupported_missed_phrases": fn if valid_count else None},
        "keyword_baseline": {"denominator": count, "core_fields": baseline_fields,
                             "core_cards": baseline_cards},
        "failures": failures,
    }
