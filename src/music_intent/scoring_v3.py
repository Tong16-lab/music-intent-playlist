"""Predeclared formal-scoring-v3 metrics; no model calls or answer changes."""

from __future__ import annotations

import json
from typing import Any

from .evaluation import decode_answer, keyword_baseline
from .intent import CORE_FIELDS

SCORE_VERSION = "formal-scoring-v3"
NULLABLE_FIELDS = CORE_FIELDS[:5]


def explicit_gold(field: str, value: Any) -> bool:
    """An explicit music *sequence* is only a V2 from_to trajectory."""
    if field == "trajectory":
        if isinstance(value, dict) and value.get("type") == "from_to":
            return True
        if value in ("single_target", "none"):
            return False
        raise ValueError("invalid_gold_trajectory")
    if field not in NULLABLE_FIELDS:
        raise ValueError("unknown_core_field")
    return value is not None


def unspoken_false_fill(field: str, predicted: Any) -> bool:
    if field == "trajectory":
        return isinstance(predicted, dict) and predicted.get("type") == "from_to"
    return predicted is not None


def _field_template(total: int, valid: int) -> dict[str, Any]:
    return {
        "end_to_end": {"correct": 0, "denominator": total},
        "valid_only": {"correct": 0, "denominator": valid},
        "baseline": {"correct": 0, "denominator": total},
        "explicit": {"gold_cases": 0, "valid_cases": 0,
                     "ai_end_to_end_correct": 0, "ai_valid_correct": 0,
                     "baseline_correct": 0},
        "unspoken": {"gold_cases": 0, "valid_cases": 0,
                      "ai_end_to_end_exact": 0, "ai_valid_exact": 0,
                      "ai_false_fills": 0, "ai_no_order_classification_errors": 0,
                      "baseline_exact": 0, "baseline_false_fills": 0,
                      "baseline_no_order_classification_errors": 0},
    }


