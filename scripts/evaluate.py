"""Author-gated formal run using the frozen compact-dev-v2 request and v3 scoring."""

from __future__ import annotations

import argparse
import csv
import hashlib
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

import evaluate_compact_dev as candidate_runner  # noqa: E402
from compact_dev_v2_request import VERSION as CANDIDATE_VERSION, load_v2_format  # noqa: E402
from freeze_test_set import MANIFEST, verify_manifest  # noqa: E402
from music_intent.config import get_settings  # noqa: E402
from music_intent.intent import CORE_FIELDS  # noqa: E402
from music_intent.openrouter_client import OpenRouterFailure  # noqa: E402
from music_intent.pricing import estimate_standard_cost_usd  # noqa: E402
from music_intent.scoring_v3 import SCORE_VERSION, score_detailed  # noqa: E402
from review_test_answers import validate_all  # noqa: E402

MODEL = "google/gemini-3.5-flash-lite"
REPORTS = ROOT / "reports"
STARTED = REPORTS / "evaluation.started.json"
TRACE = REPORTS / "evaluation_trace.jsonl"
RESULT = REPORTS / "evaluation.json"
MARKDOWN = REPORTS / "evaluation.md"
PRIVATE_DIR = REPORTS / "private_formal_predictions"
PRIVATE_FILE = PRIVATE_DIR / "compact_v2_formal_predictions.jsonl"
SECOND_REPORTS = REPORTS / "formal_run_02"
SECOND_PRIVATE_FILE = PRIVATE_DIR / "compact_v2_formal_run_02_predictions.jsonl"
EXPECTED_IDS = {f"test_{n:03d}" for n in range(1, 31)}
EXPECTED_PROMPT_SHA256 = "1177a979ad7a42aa2a3d02c04563eed950c4ef74d9f081aa44bb1044742e3eb2"
EXPECTED_SCHEMA_SHA256 = "c2d9e08fabefa74124fe3c22f9c74a991731a0bf67f42ca29e4ced9d2a44c344"
CODE_FILES = (
    "data/COMPACT_DEV_PROMPT_v2.txt", "data/COMPACT_DEV_SCHEMA_v1.json",
    "prototypes/compact_dev_request.py", "prototypes/compact_dev_v2_request.py",
    "prototypes/compact_intent_format.py", "scripts/evaluate_compact_dev.py",
    "scripts/evaluate.py", "src/music_intent/intent.py",
    "src/music_intent/evaluation.py", "src/music_intent/scoring_v3.py",
    "src/music_intent/pricing.py",
)


def code_hashes() -> dict[str, str]:
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in CODE_FILES}


def verify_candidate_format(digests: dict[str, str]) -> None:
    if (digests.get("prompt_sha256") != EXPECTED_PROMPT_SHA256
            or digests.get("schema_sha256") != EXPECTED_SCHEMA_SHA256):
        raise ValueError("compact_dev_v2_format_changed")


def verify_previous_run() -> dict[str, Any]:
    """Pin the archived failed run before a separate second run starts."""
    old_files = (STARTED, TRACE, RESULT, MARKDOWN, PRIVATE_FILE)
    if not all(path.is_file() for path in old_files):
        raise ValueError("previous_formal_run_missing")
    previous = json.loads(RESULT.read_text(encoding="utf-8"))
    scores = previous.get("scores", {})
    if (scores.get("attempted_calls") != 3 or scores.get("valid_responses") != 0
            or scores.get("total_cases") != 30 or previous.get("stopped_early") is not True
            or previous.get("error_categories") != {"network": 3}):
        raise ValueError("previous_formal_run_unexpected")
    return {"attempted_calls": 3, "valid_responses": 0,
            "stop_category": "three_consecutive_network_failures",
            "files_sha256": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                             for path in old_files}}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def cost(usage: dict[str, int], model: str) -> float | None:
    """Keep the original pricing helper's public behavior for offline checks."""
    return estimate_standard_cost_usd(model, usage)


