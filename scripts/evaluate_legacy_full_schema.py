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
        return f"{correct}/{valid_n}" if valid_n else "未评估（有效响应 0 条）"
    lines = ["# PE6201 V2 正式合成测试评估", "",
             "这些是 30 条合成表达，不是真人受访数据。没有把测试答案写入运行时提示词。",
             "", f"模型：`{result['model']}`", f"冻结记录：`data/{MANIFEST.name}`",
             f"运行时间（新加坡）：`{result['started_at']}`", "",
             f"调用总数 {scores['attempted_calls']}；有效响应 {scores['valid_responses']}；失败调用 {scores['failed_calls']}。",
             "端到端分母包含失败调用；仅有效响应分母只包含通过结构与证据校验的意图卡。失败调用不会算作模型的原词误报或漏报。",
             "", "| 指标 | 端到端正确／总数 | 仅有效响应正确／总数 |",
             "| --- | ---: | ---: |"]
    for field in end_to_end["core_fields"]:
        correct = end_to_end["core_fields"][field]
        lines.append(f"| {field} | {correct}/{n} | {valid_cell(valid_only['core_fields'][field])} |")
    for label, key in (("六字段整卡", "core_cards"),
                       ("requires_melody_present", "requires_melody_present"),
                       ("不支持条件原词集合全对", "unsupported_exact_sets"),
                       ("cannot_guarantee_constraint 状态", "cannot_guarantee_constraint_status")):
        lines.append(f"| {label} | {end_to_end[key]}/{n} | {valid_cell(valid_only[key])} |")
    lines.extend(["", "## 关键词基线（全部合成测试句）", "",
                  f"六字段整卡：{baseline['core_cards']}/{baseline['denominator']}。"])
    for field, correct in baseline["core_fields"].items():
        lines.append(f"- `{field}`：{correct}/{baseline['denominator']}")
    lines.extend(["", "## 不支持条件原词", "",
                  f"端到端：预期原词共 {end_to_end['unsupported_expected_phrases']} 个，未完成 {end_to_end['unsupported_unfulfilled_phrases']} 个；其中 {end_to_end['unsupported_unfulfilled_due_to_call_failure']} 个来自调用失败。",
                  (f"仅有效响应（{valid_n} 条，预期原词 {valid_only['unsupported_expected_phrases']} 个）：精确命中 {valid_only['unsupported_true_positive_phrases']}；误报 {valid_only['unsupported_false_positive_phrases']}；漏报 {valid_only['unsupported_missed_phrases']}。"
                   if valid_n else "仅有效响应：没有有效意图卡，模型原词识别指标未评估。"),
                  "", "## 用量与费用", "",
                  f"输入 token：{result['tokens']['prompt_tokens']}；输出 token：{result['tokens']['completion_tokens']}；总 token：{result['tokens']['total_tokens']}。",
                  f"按标准标价估算费用：{result['estimated_cost_usd']} USD；实际账单以 OpenRouter 为准。",
                  f"用量或模型费率缺失的调用：{result['usage_unavailable_calls']}；若非零，上述费用只是可取得记录的部分估算。",
                  "", "## 失败案例", ""])
    if not scores["failures"]:
        lines.append("无。")
    else:
        for item in scores["failures"]:
            lines.append(f"- `{item['case_id']}`：{json.dumps({k: v for k, v in item.items() if k != 'case_id'}, ensure_ascii=False)}")
    lines.extend(["", "本报告只衡量合成找歌意图解析；正式 35 首曲库尚未接入，未声称验证真实曲库推荐效果。", ""])
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
