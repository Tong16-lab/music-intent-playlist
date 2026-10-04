"""Historical full-Schema evaluator, retained for review and disabled for execution."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from music_intent.config import get_settings  # noqa: E402
from music_intent.evaluation import score_records  # noqa: E402
from music_intent.openrouter_client import OpenRouterFailure, parse_once  # noqa: E402
from music_intent.pricing import estimate_standard_cost_usd  # noqa: E402
from freeze_test_set import MANIFEST, verify_manifest  # noqa: E402
from connection_test import PREFLIGHT, code_hashes  # noqa: E402
from review_test_answers import validate_all  # noqa: E402

REPORTS = ROOT / "reports"
STARTED = REPORTS / "evaluation.started.json"
TRACE = REPORTS / "evaluation_trace.jsonl"
RESULT = REPORTS / "evaluation.json"
MARKDOWN = REPORTS / "evaluation.md"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def cost(usage: dict[str, int], model: str) -> float | None:
    return estimate_standard_cost_usd(model, usage)


def render_report(result: dict) -> str:
    scores = result["scores"]
    end_to_end = scores["end_to_end"]
    valid_only = scores["valid_only"]
    baseline = scores["keyword_baseline"]
    n = end_to_end["denominator"]
    valid_n = valid_only["denominator"]
    def valid_cell(correct: int) -> str:
        return f"{correct}/{valid_n}" if valid_n else "Not evaluated (0 valid responses)"
    lines = ["# PE6201 V2 Official Synthesis Test Evaluation", "",
             "These are 30 synthetic expressions, not real-person interview data. Test answers were not written into the runtime prompt.",
             "", f"Model: `{result['model']}`", f"Frozen records: `data/{MANIFEST.name}`",
             f"Run Time (Singapore): `{result['started_at']}`", "",
             f"Total calls {scores['attempted_calls']}; valid responses {scores['valid_responses']}; failed calls {scores['failed_calls']}.",
             "The end-to-end denominator includes failed calls; the valid-response-only denominator only includes intent cards that pass structure and evidence validation. Failed calls will not be counted as false positives or false negatives of the model's verbatim words.",
             "", "| Metric | End-to-End Correct / Total | Valid Response Only Correct / Total |",
             "| --- | ---: | ---: |"]
    for field in end_to_end["core_fields"]:
        correct = end_to_end["core_fields"][field]
        lines.append(f"| {field} | {correct}/{n} | {valid_cell(valid_only['core_fields'][field])} |")
    for label, key in (("Six-field full card", "core_cards"),
                       ("requires_melody_present", "requires_melody_present"),
                       ("unsupported exact sets", "unsupported_exact_sets"),
                       ("cannot_guarantee_constraint status", "cannot_guarantee_constraint_status")):
        lines.append(f"| {label} | {end_to_end[key]}/{n} | {valid_cell(valid_only[key])} |")
    lines.extend(["", "## Keyword Baseline (all test examples)", "",
                  f"Six-field full cards: {baseline['core_cards']}/{baseline['denominator']}."])
    for field, correct in baseline["core_fields"].items():
        lines.append(f"- `{field}`:{correct}/{baseline['denominator']}")
    lines.extend(["", "## Unsupported Condition Original Words", "",
                  f"End-to-end: Expected original phrases: {end_to_end['unsupported_expected_phrases']}, unfulfilled: {end_to_end['unsupported_unfulfilled_phrases']}; of which {end_to_end['unsupported_unfulfilled_due_to_call_failure']} are due to call failures.",
                  (f"Only valid responses ({valid_n}, expected original phrases {valid_only['unsupported_expected_phrases']}): exact hits {valid_only['unsupported_true_positive_phrases']}; false positives {valid_only['unsupported_false_positive_phrases']}; missed {valid_only['unsupported_missed_phrases']}."
                   if valid_n else "Valid response only: No valid intent card, model verbatim recognition metrics not evaluated."),
                  "", "## Usage & Fees", "",
                  f"Input tokens: {result['tokens']['prompt_tokens']}; Output tokens: {result['tokens']['completion_tokens']}; Total tokens: {result['tokens']['total_tokens']}.",
                  f"Estimated cost based on standard pricing: {result['estimated_cost_usd']} USD; actual billing is subject to OpenRouter.",
                  f"Calls missing usage or model rates: {result['usage_unavailable_calls']}; if non-zero, the above costs are only partial estimates based on available records.",
                  "", "## Failure Cases", ""])
    if not scores["failures"]:
        lines.append("None.")
    else:
        for item in scores["failures"]:
            lines.append(f"- `{item['case_id']}`:{json.dumps({k: v for k, v in item.items() if k != 'case_id'}, ensure_ascii=False)}")
    lines.extend(["", "This report only measures synthetic song-finding intent parsing; the official 35-song music library has not yet been integrated, and no claim is made to have verified the actual music library recommendation effectiveness.", ""])
    return "\n".join(lines)


def run() -> None:
    raise ValueError("historical_full_schema_evaluator_disabled_use_evaluate_py")
    verify_manifest()
    validate_all(approved=True)
    key, model = get_settings()
    try:
        preflight = json.loads(PREFLIGHT.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        raise ValueError("successful_connection_preflight_required") from None
    if preflight.get("model") != model or preflight.get("code_sha256") != code_hashes():
        raise ValueError("connection_preflight_stale")
    answers = read_csv(ROOT / "data" / "synthetic_intents_test.csv")
    unsupported = read_csv(ROOT / "data" / "unsupported_conditions_test.csv")
    if len(answers) != 30 or len(unsupported) != 30:
        raise ValueError("wrong_test_count")
    REPORTS.mkdir(exist_ok=True)
    if any(path.exists() for path in (STARTED, TRACE, RESULT, MARKDOWN)):
        raise ValueError("formal_run_already_started")
    started = datetime.now(ZoneInfo("Asia/Singapore")).isoformat(timespec="seconds")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    with STARTED.open("x", encoding="utf-8") as handle:
        json.dump({"started_at": started, "model": model, "freeze_files": manifest["files"]}, handle, ensure_ascii=False, indent=2)
    records = []
    with TRACE.open("x", encoding="utf-8") as trace:
        for row in answers:
            record = {"case_id": row["case_id"], "utterance": row["utterance"], "model": model}
            try:
                intent, info = parse_once(row["utterance"], key, model)
                record.update({"intent": intent, "model": info["model"], "usage": info["usage"]})
            except OpenRouterFailure as error:
                record.update({"intent": None, "error_category": str(error),
                               "model": error.model or model, "usage": error.usage})
            records.append(record)
            trace.write(json.dumps(record, ensure_ascii=False) + "\n")
            trace.flush()
    tokens = {name: sum(record["usage"].get(name, 0) for record in records)
              for name in ("prompt_tokens", "completion_tokens", "total_tokens")}
    known_costs = [cost(record["usage"], record["model"]) for record in records]
    result = {"synthetic": True, "started_at": started, "model": model,
              "freeze_files": manifest["files"],
              "code_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                              for name in ("src/music_intent/intent.py", "src/music_intent/openrouter_client.py",
                                           "src/music_intent/pricing.py", "src/music_intent/evaluation.py",
                                           "scripts/evaluate.py")},
              "scores": score_records(records, answers, unsupported), "tokens": tokens,
              "estimated_cost_usd": round(sum(x for x in known_costs if x is not None), 8),
              "usage_unavailable_calls": sum(x is None for x in known_costs)}
    with RESULT.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
    MARKDOWN.write_text(render_report(result), encoding="utf-8")
    print(f"formal_evaluation=complete cases={len(records)} report={MARKDOWN}")


if __name__ == "__main__":
    try:
        run()
    except (ValueError, FileNotFoundError, OSError, json.JSONDecodeError) as error:
        raise SystemExit(f"formal_evaluation=failed category={error}") from None
