"""Independent, one-pass comparison of the compact wire format on approved dev cases."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "prototypes"))
sys.path.insert(0, str(ROOT / "scripts"))

from compact_dev_request import VERSION, build_candidate_request, load_versioned_format  # noqa: E402
from compact_intent_format import convert_syntax  # noqa: E402
from evaluate_dev import (  # noqa: E402
    failure_group, read_dev_data, safe_case_summary, valid_answer_mismatch_count,
)
from music_intent.config import get_settings  # noqa: E402
from music_intent.evaluation import score_records  # noqa: E402
from music_intent.intent import CORE_FIELDS, InvalidIntent, validate_intent  # noqa: E402
from music_intent.openrouter_client import (  # noqa: E402
    ENDPOINT, OpenRouterFailure, classify_http_error, classify_transport_error,
    required_structure_complete,
    safe_finish_reason,
)
from music_intent.pricing import estimate_standard_cost_usd  # noqa: E402

MODEL = "google/gemini-3.5-flash-lite"
REPORTS = ROOT / "reports"
PRIVATE_DIR = REPORTS / "private_dev_predictions"
PRIVATE_FILE = PRIVATE_DIR / "compact_dev_predictions.jsonl"
PUBLIC_JSON = REPORTS / "compact_dev_evaluation.json"
PUBLIC_MD = REPORTS / "compact_dev_evaluation.md"
ORIGINAL_JSON = REPORTS / "dev_evaluation.json"


def safe_usage(raw: Any) -> dict[str, int]:
    if not isinstance(raw, dict):
        return {}
    usage = {name: value for name in ("prompt_tokens", "completion_tokens", "total_tokens")
             if type(value := raw.get(name)) is int and value >= 0}
    details = raw.get("completion_tokens_details")
    reasoning = details.get("reasoning_tokens") if isinstance(details, dict) else None
    if reasoning is None:
        reasoning = raw.get("reasoning_tokens")
    if type(reasoning) is int and reasoning >= 0:
        usage["reasoning_tokens"] = reasoning
    return usage


def _base_record(case_id: str, utterance: str, model: str) -> dict[str, Any]:
    return {"case_id": case_id, "utterance": utterance, "intent": None,
            "model": model, "usage": {}, "finish_reason": "unavailable",
            "json_complete": False, "required_structure_complete": None,
            "conversion_complete": False, "error_category": None, "error_field": None,
            "failure_group": None, "failure_stage": None}


def _fail(record: dict[str, Any], category: str, stage: str,
          field: str | None = None) -> None:
    record["error_category"] = category
    record["error_field"] = field
    record["failure_stage"] = stage
    record["failure_group"] = ("structure" if stage == "conversion" else
                               failure_group(category, record["required_structure_complete"]))


def inspect_candidate_response(payload: Any, case_id: str, utterance: str,
                               requested_model: str, schema: dict[str, Any]
                               ) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return safe scoring data and a separate local-only raw prediction record."""
    record = _base_record(case_id, utterance, requested_model)
    private = {"case_id": case_id, "raw_prediction": None, "converted_v2": None}
    if not isinstance(payload, dict):
        _fail(record, "invalid_response_shape", "api")
        return record, private
    record["usage"] = safe_usage(payload.get("usage"))
    model = payload.get("model")
    if isinstance(model, str) and re.fullmatch(r"[A-Za-z0-9._:/-]{1,120}", model):
        record["model"] = model
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        _fail(record, "missing_content", "structure")
        return record, private
    choice = choices[0]
    record["finish_reason"] = safe_finish_reason(choice.get("finish_reason"))
    message = choice.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if isinstance(content, str):
        private["raw_prediction"] = content
    if record["finish_reason"] == "length":
        _fail(record, "output_token_limit", "structure")
        return record, private
    if record["finish_reason"] != "stop":
        _fail(record, "incomplete_response", "structure")
        return record, private
    if content is None or content == "":
        _fail(record, "missing_content", "structure")
        return record, private
    if not isinstance(content, str):
        _fail(record, "invalid_content_type", "structure")
        return record, private
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        _fail(record, "invalid_content_json", "structure")
        return record, private
    record["json_complete"] = True
    record["required_structure_complete"] = required_structure_complete(schema, parsed)
    try:
        converted = convert_syntax(parsed)
    except InvalidIntent as error:
        _fail(record, error.category, "conversion", error.field)
        return record, private
    record["conversion_complete"] = True
    private["converted_v2"] = converted
    try:
        record["intent"] = validate_intent(converted, utterance)
    except InvalidIntent as error:
        _fail(record, error.category, "local_validation", error.field)
    return record, private