def _cell(correct: int, denominator: int) -> str:
    return f"{correct}/{denominator}" if denominator else "Unevaluated (denominator 0)"


def render_report(result: dict[str, Any]) -> str:
    scores = result["scores"]
    n, valid = scores["total_cases"], scores["valid_responses"]
    stage = scores["stages"]
    lines = ["# PE6201 V2 Official Synthesis Test Evaluation", "",
             f"Run ID: **{result.get('run_label', 'First official run after freeze')}**.",
             ("First run only tried 3/30 items, stopped due to three consecutive `network` failures, valid results 0;"
              "This report only counts the second run and does not merge the two invocations."
              if result.get("run_label") == "second official run after freezing" else
              "This report only counts this run."), "",
             "This report can only be generated after the author verifies the answers, freezes the test set, and authorizes the official invocation. The evaluated examples are not real user data; this test does not measure recommendation quality for the 35-track catalog.",
             "", f"Candidate: `{result['candidate_version']}`; Model: `{result['model']}`; Score: `{scores['score_version']}`.",
             f"Prompt SHA-256: `{result['prompt_sha256']}`; Schema SHA-256: `{result['schema_sha256']}`; Singapore runtime: `{result['started_at']}`.",
             f"Frozen record: `data/{MANIFEST.name}`.",
             "", "## Call and Validation Phase", "",
             f"Actual calls {scores['attempted_calls']}/{n}; API returned processable responses {stage['api_success']}/{n}; Complete JSON {stage['json_complete']}/{n}; Required structure complete {stage['required_structure_complete']}/{n}; Shorthand conversion complete {stage['conversion_complete']}/{n}; V2 local validation passed {stage['local_valid']}/{n}.",
             f"No valid intent card: {scores['failed_calls']}/{n}; stopped early: {'Yes' if result['stopped_early'] else 'No'}. Passing a stage means only that the data can be processed, not that the intent judgment is correct.",
             "", "## Six Core Fields: Primary Metrics", "",
             "End-to-end denominator includes invalid calls; valid-only output denominator contains only intent cards that passed conversion and local validation. The keyword baseline directly outputs the six fields for the same batch of raw utterances, with no API, JSON, or structural pass rate.",
             "", "| Field | AI End-to-End | AI Valid-Only | Keyword Baseline |",
             "| --- | ---: | ---: | ---: |"]
    for field in CORE_FIELDS:
        item = scores["fields"][field]
        lines.append(f"| `{field}` | {_cell(item['end_to_end']['correct'], n)} | "
                     f"{_cell(item['valid_only']['correct'], valid)} | "
                     f"{_cell(item['baseline']['correct'], n)} |")
    lines.extend(["", "## Classified by Whether Approval Answer Clearly Expresses", "",
                  "Approved nonnull answers for the five nullable fields form the explicit subset, including range objects. For `trajectory`, only `from_to` explicitly requests a **song order**; `single_target` and `none` do not. Correctness requires an exact match to the approved answer.",
                  "", "| Field | Explicit Subset Utterances | AI End-to-End | AI Valid Only | Keyword Baseline |",
                  "| --- | ---: | ---: | ---: | ---: |"])
    for field in CORE_FIELDS:
        item = scores["fields"][field]["explicit"]
        lines.append(f"| `{field}` | {item['gold_cases']} | "
                     f"{_cell(item['ai_end_to_end_correct'], item['gold_cases'])} | "
                     f"{_cell(item['ai_valid_correct'], item['valid_cases'])} | "
                     f"{_cell(item['baseline_correct'], item['gold_cases'])} |")
    lines.extend(["", "Unspecified subset: the five nullable fields have an approved value of `null`; trajectory means **no explicit song order** (including `single_target` and `none`). False fills are calculated only among valid AI cards; failed calls are separately counted as incomplete. For trajectory, a false fill means an unwarranted `from_to`; confusion between `single_target` and `none` is reported separately.",
                  "", "| Field | Unspecified subset sentence count | AI end-to-end precision | AI valid-only precision | AI valid misfilled | Invalid unfinished | Keyword baseline precision | Baseline misfilled |",
                  "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"])
    for field in CORE_FIELDS:
        item = scores["fields"][field]["unspoken"]
        lines.append(f"| `{field}` | {item['gold_cases']} | "
                     f"{_cell(item['ai_end_to_end_exact'], item['gold_cases'])} | "
                     f"{_cell(item['ai_valid_exact'], item['valid_cases'])} | "
                     f"{_cell(item['ai_false_fills'], item['valid_cases'])} | "
                     f"{item['invalid_or_missing_cases']} | "
                     f"{_cell(item['baseline_exact'], item['gold_cases'])} | "
                     f"{_cell(item['baseline_false_fills'], item['gold_cases'])} |")
    no_order = scores["fields"]["trajectory"]["unspoken"]
    lines.append(f"Unordered classification errors: AI {no_order['ai_no_order_classification_errors']}/{no_order['valid_cases']} valid cards; keyword baseline {no_order['baseline_no_order_classification_errors']}/{no_order['gold_cases']}.")
    card = scores["core_cards"]
    melody = scores["requires_melody_present"]
    lines.extend(["", "## Strict Supplementary Indicators and Unsupported Conditions", "",
                  f"Six-field full card all correct: AI end-to-end {_cell(card['end_to_end_correct'], n)}; valid only {_cell(card['valid_correct'], valid)}; keyword baseline {_cell(card['baseline_correct'], n)}. Full card is a strict supplementary metric and does not independently represent comprehension ability.",
                  f"`requires_melody_present`: AI end-to-end {_cell(melody['end_to_end_correct'], n)}; valid only {_cell(melody['valid_correct'], valid)}.",
                  "", "| Unsupported conditional metric | AI end-to-end | AI effective only |",
                  "| --- | ---: | ---: |"])
    condition = scores["unsupported"]
    lines.append(f"| Correctly identified existence of an unsupported condition | {_cell(condition['status_end_to_end_correct'], n)} | "
                 f"{_cell(condition['status_valid_correct'], valid)} |")
    lines.append(f"| Exact set of extracted source phrases | {_cell(condition['exact_set_end_to_end_correct'], n)} | "
                 f"{_cell(condition['exact_set_valid_correct'], valid)} |")
    if valid:
        lines.append(f"Original terms of valid cards only: exact hits {condition['valid_true_positive_phrases']}, false positives {condition['valid_false_positive_phrases']}, misses {condition['valid_missed_phrases']}.")
    else:
        lines.append("No valid cards; original term hit/false positive/false negative not evaluated.")
    lines.append(f"End-to-end expected original terms: {condition['expected_phrase_total']}, unfulfilled: {condition['unfulfilled_phrases_end_to_end']}; of which {condition['unfulfilled_phrases_due_to_invalid']} are from invalid calls and are not counted as model original term omissions.")
    token = result["tokens"]
    lines.extend(["", "## Usage, Failures, and Limits", "",
                  f"Input/Completion/Total tokens: {token['prompt_tokens']}/{token['completion_tokens']}/{token['total_tokens']}; Reasoning tokens available: {token['reasoning_tokens']} (missing details {result['reasoning_unavailable_calls']} times).",
                  f"Estimated at standard rate USD {result['estimated_cost_usd']:.6f}; missing data for estimation {result['cost_unavailable_calls']} calls. Actual bill subject to service provider.",
                  f"Failure groups in actual invocation: {json.dumps(result['failure_groups'], ensure_ascii=False, sort_keys=True)}; Safety error categories: {json.dumps(result['error_categories'], ensure_ascii=False, sort_keys=True)}.", ""])
    for item in scores["case_summaries"]:
        if not item["valid"]:
            lines.append(f"- `{item['case_id']}`: No valid card / `{item['error_category']}`")
        elif item["wrong_core_fields"] or item["unsupported_exact_set_wrong"]:
            wrong = ", ".join(item["wrong_core_fields"]) or "None"
            lines.append(f"- `{item['case_id']}`: Valid; Wrong core fields: {wrong}; Unsupported condition status error: {item['unsupported_status_wrong']}; Original term set error: {item['unsupported_exact_set_wrong']}.")
    lines.extend(["", "Keyword baseline does not require JSON; structural pass rate is not comprehension accuracy. Full model predictions exist only in the local Git-ignored directory; public reports contain no API keys, request headers, or full responses. After freezing, approved answer lineage must not be stealthily altered to maintain these scores.", ""])
    return "\n".join(lines)


