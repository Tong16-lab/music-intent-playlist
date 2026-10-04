"""One prompt-only comparison on the 12 approved synthetic development cases."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "prototypes"))
sys.path.insert(0, str(ROOT / "scripts"))

import evaluate_compact_dev as v1_runner  # noqa: E402
from compact_dev_request import load_versioned_format  # noqa: E402
from compact_dev_v2_request import VERSION, load_v2_format  # noqa: E402
from music_intent.config import get_settings  # noqa: E402
from music_intent.evaluation import score_records  # noqa: E402
from music_intent.intent import CORE_FIELDS  # noqa: E402
from music_intent.openrouter_client import OpenRouterFailure  # noqa: E402
from music_intent.pricing import estimate_standard_cost_usd  # noqa: E402

MODEL = v1_runner.MODEL
REPORTS = ROOT / "reports"
PRIVATE_DIR = REPORTS / "private_dev_predictions"
PRIVATE_FILE = PRIVATE_DIR / "compact_dev_v2_predictions.jsonl"
PUBLIC_JSON = REPORTS / "compact_dev_v2_evaluation.json"
PUBLIC_MD = REPORTS / "compact_dev_v2_evaluation.md"
ORIGINAL_JSON = REPORTS / "dev_evaluation.json"
V1_JSON = REPORTS / "compact_dev_evaluation.json"
MAX_ESTIMATED_COST_USD = 0.05


def estimate_run_cost(v1_result: dict[str, Any], v1_prompt: str, v2_prompt: str) -> dict[str, Any]:
    """Planning estimate from observed v1 use, with explicit conservative cushions."""
    if v1_result.get("attempted_calls") != 12 or v1_result.get("model") != MODEL:
        raise ValueError("v1_report_incomparable")
    added_chars = len(v2_prompt) - len(v1_prompt)
    if added_chars < 0:
        raise ValueError("v2_prompt_shorter_than_v1")
    prompt_tokens = v1_result["tokens"]["prompt_tokens"] + added_chars * 2 * 12
    completion_tokens = (v1_result["tokens"]["completion_tokens"] * 5 + 3) // 4
    cost = estimate_standard_cost_usd(MODEL, {
        "prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens,
    })
    if cost is None:
        raise ValueError("run_cost_unavailable")
    return {"added_prompt_characters": added_chars,
            "assumed_prompt_tokens": prompt_tokens,
            "assumed_completion_tokens": completion_tokens,
            "estimated_cost_usd": round(cost, 8),
            "method": "v1 observed input + 2 tokens per added character per call; v1 completion + 25%"}


def _metric_tables(result: dict[str, Any], original: dict[str, Any],
                   v1: dict[str, Any]) -> list[str]:
    versions = (("Original", original), ("Abbreviated v1", v1), ("Prompt v2", result))
    lines = ["| Metric | Original End-to-End | Abbreviated v1 End-to-End | Prompt v2 End-to-End | Same Keyword Baseline |",
             "| --- | ---: | ---: | ---: | ---: |"]
    for field in CORE_FIELDS:
        values = [f"{item['scores']['end_to_end']['core_fields'][field]}/{item['scores']['end_to_end']['denominator']}"
                  for _, item in versions]
        base = result["scores"]["keyword_baseline"]
        lines.append(f"| `{field}` | {' | '.join(values)} | {base['core_fields'][field]}/{base['denominator']} |")
    for label, key in (("Six-field full card", "core_cards"),
                       ("requires_melody_present", "requires_melody_present"),
                       ("unsupported exact sets", "unsupported_exact_sets"),
                       ("cannot_guarantee_constraint status correct", "cannot_guarantee_constraint_status")):
        values = [f"{item['scores']['end_to_end'][key]}/{item['scores']['end_to_end']['denominator']}"
                  for _, item in versions]
        baseline = (f"{result['scores']['keyword_baseline']['core_cards']}/{result['scores']['keyword_baseline']['denominator']}"
                    if key == "core_cards" else "—")
        lines.append(f"| {label} | {' | '.join(values)} | {baseline} |")
    lines.extend(["", "The denominators for the only valid outputs are original 6, shorthand v1 9, prompt v2 " +
                  str(result["scores"]["valid_only"]["denominator"]) + ";the table below only measures cards that passed conversion and local validation.",
                  "", "| Metric | Original only valid | Abbreviation v1 only valid | Prompt v2 only valid |",
                  "| --- | ---: | ---: | ---: |"])
    for field in CORE_FIELDS:
        values = [f"{item['scores']['valid_only']['core_fields'][field]}/{item['scores']['valid_only']['denominator']}"
                  for _, item in versions]
        lines.append(f"| `{field}` | {' | '.join(values)} |")
    for label, key in (("Six-field full card", "core_cards"),
                       ("unsupported exact sets", "unsupported_exact_sets"),
                       ("cannot_guarantee_constraint status correct", "cannot_guarantee_constraint_status")):
        values = [f"{item['scores']['valid_only'][key]}/{item['scores']['valid_only']['denominator']}"
                  for _, item in versions]
        lines.append(f"| {label} | {' | '.join(values)} |")
    return lines


def render_report(result: dict[str, Any], original: dict[str, Any],
                  v1: dict[str, Any]) -> str:
    attempted = result["attempted_calls"]
    scores = result["scores"]
    end = scores["end_to_end"]
    valid = scores["valid_only"]
    lines = ["# compact-dev-v2: Comparison of synthetic development sets with prompt-only modifications", "",
             "This round reuses the v1 schema, converter, model, request parameters, approved V2 answers, keyword baseline, and local validator; only the general intent-judgment instructions change. Each request sends one development example without its answer. No formal test example was used in a call or to design the rules.",
             "", f"Version: `{VERSION}`; v2 prompt SHA-256: `{result['prompt_sha256']}`; v1 prompt SHA-256: `{result['v1_prompt_sha256']}`; Common Schema SHA-256 for both versions: `{result['schema_sha256']}`.",
             f"Model: `{result['model']}`;Singapore start time: `{result['started_at']}`.",
             f"Pre-estimated cost USD {result['pre_run_estimate']['estimated_cost_usd']:.6f} (based on v1 actual measurements, assuming 2 input tokens per added character and a 25% increase in completion tokens).",
             f"Actual calls {attempted}/12; Early stopped: {'Yes' if result['stopped_early'] else 'No'}. Complete JSON {result['json_complete_calls']}/{attempted}; Required structure complete {result['required_structure_complete_calls']}/{attempted}; Abbreviation conversion complete {result['conversion_complete_calls']}/{attempted}; V2 local validation passed {result['locally_valid_calls']}/{attempted}.",
             f"No valid cards {scores['failed_calls']} times, including API failures {result['failure_groups'].get('api', 0)} times; failure groups {json.dumps(result['failure_groups'], ensure_ascii=False, sort_keys=True)}; security error categories {json.dumps(result['error_categories'], ensure_ascii=False, sort_keys=True)}.",
             "", "## Version 3 and Same Keyword Baseline", ""]
    if attempted != 12:
        lines.extend(["v2 early stopping, only counting called sentences; other versions cover 12 sentences, so the horizontal correct counts do not share the same denominator.", ""])
    lines.extend(_metric_tables(result, original, v1))
    lines.extend(["", "The end-to-end denominator includes calls without valid cards; such calls are not counted as model verbatim false positives or false negatives. Complete format only indicates that the output is parsable, not that the intent judgment is correct.",
                  "", "## Unsupported conditions: State and original term are scored separately", "",
                  f"Correct status (end-to-end): original {original['scores']['end_to_end']['cannot_guarantee_constraint_status']}/12, shorthand v1 {v1['scores']['end_to_end']['cannot_guarantee_constraint_status']}/12, v2 {end['cannot_guarantee_constraint_status']}/{attempted}.",
                  f"Original word sets completely identical (end-to-end): original {original['scores']['end_to_end']['unsupported_exact_sets']}/12, shorthand v1 {v1['scores']['end_to_end']['unsupported_exact_sets']}/12, v2 {end['unsupported_exact_sets']}/{attempted}.",
                  f"v2 valid-only output: expected original phrases {valid['unsupported_expected_phrases']}; exact hits {valid['unsupported_true_positive_phrases'] if valid['denominator'] else 'unevaluated'}, false positives {valid['unsupported_false_positive_phrases'] if valid['denominator'] else 'unevaluated'}, false negatives {valid['unsupported_missed_phrases'] if valid['denominator'] else 'unevaluated'} ({valid['denominator']} valid cards). End-to-end unfulfilled original phrases {end['unsupported_unfulfilled_phrases']}, of which {end['unsupported_unfulfilled_due_to_call_failure']} are from cards without valid output.",
                  "", "## Security Error Summary", ""])
    for stage, count in sorted(result["failure_stages"].items()):
        lines.append(f"- `{stage}`: {count} times")
    for case in result["case_summaries"]:
        if not case["intent_valid"]:
            lines.append(f"- `{case['case_id']}`:{case['failure_group']} / {case['error_category']}" +
                         (f" / {case['error_field']}" if case.get("error_field") else ""))
        elif case["wrong_core_fields"] or case["unsupported_exact_set_wrong"]:
            wrong = ", ".join(case["wrong_core_fields"]) or "None"
            lines.append(f"- `{case['case_id']}`:Valid; core field error: {wrong}; original term set error: {'Yes' if case['unsupported_exact_set_wrong'] else 'No'}.")
    t = result["tokens"]
    lines.extend(["", "## Usage and Boundaries", "",
                  f"v2 input/completion/total tokens: {t['prompt_tokens']}/{t['completion_tokens']}/{t['total_tokens']}; available reasoning tokens: {t['reasoning_tokens']} (missing breakdown {result['reasoning_unavailable_calls']} times).",
                  f"v2 estimated cost USD {result['estimated_cost_usd']:.6f}; unestimatable data {result['cost_unavailable_calls']} times. Original USD {original['estimated_cost_usd']:.6f}; shorthand v1 USD {v1['estimated_cost_usd']:.6f}. Actual bill subject to the service provider.",
                  "Raw model predictions and conversion cards exist only locally in private directories ignored by Git; public reports do not contain complete raw responses, request headers, or keys. Not integrated into the official runtime, frozen, or evaluating the official test set.", ""])
    return "\n".join(lines)


def run() -> dict[str, Any]:
    answers, unsupported = v1_runner.read_dev_data()
    original = json.loads(ORIGINAL_JSON.read_text(encoding="utf-8"))
    v1 = json.loads(V1_JSON.read_text(encoding="utf-8"))
    if (original.get("attempted_calls") != 12 or v1.get("attempted_calls") != 12
            or original.get("model") != MODEL or v1.get("model") != MODEL
            or original["scores"]["keyword_baseline"] != v1["scores"]["keyword_baseline"]):
        raise ValueError("historical_dev_reports_incomparable")
    v1_prompt, _, _ = load_versioned_format()
    prompt, schema, digests = load_v2_format()
    planning = estimate_run_cost(v1, v1_prompt, prompt)
    if planning["estimated_cost_usd"] > MAX_ESTIMATED_COST_USD:
        raise ValueError("estimated_cost_above_authorized_threshold")
    v1_runner.verify_private_path(PRIVATE_FILE)
    if PUBLIC_JSON.exists() or PUBLIC_MD.exists():
        raise ValueError("v2_report_already_exists")
    key, model = get_settings()
    if model != MODEL:
        raise ValueError("v2_model_mismatch")
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
            case_id, utterance = answer["case_id"], answer["utterance"]
            try:
                payload = v1_runner.call_candidate_once(utterance, key, model, prompt, schema)
                record, private = v1_runner.inspect_candidate_response(payload, case_id, utterance, model, schema)
            except OpenRouterFailure as error:
                record = v1_runner._base_record(case_id, utterance, error.model or model)
                record["usage"] = error.usage
                v1_runner._fail(record, error.category, "api")
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
            print(f"compact_dev_v2_case={case_id} status={'valid' if record['intent'] is not None else record['failure_group']}", flush=True)
            if consecutive >= 3:
                stopped_early = True
                print("compact_dev_v2=stopped category=three_consecutive_api_or_structure_failures", flush=True)
                break
    answer_by_id = {row["case_id"]: row for row in answers}
    unsupported_by_id = {row["case_id"]: row for row in unsupported}
    scores = score_records(records,
                           [answer_by_id[record["case_id"]] for record in records],
                           [unsupported_by_id[record["case_id"]] for record in records])
    scores.pop("failures")  # Raw model text remains in the ignored private file.
    if len(records) == 12 and scores["keyword_baseline"] != v1["scores"]["keyword_baseline"]:
        raise ValueError("keyword_baseline_changed")
    token_names = ("prompt_tokens", "completion_tokens", "total_tokens", "reasoning_tokens")
    tokens = {name: sum(record["usage"].get(name, 0) for record in records) for name in token_names}
    costs = [estimate_standard_cost_usd(record["model"], record["usage"]) for record in records]
    result = {"synthetic_dev": True, "version": VERSION, **digests,
              "started_at": started_at, "model": model, "expected_cases": 12,
              "attempted_calls": len(records), "stopped_early": stopped_early,
              "pre_run_estimate": planning,
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
              "case_summaries": [v1_runner.safe_case_summary(record, answer_by_id[record["case_id"]],
                                                                unsupported_by_id[record["case_id"]]) for record in records]}
    result["valid_answer_mismatch_cases"] = v1_runner.valid_answer_mismatch_count(result["case_summaries"])
    with PUBLIC_JSON.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    with PUBLIC_MD.open("x", encoding="utf-8") as handle:
        handle.write(render_report(result, original, v1))
    print(f"compact_dev_v2=complete attempted={len(records)} valid={scores['valid_responses']}", flush=True)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="One prompt-only compact development comparison")
    parser.add_argument("--allow-paid-dev", action="store_true")
    args = parser.parse_args(argv)
    if not args.allow_paid_dev:
        print("compact_dev_v2=not_run category=authorization_required")
        return 2
    try:
        run()
    except Exception:
        # No raw model response, user utterance, request header, or credential in a traceback.
        print("compact_dev_v2=failed category=preflight_or_local_error")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