def score_detailed(records: list[dict[str, Any]], answers: list[dict[str, str]],
                   unsupported: list[dict[str, str]]) -> dict[str, Any]:
    """Score the same approved sentences for AI and the fixed keyword baseline."""
    answer_by_id = {row["case_id"]: row for row in answers}
    unsupported_by_id = {row["case_id"]: row for row in unsupported}
    record_by_id = {row["case_id"]: row for row in records}
    if (not answers or len(answer_by_id) != len(answers)
            or len(unsupported_by_id) != len(unsupported)
            or len(record_by_id) != len(records)
            or set(answer_by_id) != set(unsupported_by_id) or set(answer_by_id) != set(record_by_id)):
        raise ValueError("scoring_case_alignment")
    total = len(answers)
    valid = sum(record.get("intent") is not None for record in records)
    fields = {name: _field_template(total, valid) for name in CORE_FIELDS}
    stage_names = ("api_success", "json_complete", "required_structure_complete",
                   "conversion_complete")
    stages = {name: sum(record.get(name) is True for record in records) for name in stage_names}
    stages["local_valid"] = valid
    ai_cards = baseline_cards = ai_melody = 0
    status = exact_sets = tp = fp = fn = unfulfilled_failed = expected_phrase_total = 0
    case_summaries = []

    for answer in answers:
        case_id = answer["case_id"]
        record = record_by_id[case_id]
        condition = unsupported_by_id[case_id]
        if (record.get("utterance") != answer["utterance"]
                or condition.get("utterance") != answer["utterance"]):
            raise ValueError("scoring_utterance_alignment")
        truth = decode_answer(answer)
        baseline = keyword_baseline(answer["utterance"])
        prediction = record.get("intent")
        if prediction is not None and not all(record.get(name) is True for name in stage_names):
            raise ValueError("valid_intent_without_complete_stages")
        expected_phrases = set(json.loads(condition["unsupported_condition_phrases"]))
        if condition["expected_cannot_guarantee_constraint"] not in ("true", "false"):
            raise ValueError("scoring_unsupported_status_invalid")
        expected_status = condition["expected_cannot_guarantee_constraint"] == "true"
        if expected_status != bool(expected_phrases):
            raise ValueError("scoring_unsupported_answer_inconsistent")
        expected_phrase_total += len(expected_phrases)
        baseline_matches = []
        ai_matches = []
        for field in CORE_FIELDS:
            bucket = fields[field]
            gold = truth[field]
            baseline_correct = baseline[field] == gold
            baseline_matches.append(baseline_correct)
            if baseline_correct:
                bucket["baseline"]["correct"] += 1
            is_explicit = explicit_gold(field, gold)
            subset = bucket["explicit" if is_explicit else "unspoken"]
            subset["gold_cases"] += 1
            if is_explicit:
                subset["baseline_correct"] += baseline_correct
            else:
                subset["baseline_exact"] += baseline_correct
                subset["baseline_false_fills"] += unspoken_false_fill(field, baseline[field])
                if field == "trajectory" and baseline[field] != gold and not unspoken_false_fill(field, baseline[field]):
                    subset["baseline_no_order_classification_errors"] += 1
            if prediction is None:
                ai_matches.append(False)
                continue
            subset["valid_cases"] += 1
            correct = prediction[field] == gold
            ai_matches.append(correct)
            if correct:
                bucket["end_to_end"]["correct"] += 1
                bucket["valid_only"]["correct"] += 1
                if is_explicit:
                    subset["ai_end_to_end_correct"] += 1
                    subset["ai_valid_correct"] += 1
                else:
                    subset["ai_end_to_end_exact"] += 1
                    subset["ai_valid_exact"] += 1
            elif not is_explicit:
                if unspoken_false_fill(field, prediction[field]):
                    subset["ai_false_fills"] += 1
                elif field == "trajectory":
                    subset["ai_no_order_classification_errors"] += 1
        baseline_cards += all(baseline_matches)
        if prediction is None:
            unfulfilled_failed += len(expected_phrases)
            case_summaries.append({"case_id": case_id, "valid": False,
                                   "error_category": record.get("error_category", "no_valid_intent")})
            continue
        ai_cards += all(ai_matches)
        ai_melody += prediction["requires_melody_present"] == truth["requires_melody_present"]
        found = {item["evidence"] for item in prediction["constraints"]}
        status_ok = bool(found) == expected_status
        exact_ok = found == expected_phrases
        status += status_ok
        exact_sets += exact_ok
        tp += len(found & expected_phrases)
        fp += len(found - expected_phrases)
        fn += len(expected_phrases - found)
        case_summaries.append({"case_id": case_id, "valid": True,
                               "wrong_core_fields": [field for field, correct in zip(CORE_FIELDS, ai_matches) if not correct],
                               "unsupported_status_wrong": not status_ok,
                               "unsupported_exact_set_wrong": not exact_ok,
                               "unsupported_false_positive_count": len(found - expected_phrases),
                               "unsupported_missed_count": len(expected_phrases - found)})
    for bucket in fields.values():
        for name in ("explicit", "unspoken"):
            subset = bucket[name]
            subset["invalid_or_missing_cases"] = subset["gold_cases"] - subset["valid_cases"]

    return {
        "score_version": SCORE_VERSION, "total_cases": total,
        "attempted_calls": sum(record.get("attempted", True) is True for record in records),
        "valid_responses": valid,
        "failed_calls": total - valid, "stages": stages,
        "fields": fields,
        "core_cards": {"end_to_end_correct": ai_cards, "end_to_end_denominator": total,
                       "valid_correct": ai_cards, "valid_denominator": valid,
                       "baseline_correct": baseline_cards, "baseline_denominator": total},
        "requires_melody_present": {"end_to_end_correct": ai_melody,
                                    "end_to_end_denominator": total,
                                    "valid_correct": ai_melody, "valid_denominator": valid},
        "unsupported": {"status_end_to_end_correct": status, "status_end_to_end_denominator": total,
                        "status_valid_correct": status, "status_valid_denominator": valid,
                        "exact_set_end_to_end_correct": exact_sets, "exact_set_end_to_end_denominator": total,
                        "exact_set_valid_correct": exact_sets, "exact_set_valid_denominator": valid,
                        "expected_phrase_total": expected_phrase_total,
                        "unfulfilled_phrases_due_to_invalid": unfulfilled_failed,
                        "unfulfilled_phrases_end_to_end": fn + unfulfilled_failed,
                        "valid_true_positive_phrases": tp if valid else None,
                        "valid_false_positive_phrases": fp if valid else None,
                        "valid_missed_phrases": fn if valid else None},
        "case_summaries": case_summaries,
    }