def call_candidate_once(utterance: str, key: str, model: str, prompt: str,
                        schema: dict[str, Any], timeout: int = 30) -> Any:
    body = json.dumps(build_candidate_request(utterance, model, prompt, schema),
                      ensure_ascii=False).encode("utf-8")
    request = Request(ENDPOINT, data=body, method="POST",
                      headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        response = urlopen(request, timeout=timeout)
    except HTTPError as error:
        raise OpenRouterFailure(classify_http_error(error.code), model=model,
                                http_status=error.code, transport_phase="http_status") from None
    except (URLError, TimeoutError, OSError) as error:
        raise OpenRouterFailure(classify_transport_error(error, "open_or_headers"), model=model,
                                transport_phase="open_or_headers") from None
    response_status = getattr(response, "status", None)
    try:
        with response:
            return json.load(response)
    except HTTPError as error:
        raise OpenRouterFailure(classify_http_error(error.code), model=model,
                                http_status=error.code, transport_phase="http_status") from None
    except (URLError, TimeoutError, OSError) as error:
        raise OpenRouterFailure(classify_transport_error(error, "response_body"), model=model,
                                http_status=response_status,
                                transport_phase="response_body") from None
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise OpenRouterFailure("invalid_response_json", model=model) from None


def verify_private_path(path: Path = PRIVATE_FILE) -> None:
    if path.parent.is_symlink() or path.is_symlink() or path.exists():
        raise ValueError("private_prediction_target_not_new")
    relative = path.relative_to(ROOT)
    ignore = subprocess.run(["git", "check-ignore", "-q", "--", str(relative)],
                            cwd=ROOT, capture_output=True, check=False)
    tracked = subprocess.run(["git", "ls-files", "--cached", "--", str(relative.parent)],
                             cwd=ROOT, capture_output=True, check=False)
    if ignore.returncode != 0 or tracked.returncode != 0 or tracked.stdout.strip():
        raise ValueError("private_prediction_git_guard_failed")


def _metric_rows(new: dict[str, Any], old: dict[str, Any]) -> list[str]:
    new_score, old_score = new["scores"], old["scores"]
    n = new_score["end_to_end"]["denominator"]
    valid_n = new_score["valid_only"]["denominator"]
    old_n = old_score["end_to_end"]["denominator"]
    old_valid_n = old_score["valid_only"]["denominator"]
    rows = ["| Metric | Original End-to-End | Candidate End-to-End | Original Valid-Only | Candidate Valid-Only | Same Keyword Baseline |",
            "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for field in CORE_FIELDS:
        rows.append(f"| `{field}` | {old_score['end_to_end']['core_fields'][field]}/{old_n} | "
                    f"{new_score['end_to_end']['core_fields'][field]}/{n} | "
                    f"{old_score['valid_only']['core_fields'][field]}/{old_valid_n} | "
                    f"{new_score['valid_only']['core_fields'][field]}/{valid_n} | "
                    f"{new_score['keyword_baseline']['core_fields'][field]}/{n} |")
    for label, name in (("six_field_full_card", "core_cards"),
                        ("requires_melody_present", "requires_melody_present"),
                        ("unsupported exact word sets not fully matched", "unsupported_exact_sets"),
                        ("cannot_guarantee_constraint status", "cannot_guarantee_constraint_status")):
        baseline = (f"{new_score['keyword_baseline']['core_cards']}/{n}" if name == "core_cards" else "—")
        rows.append(f"| {label} | {old_score['end_to_end'][name]}/{old_n} | "
                    f"{new_score['end_to_end'][name]}/{n} | "
                    f"{old_score['valid_only'][name]}/{old_valid_n} | "
                    f"{new_score['valid_only'][name]}/{valid_n} | {baseline} |")
    return rows


def render_report(result: dict[str, Any], old: dict[str, Any]) -> str:
    score = result["scores"]
    valid = score["valid_only"]
    end = score["end_to_end"]
    attempted = result["attempted_calls"]
    lines = ["# Nine-field shorthand format: controlled comparison of synthetic development sets", "",
             "This control group modification changed **two text portions: the prompt words required for the output Schema and the explanation shorthand format**, rather than just altering a single API parameter. The model, 12 synthetic development sentences, other request parameters, V2 answers, keyword baselines, and local validation remained consistent. Formal test sentences were not called.",
             "", f"Candidate version: `{result['version']}`; Prompt SHA-256: `{result['prompt_sha256']}`; Schema SHA-256: `{result['schema_sha256']}`.",
             f"Model: `{result['model']}`;Singapore start time: `{result['started_at']}`.",
             f"Calls {attempted}/12; stopped early: {'Yes' if result['stopped_early'] else 'No'}; complete JSON {result['json_complete_calls']}/{attempted}; required structure complete {result['required_structure_complete_calls']}/{attempted}; compact conversion complete {result['conversion_complete_calls']}/{attempted}; V2 local validation passed {result['locally_valid_calls']}/{attempted}.",
             f"Failed to acquire valid intent card {score['failed_calls']} times (including API failures {result['failure_groups'].get('api', 0)} times); groups {json.dumps(result['failure_groups'], ensure_ascii=False, sort_keys=True)}; safety error categories {json.dumps(result['error_categories'], ensure_ascii=False, sort_keys=True)}.",
             "", "## Comparison with Original Version and Keyword Baseline", ""]
    if attempted != 12:
        lines.append("Candidate version early stopping, candidates and baselines only count called development sentences; original version counts all 12 sentences, horizontal values cannot be directly used as performance differences with the same denominator.")
        lines.append("")
    lines.extend(_metric_rows(result, old))
    lines.extend(["", "End-to-end denominator includes calls without valid intent cards; valid-output-only denominator includes only intent cards that pass conversion and V2 local validation. Invalid outputs do not count as model false positives or false negatives for conditions. The keyword baseline still uses the project's original implementation.",
                  "", "## Unsupported Condition Original Term", "",
                  f"Candidate end-to-end expected original words: {end['unsupported_expected_phrases']}, unfulfilled: {end['unsupported_unfulfilled_phrases']}; among which {end['unsupported_unfulfilled_due_to_call_failure']} are due to no valid intent cards.",
                  (f"Candidate valid output only: hit {valid['unsupported_true_positive_phrases']}, false positive {valid['unsupported_false_positive_phrases']}, missed {valid['unsupported_missed_phrases']}; denominator is {valid['denominator']} valid outputs, including {valid['unsupported_expected_phrases']} expected original words."
                   if valid['denominator'] else "The candidate has no valid output, model original word hit/false alarm/missed rate will not be calculated."),
                  f"Original valid-only output: hits {old['scores']['valid_only']['unsupported_true_positive_phrases']}, false positives {old['scores']['valid_only']['unsupported_false_positive_phrases']}, misses {old['scores']['valid_only']['unsupported_missed_phrases']}; denominator is {old['scores']['valid_only']['denominator']} items.",
                  "", "## Errors and Usage", ""])
    for stage, count in sorted(result["failure_stages"].items()):
        lines.append(f"- `{stage}`: {count} times")
    for case in result["case_summaries"]:
        if not case["intent_valid"]:
            lines.append(f"- `{case['case_id']}`:{case['failure_group']} / {case['error_category']}" +
                         (f" / {case['error_field']}" if case.get("error_field") else ""))
        else:
            wrong = ", ".join(case["wrong_core_fields"]) or "None"
            lines.append(f"- `{case['case_id']}`: Valid; core field error: {wrong}; condition set error: {'Yes' if case['unsupported_exact_set_wrong'] else 'No'}.")
    token = result["tokens"]
    false_positive_cases = sum(
        case.get("unsupported_false_positive_count", 0) > 0
        for case in result["case_summaries"] if case["intent_valid"]
    )
    lines.extend(["", f"Candidate input / completion / total tokens: {token['prompt_tokens']} / {token['completion_tokens']} / {token['total_tokens']}; Available reasoning tokens: {token['reasoning_tokens']} (missing details {result['reasoning_unavailable_calls']} times).",
                  f"Candidate estimated cost USD {result['estimated_cost_usd']:.6f}; calls with missing estimable data {result['cost_unavailable_calls']}. Original input/completion/total tokens: {old['tokens']['prompt_tokens']}/{old['tokens']['completion_tokens']}/{old['tokens']['total_tokens']}; original estimated cost USD {old['estimated_cost_usd']:.6f}. Actual billing is subject to the provider.",
                  "", "## Comparative Judgment", "",
                  f"In terms of format: Original required structure {old['required_structure_complete_calls']}/12, locally valid {old['locally_valid_calls']}/12; Candidate required structure {result['required_structure_complete_calls']}/{attempted}, conversion complete {result['conversion_complete_calls']}/{attempted}, locally valid {result['locally_valid_calls']}/{attempted}. This shows that the current candidate output more frequently meets the structural requirements, but it cannot be proven solely based on a single dev set comparison that the reason is the abbreviated Schema.",
                  f"Regarding intent: original six-field full card {old['scores']['end_to_end']['core_cards']}/12, candidate {end['core_cards']}/{attempted}, keyword baseline {score['keyword_baseline']['core_cards']}/{attempted}. The candidate has more valid outputs, but the number of correct full cards did not increase accordingly; the valid output denominators are also different (original {old['scores']['valid_only']['denominator']}, candidate {valid['denominator']}), so formatting success cannot be equated to intent judgment success.",
                  f"In terms of constraints: The candidate still has original-word false positives in {false_positive_cases}/{valid['denominator']} valid outputs, totaling {valid['unsupported_false_positive_phrases']}; there are also {valid['unsupported_missed_phrases']} misses. The original valid outputs have {old['scores']['valid_only']['unsupported_false_positive_phrases']} false positives and {old['scores']['valid_only']['unsupported_missed_phrases']} misses. The valid sets of the two versions differ, so total counts alone cannot be used to determine the change in the false positive rate.",
                  "Recommendation: Do not adopt the candidate format as the official runtime for now. It is worth keeping as a structural development prototype, but intent card drops and constraint false positives must first be resolved on the development set before considering another round of controlled comparison; do not use these results to modify approved answers or infer official test scores.",
                  "", "This report only compares intent parsing of synthetic development sentences. Successful structure or conversion does not equate to correct intent judgment; raw model predictions and conversion results reside only in local Git-ignored directories. No formal pre-check flag was generated, and formal tests were not frozen or run.", ""])
    return "\n".join(lines)


def run() -> dict[str, Any]:
    answers, unsupported = read_dev_data()
    old = json.loads(ORIGINAL_JSON.read_text(encoding="utf-8"))
    if old.get("attempted_calls") != 12 or old.get("model") != MODEL:
        raise ValueError("original_dev_report_mismatch")
    prompt, schema, digests = load_versioned_format()
    verify_private_path()
    if PUBLIC_JSON.exists() or PUBLIC_MD.exists():
        raise ValueError("candidate_report_already_exists")
    key, model = get_settings()
    if model != MODEL:
        raise ValueError("candidate_model_mismatch")
    REPORTS.mkdir(exist_ok=True)
    PRIVATE_DIR.mkdir(mode=0o700, exist_ok=True)
    os.chmod(PRIVATE_DIR, 0o700)
    started_at = datetime.now(ZoneInfo("Asia/Singapore")).isoformat(timespec="seconds")
    descriptor = os.open(PRIVATE_FILE, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    records: list[dict[str, Any]] = []
    consecutive = 0
    stopped_early = False
    with os.fdopen(descriptor, "w", encoding="utf-8") as private_file:
        for answer in answers:
            case_id = answer["case_id"]
            utterance = answer["utterance"]
            try:
                payload = call_candidate_once(utterance, key, model, prompt, schema)
                record, private = inspect_candidate_response(payload, case_id, utterance, model, schema)
            except OpenRouterFailure as error:
                record = _base_record(case_id, utterance, error.model or model)
                record["usage"] = error.usage
                _fail(record, error.category, "api")
                private = {"case_id": case_id, "raw_prediction": None, "converted_v2": None}
            records.append(record)
            private.update({"model": record["model"], "finish_reason": record["finish_reason"],
                            "usage": record["usage"], "json_complete": record["json_complete"],
                            "required_structure_complete": record["required_structure_complete"],
                            "conversion_complete": record["conversion_complete"],
                            "intent_valid": record["intent"] is not None,
                            "error_category": record["error_category"],
                            "error_field": record["error_field"]})
            private_file.write(json.dumps(private, ensure_ascii=False) + "\n")
            private_file.flush()
            consecutive = (consecutive + 1 if record["intent"] is None and
                           record["failure_group"] in {"api", "structure"} else 0)
            print(f"compact_dev_case={case_id} status={'valid' if record['intent'] is not None else record['failure_group']}", flush=True)
            if consecutive >= 3:
                stopped_early = True
                print("compact_dev=stopped category=three_consecutive_api_or_structure_failures", flush=True)
                break
    answer_by_id = {row["case_id"]: row for row in answers}
    unsupported_by_id = {row["case_id"]: row for row in unsupported}
    attempted_answers = [answer_by_id[record["case_id"]] for record in records]
    attempted_unsupported = [unsupported_by_id[record["case_id"]] for record in records]
    scores = score_records(records, attempted_answers, attempted_unsupported)
    scores.pop("failures")  # Model-generated terms remain in the ignored private file only.
    if len(records) == 12 and scores["keyword_baseline"] != old["scores"]["keyword_baseline"]:
        raise ValueError("keyword_baseline_changed")
    token_names = ("prompt_tokens", "completion_tokens", "total_tokens", "reasoning_tokens")
    tokens = {name: sum(record["usage"].get(name, 0) for record in records) for name in token_names}
    costs = [estimate_standard_cost_usd(record["model"], record["usage"]) for record in records]
    result = {
        "synthetic_dev": True, "version": VERSION, **digests, "started_at": started_at,
        "model": model, "expected_cases": 12, "attempted_calls": len(records),
        "stopped_early": stopped_early,
        "json_complete_calls": sum(record["json_complete"] is True for record in records),
        "required_structure_complete_calls": sum(record["required_structure_complete"] is True for record in records),
        "conversion_complete_calls": sum(record["conversion_complete"] is True for record in records),
        "locally_valid_calls": scores["valid_responses"],
        "failure_groups": dict(Counter(record["failure_group"] for record in records if record["intent"] is None)),
        "failure_stages": dict(Counter(record["failure_stage"] for record in records if record["intent"] is None)),
        "error_categories": dict(Counter(record["error_category"] for record in records if record["intent"] is None)),
        "scores": scores, "tokens": tokens,
        "reasoning_unavailable_calls": sum("reasoning_tokens" not in record["usage"] for record in records),
        "cost_unavailable_calls": sum(cost is None for cost in costs),
        "estimated_cost_usd": round(sum(cost for cost in costs if cost is not None), 8),
        "case_summaries": [safe_case_summary(record, answer_by_id[record["case_id"]],
                                              unsupported_by_id[record["case_id"]]) for record in records],
    }
    result["valid_answer_mismatch_cases"] = valid_answer_mismatch_count(result["case_summaries"])
    with PUBLIC_JSON.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    with PUBLIC_MD.open("x", encoding="utf-8") as handle:
        handle.write(render_report(result, old))
    print(f"compact_dev=complete attempted={len(records)} valid={scores['valid_responses']}", flush=True)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="One compact-format pass over approved synthetic dev cases")
    parser.add_argument("--allow-paid-dev", action="store_true")
    args = parser.parse_args(argv)
    if not args.allow_paid_dev:
        print("compact_dev=not_run category=authorization_required")
        return 2
    try:
        run()
    except Exception:
        # Never let an HTTP response, prediction, credential, or request header
        # appear in a traceback. Inspect local files and tests for diagnosis.
        print("compact_dev=failed category=preflight_or_local_error")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
