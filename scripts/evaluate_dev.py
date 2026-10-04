"""One pass over the 12 approved synthetic development sentences only."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from music_intent.config import get_settings  # noqa: E402
from music_intent.evaluation import decode_answer, score_records  # noqa: E402
from music_intent.intent import CORE_FIELDS  # noqa: E402
from music_intent.openrouter_client import OpenRouterFailure, parse_once  # noqa: E402
from music_intent.pricing import estimate_standard_cost_usd  # noqa: E402

REPORTS = ROOT / "reports"
EXPECTED_IDS = {f"dev_{index:03d}" for index in range(1, 13)}
EVIDENCE_FAILURES = {"missing_evidence", "invalid_evidence_value", "unexpected_evidence",
                     "evidence_not_in_utterance"}
STRUCTURE_FAILURES = {
    "missing_content", "invalid_content_type", "invalid_content_json", "invalid_response_json",
    "invalid_response_shape", "incomplete_response", "output_token_limit", "missing_field",
    "extra_field", "invalid_constraint_format", "invalid_numeric_type",
}
FIELD_FAILURES = {"invalid_field_value", "numeric_out_of_range"}


def read_dev_data() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    with (ROOT / "data" / "synthetic_intents_dev.csv").open(encoding="utf-8", newline="") as handle:
        answers = list(csv.DictReader(handle))
    if (len(answers) != 12 or {row["case_id"] for row in answers} != EXPECTED_IDS
            or any(row["split"] != "dev" or row["review_status"] != "approved" for row in answers)):
        raise ValueError("dev_answers_not_approved_or_aligned")
    with (ROOT / "data" / "user_intents_v2_review.tsv").open(encoding="utf-8", newline="") as handle:
        source = [row for row in csv.DictReader(handle, delimiter="\t") if row["split"] == "dev"]
    source_by_id = {row["case_id"]: row for row in source}
    if len(source) != 12 or set(source_by_id) != EXPECTED_IDS:
        raise ValueError("dev_v2_source_alignment")
    unsupported = []
    for answer in answers:
        original = source_by_id[answer["case_id"]]
        if (original["review_status"] != "approved" or original["utterance"] != answer["utterance"]
                or original["role_id"] != answer["synthetic_role_id"]):
            raise ValueError("dev_v2_source_alignment")
        source_evidence = json.loads(original["evidence_json"])
        for field in (*CORE_FIELDS, "requires_melody_present"):
            if (answer[field] != original[field]
                    or answer[f"{field}_evidence"] != source_evidence.get(field, "")):
                raise ValueError("dev_v2_answer_mismatch")
        if (answer["ambiguous"] != original["ambiguous"]
                or answer["other_request_or_note"] != original["other_request_or_note"]):
            raise ValueError("dev_v2_answer_mismatch")
        phrases = json.loads(original["unsupported_condition_phrases"])
        if not isinstance(phrases, list) or any(
            not isinstance(phrase, str) or not phrase or phrase not in answer["utterance"]
            for phrase in phrases
        ):
            raise ValueError("dev_unsupported_evidence")
        unsupported.append({"case_id": answer["case_id"], "utterance": answer["utterance"],
                            "unsupported_condition_phrases": original["unsupported_condition_phrases"],
                            "expected_cannot_guarantee_constraint": "true" if phrases else "false",
                            "review_status": "approved"})
    return answers, unsupported


def failure_group(category: str, structure_complete: bool | None = None) -> str:
    if structure_complete is False:
        return "structure"
    if category in EVIDENCE_FAILURES:
        return "evidence"
    if category in STRUCTURE_FAILURES:
        return "structure"
    if category in FIELD_FAILURES:
        return "field_value"
    return "api"


def safe_case_summary(record: dict[str, Any], answer: dict[str, str],
                      unsupported: dict[str, str]) -> dict[str, Any]:
    case = {"case_id": record["case_id"], "json_complete": record["json_complete"],
            "required_structure_complete": record["required_structure_complete"],
            "intent_valid": record["intent"] is not None}
    prediction = record["intent"]
    if prediction is None:
        case.update({"failure_group": record["failure_group"],
                     "error_category": record["error_category"]})
        if record.get("error_field"):
            case["error_field"] = record["error_field"]
        return case
    truth = decode_answer(answer)
    found = {item["evidence"] for item in prediction["constraints"]}
    expected = set(json.loads(unsupported["unsupported_condition_phrases"]))
    case.update({"wrong_core_fields": [name for name in CORE_FIELDS
                                       if prediction[name] != truth[name]],
                 "requires_melody_present_wrong":
                     prediction["requires_melody_present"] != truth["requires_melody_present"],
                 "unsupported_exact_set_wrong": found != expected,
                 "unsupported_true_positive_count": len(found & expected),
                 "unsupported_false_positive_count": len(found - expected),
                 "unsupported_missed_count": len(expected - found),
                 "cannot_guarantee_constraint_wrong":
                     bool(found) != (unsupported["expected_cannot_guarantee_constraint"] == "true")})
    return case


def valid_answer_mismatch_count(cases: list[dict[str, Any]]) -> int:
    return sum(case["intent_valid"] and (
        bool(case["wrong_core_fields"]) or case["requires_melody_present_wrong"]
        or case["unsupported_exact_set_wrong"] or case["cannot_guarantee_constraint_wrong"]
    ) for case in cases)


def render_report(result: dict[str, Any]) -> str:
    scores = result["scores"]
    end = scores["end_to_end"]
    valid = scores["valid_only"]
    baseline = scores["keyword_baseline"]
    attempted = result["attempted_calls"]
    valid_n = scores["valid_responses"]
    def valid_cell(value: int) -> str:
        return f"{value}/{valid_n}" if valid_n else "Not evaluated (0 valid outputs)"
    lines = ["# PE6201 V2 Development Set Synthesis Evaluation", "",
             "Only the 12 author-approved development sentences are used; this is neither an official test score nor real-user data. Each request contains only the original text, the fixed runtime prompt, and the Schema, with no answers.",
             "", f"Model: `{result['model']}`; Singapore start time: `{result['started_at']}`.",
             f"Actual calls {attempted}/12; Uncalled {12-attempted}; Complete JSON {result['json_complete_calls']}/{attempted}; Required structure complete {result['required_structure_complete_calls']}/{attempted}; Local valid intent cards {valid_n}/{attempted}.",
             f"API failure {result['failure_groups'].get('api', 0)}; format/structure failure {result['failure_groups'].get('structure', 0)}; evidence failure {result['failure_groups'].get('evidence', 0)}; field value failure {result['failure_groups'].get('field_value', 0)}.",
             f"In addition, {result['valid_answer_mismatch_cases']}/{valid_n} local valid outputs are not completely consistent with the approved answers; this is an intent judgment discrepancy and was not classified as a format or evidence failure.",
             f"Early stopping: {'Yes' if result['stopped_early'] else 'No'}.",
             "", "## Six Core Fields", "",
             "| Field | Dev Set Coverage (Correct / 12) | End-to-End Called | Valid Output Only | Keyword Baseline (Called) |",
             "| --- | ---: | ---: | ---: | ---: |"]
    if result.get("classification_corrected_from_safe_trace"):
        lines[lines.index("## Six Core Fields") - 1:lines.index("## Six Core Fields") - 1] = [
            "", "Failed groups have been offline-corrected based on the saved security structure flags; no model re-invocation or modification to the ground truth was made."]
    for field in CORE_FIELDS:
        correct = end["core_fields"][field]
        lines.append(f"| `{field}` | {correct}/12 | {correct}/{attempted} | "
                     f"{valid_cell(valid['core_fields'][field])} | "
                     f"{baseline['core_fields'][field]}/{attempted} |")
    for label, key in (("Six-field full card", "core_cards"),
                       ("requires_melody_present", "requires_melody_present"),
                       ("unsupported exact sets", "unsupported_exact_sets"),
                       ("cannot_guarantee_constraint status", "cannot_guarantee_constraint_status")):
        correct = end[key]
        lines.append(f"| {label} | {correct}/12 | {correct}/{attempted} | "
                     f"{valid_cell(valid[key])} | "
                     f"{baseline['core_cards']}/{attempted} |" if key == "core_cards" else
                     f"| {label} | {correct}/12 | {correct}/{attempted} | "
                     f"{valid_cell(valid[key])} | — |")
    lines.extend(["", "The development set coverage column marks uncalled sentences as incomplete, which does not mean the model judged these sentences incorrectly. The end-to-end column counts sentences that were called but have no valid intent cards into the denominator; the valid-output-only column only measures intent cards that passed local validation.",
                  "", "## Unsupported Condition Original Term", "",
                  f"Called sentence expected original words: {end['unsupported_expected_phrases']}; end-to-end unfulfilled: {end['unsupported_unfulfilled_phrases']}, of which {end['unsupported_unfulfilled_due_to_call_failure']} belong to cards with no valid intent.",
                  (f"Valid outputs only: hits {valid['unsupported_true_positive_phrases']}, false positives {valid['unsupported_false_positive_phrases']}, misses {valid['unsupported_missed_phrases']} (calculated within {valid_n} valid outputs only)."
                   if valid_n else "Valid output only: No valid intent card, original word hit/false positive/false negative not evaluated."),
                  "", "## Security Error Summary", ""])
    if result["error_categories"]:
        for category, count in sorted(result["error_categories"].items()):
            lines.append(f"- `{category}`: {count} times")
    else:
        lines.append("- No local or call failure.")
    lines.extend(["", "## Sentence-by-Sentence Security Summary", ""])
    for case in result["case_summaries"]:
        if not case["intent_valid"]:
            lines.append(f"- `{case['case_id']}`:{case['failure_group']} / "
                         f"`{case['error_category']}`" +
                         (f" / `{case['error_field']}`" if case.get("error_field") else ""))
        else:
            wrong = ", ".join(case["wrong_core_fields"]) or "None"
            lines.append(f"- `{case['case_id']}`: Valid; Core field error: {wrong};"
                         f"Unsupported condition set error: {'Yes' if case['unsupported_exact_set_wrong'] else 'No'}.")
    tokens = result["tokens"]
    lines.extend(["", "## Dosage and Scope", "",
                  f"Input/Completion/Total tokens: {tokens['prompt_tokens']}/{tokens['completion_tokens']}/{tokens['total_tokens']}; Total reasoning tokens available: {tokens['reasoning_tokens']} (missing breakdown {result['reasoning_unavailable_calls']} times).",
                  f"Estimated cost: USD {result['estimated_cost_usd']:.6f}; Calls with missing cost estimation data: {result['cost_unavailable_calls']}. Actual billing is subject to the service provider.",
                  "No audio was downloaded, and the effectiveness of the real music library recommendation was not evaluated. The test set was not frozen, and 30 formal tests were not run.", ""])
    return "\n".join(lines)


def run(report_dir: Path | None = None) -> dict[str, Any]:
    answers, unsupported = read_dev_data()
    by_answer = {row["case_id"]: row for row in answers}
    by_unsupported = {row["case_id"]: row for row in unsupported}
    key, model = get_settings()
    target = report_dir or REPORTS
    target.mkdir(exist_ok=True)
    paths = {name: target / f"dev_evaluation.{name}" for name in ("started.json", "trace.jsonl", "json", "md")}
    if any(path.exists() for path in paths.values()):
        raise ValueError("dev_evaluation_files_already_exist")
    started_at = datetime.now(ZoneInfo("Asia/Singapore")).isoformat(timespec="seconds")
    paths["started.json"].write_text(json.dumps({"started_at": started_at, "model": model,
                                                   "synthetic_dev_cases": 12}, indent=2) + "\n", encoding="utf-8")
    records = []
    safe_trace = []
    consecutive = 0
    stopped_early = False
    with paths["trace.jsonl"].open("x", encoding="utf-8") as trace:
        for answer in answers:
            case_id = answer["case_id"]
            record: dict[str, Any] = {"case_id": case_id, "utterance": answer["utterance"]}
            try:
                intent, info = parse_once(answer["utterance"], key, model)
                record.update({"intent": intent, "model": info["model"], "usage": info["usage"],
                               "json_complete": info["json_complete"],
                               "required_structure_complete": info["required_structure_complete"]})
                consecutive = 0
            except OpenRouterFailure as error:
                group = failure_group(error.category, error.required_structure_complete)
                record.update({"intent": None, "model": error.model or model, "usage": error.usage,
                               "json_complete": error.json_complete,
                               "required_structure_complete": error.required_structure_complete,
                               "error_category": error.category, "error_field": error.field,
                               "failure_group": group})
                consecutive = consecutive + 1 if group in {"api", "structure"} else 0
            records.append(record)
            safe = {name: record.get(name) for name in
                    ("case_id", "model", "usage", "json_complete", "required_structure_complete",
                     "error_category", "error_field", "failure_group")}
            safe["intent_valid"] = record["intent"] is not None
            safe_trace.append(safe)
            trace.write(json.dumps(safe, ensure_ascii=False) + "\n")
            trace.flush()
            print(f"dev_case={case_id} status={'valid' if safe['intent_valid'] else record['failure_group']}",
                  flush=True)
            if consecutive >= 3:
                stopped_early = True
                print("dev_evaluation=stopped category=three_consecutive_api_or_structure_failures",
                      flush=True)
                break
    attempted_answers = [by_answer[record["case_id"]] for record in records]
    attempted_unsupported = [by_unsupported[record["case_id"]] for record in records]
    scores = score_records(records, attempted_answers, attempted_unsupported)
    scores.pop("failures")  # Never persist model-generated phrases from mismatch details.
    token_names = ("prompt_tokens", "completion_tokens", "total_tokens", "reasoning_tokens")
    tokens = {name: sum(record["usage"].get(name, 0) for record in records) for name in token_names}
    costs = [estimate_standard_cost_usd(record["model"], record["usage"]) for record in records]
    result = {
        "synthetic_dev": True, "started_at": started_at, "model": model,
        "expected_cases": 12, "attempted_calls": len(records), "stopped_early": stopped_early,
        "json_complete_calls": sum(record["json_complete"] is True for record in records),
        "required_structure_complete_calls": sum(
            record["required_structure_complete"] is True for record in records),
        "locally_valid_calls": scores["valid_responses"],
        "failure_groups": dict(Counter(record["failure_group"] for record in records
                                       if record["intent"] is None)),
        "error_categories": dict(Counter(record["error_category"] for record in records
                                         if record["intent"] is None)),
        "scores": scores, "tokens": tokens,
        "reasoning_unavailable_calls": sum("reasoning_tokens" not in record["usage"]
                                           for record in records),
        "cost_unavailable_calls": sum(value is None for value in costs),
        "estimated_cost_usd": round(sum(value for value in costs if value is not None), 8),
        "case_summaries": [safe_case_summary(record, by_answer[record["case_id"]],
                                             by_unsupported[record["case_id"]]) for record in records],
    }
    result["valid_answer_mismatch_cases"] = valid_answer_mismatch_count(result["case_summaries"])
    with paths["json"].open("x", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    with paths["md"].open("x", encoding="utf-8") as handle:
        handle.write(render_report(result))
    print(f"dev_evaluation=complete attempted={len(records)} valid={scores['valid_responses']}", flush=True)
    return result


def reconcile_safe_classification(report_dir: Path) -> dict[str, Any]:
    """Correct grouping from saved safe metadata only; never make an API call."""
    trace_path = report_dir / "dev_evaluation.trace.jsonl"
    result_path = report_dir / "dev_evaluation.json"
    markdown_path = report_dir / "dev_evaluation.md"
    trace = [json.loads(line) for line in trace_path.read_text(encoding="utf-8").splitlines()]
    result = json.loads(result_path.read_text(encoding="utf-8"))
    if (len(trace) != result["attempted_calls"]
            or [row["case_id"] for row in trace] !=
            [row["case_id"] for row in result["case_summaries"]]):
        raise ValueError("dev_safe_trace_alignment")
    consecutive = 0
    for index, row in enumerate(trace):
        if row["intent_valid"]:
            consecutive = 0
            continue
        group = failure_group(row["error_category"], row["required_structure_complete"])
        row["failure_group"] = group
        result["case_summaries"][index]["failure_group"] = group
        consecutive = consecutive + 1 if group in {"api", "structure"} else 0
        if consecutive >= 3 and index != len(trace) - 1:
            raise ValueError("dev_run_exceeded_stop_rule")
    result["failure_groups"] = dict(Counter(
        row["failure_group"] for row in trace if not row["intent_valid"]))
    result["valid_answer_mismatch_cases"] = valid_answer_mismatch_count(result["case_summaries"])
    result["classification_corrected_from_safe_trace"] = True
    trace_path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in trace),
                          encoding="utf-8")
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_report(result), encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="One pass over 12 approved synthetic development sentences")
    parser.add_argument("--allow-paid-dev", action="store_true")
    args = parser.parse_args(argv)
    if not args.allow_paid_dev:
        print("dev_evaluation=not_run category=authorization_required")
        return 2
    try:
        run()
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(f"dev_evaluation=failed category={error}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