def run(*, output_dir: Path | None = None,
        private_path: Path | None = None,
        run_label: str = "First official run after freezing") -> dict[str, Any]:
    run_reports = output_dir or REPORTS
    run_started = (run_reports / STARTED.name) if output_dir else STARTED
    run_trace = (run_reports / TRACE.name) if output_dir else TRACE
    run_result = (run_reports / RESULT.name) if output_dir else RESULT
    run_markdown = (run_reports / MARKDOWN.name) if output_dir else MARKDOWN
    run_private_file = private_path or PRIVATE_FILE
    run_private_dir = run_private_file.parent
    previous_run = verify_previous_run() if run_label == "second official run after freezing" else None
    verify_manifest()
    validate_all(approved=True)
    key, model = get_settings()
    if model != MODEL:
        raise ValueError("formal_model_mismatch")
    prompt, schema, digests = load_v2_format()
    verify_candidate_format(digests)
    answers = read_csv(ROOT / "data" / "synthetic_intents_test.csv")
    unsupported = read_csv(ROOT / "data" / "unsupported_conditions_test.csv")
    if (len(answers) != 30 or {row["case_id"] for row in answers} != EXPECTED_IDS
            or len(unsupported) != 30 or {row["case_id"] for row in unsupported} != EXPECTED_IDS
            or any(row["review_status"] != "approved" for row in answers + unsupported)):
        raise ValueError("formal_test_count_ids_or_approval")
    if any(path.exists() for path in (run_started, run_trace, run_result, run_markdown)):
        raise ValueError("formal_run_already_started")
    candidate_runner.verify_private_path(run_private_file)
    run_reports.mkdir(parents=True, exist_ok=True)
    run_private_dir.mkdir(mode=0o700, exist_ok=True)
    os.chmod(run_private_dir, 0o700)
    started = datetime.now(ZoneInfo("Asia/Singapore")).isoformat(timespec="seconds")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    with run_started.open("x", encoding="utf-8") as handle:
        json.dump({"started_at": started, "model": model, "candidate_version": CANDIDATE_VERSION,
                   "run_label": run_label,
                   "score_version": SCORE_VERSION, "prompt_sha256": digests["prompt_sha256"],
                   "schema_sha256": digests["schema_sha256"], "freeze_files": manifest["files"]},
                  handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    descriptor = os.open(run_private_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    records: list[dict[str, Any]] = []
    consecutive = 0
    stopped_early = False
    with os.fdopen(descriptor, "w", encoding="utf-8") as private_file, run_trace.open("x", encoding="utf-8") as trace:
        for index, row in enumerate(answers):
            case_id, utterance = row["case_id"], row["utterance"]
            try:
                payload = candidate_runner.call_candidate_once(utterance, key, model, prompt, schema)
                record, private = candidate_runner.inspect_candidate_response(payload, case_id, utterance, model, schema)
                api_success = True
            except OpenRouterFailure as error:
                record = candidate_runner._base_record(case_id, utterance, error.model or model)
                record["usage"] = error.usage
                record["http_status"] = error.http_status
                record["transport_phase"] = error.transport_phase
                candidate_runner._fail(record, error.category, "api")
                private = {"case_id": case_id, "raw_prediction": None, "converted_v2": None}
                api_success = False
            if record["model"] != MODEL:
                record["intent"] = None
                record["error_category"] = "response_model_mismatch"
                record["error_field"] = None
                record["failure_group"] = "api"
                record["failure_stage"] = "api"
            record["api_success"] = api_success
            record["attempted"] = True
            records.append(record)
            private.update({"model": record["model"], "finish_reason": record["finish_reason"],
                            "usage": record["usage"], "intent_valid": record["intent"] is not None,
                            "error_category": record["error_category"],
                            "error_field": record["error_field"]})
            private_file.write(json.dumps(private, ensure_ascii=False) + "\n")
            private_file.flush()
            safe = {name: record.get(name) for name in (
                "case_id", "model", "usage", "api_success", "finish_reason", "json_complete",
                "required_structure_complete", "conversion_complete", "error_category",
                "error_field", "failure_group", "http_status", "transport_phase")}
            safe["local_valid"] = record["intent"] is not None
            trace.write(json.dumps(safe, ensure_ascii=False) + "\n")
            trace.flush()
            print(f"formal_case={case_id} status={'valid' if safe['local_valid'] else record['failure_group']}", flush=True)
            consecutive = (consecutive + 1 if record["intent"] is None and
                           record["failure_group"] in {"api", "structure"} else 0)
            if consecutive >= 3:
                stopped_early = True
                print("formal_evaluation=stopped category=three_consecutive_api_or_structure_failures", flush=True)
                for remaining in answers[index + 1:]:
                    skipped = candidate_runner._base_record(remaining["case_id"], remaining["utterance"], model)
                    skipped.update({"attempted": False, "api_success": False,
                                    "error_category": "not_attempted_after_stop",
                                    "failure_group": "not_attempted", "failure_stage": "not_attempted"})
                    records.append(skipped)
                break
    scores = score_detailed(records, answers, unsupported)
    attempted_records = [record for record in records if record["attempted"]]
    tokens = {name: sum(record["usage"].get(name, 0) for record in records)
              for name in ("prompt_tokens", "completion_tokens", "total_tokens", "reasoning_tokens")}
    costs = [estimate_standard_cost_usd(record["model"], record["usage"]) for record in attempted_records]
    result = {"synthetic": True, "started_at": started, "model": model,
              "run_label": run_label,
              "previous_run": previous_run,
              "candidate_version": CANDIDATE_VERSION, "score_version": SCORE_VERSION,
              "prompt_sha256": digests["prompt_sha256"], "schema_sha256": digests["schema_sha256"],
              "freeze_files": manifest["files"], "code_sha256": code_hashes(),
              "scores": scores, "tokens": tokens, "stopped_early": stopped_early,
              "failure_groups": dict(Counter(record["failure_group"] for record in attempted_records
                                             if record["intent"] is None)),
              "error_categories": dict(Counter(record["error_category"] for record in attempted_records
                                               if record["intent"] is None)),
              "reasoning_unavailable_calls": sum("reasoning_tokens" not in record["usage"] for record in attempted_records),
              "cost_unavailable_calls": sum(cost is None for cost in costs),
              "estimated_cost_usd": round(sum(cost for cost in costs if cost is not None), 8)}
    with run_result.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    with run_markdown.open("x", encoding="utf-8") as handle:
        handle.write(render_report(result))
    print(f"formal_evaluation=complete attempted={scores['attempted_calls']} expected={len(answers)} report={run_markdown}", flush=True)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="One author-approved compact-v2 formal evaluation")
    parser.add_argument("--allow-paid-formal", action="store_true")
    parser.add_argument("--run-id", choices=("first", "second"), default="first")
    args = parser.parse_args(argv)
    if not args.allow_paid_formal:
        print("formal_evaluation=not_run category=authorization_required")
        return 2
    try:
        if args.run_id == "second":
            run(output_dir=SECOND_REPORTS, private_path=SECOND_PRIVATE_FILE,
                run_label="second official run after freezing")
        else:
            run()
    except Exception:
        print("formal_evaluation=failed category=gate_or_local_error")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
