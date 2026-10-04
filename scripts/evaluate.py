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
    return f"{correct}/{denominator}" if denominator else "未评估（分母 0）"


def render_report(result: dict[str, Any]) -> str:
    scores = result["scores"]
    n, valid = scores["total_cases"], scores["valid_responses"]
    stage = scores["stages"]
    lines = ["# PE6201 V2 正式合成测试评估", "",
             f"运行标识：**{result.get('run_label', '冻结后第一次正式运行')}**。",
             ("第一次运行仅尝试 3/30 条，因连续三次 `network` 失败停止，有效结果 0；"
              "本报告只统计第二次运行，不合并两次调用。"
              if result.get("run_label") == "冻结后第二次正式运行" else
              "本报告只统计本次运行。"), "",
             "此报告只有在作者核对答案、冻结测试集并授权正式调用后才可生成。评估对象是合成表达，不是真人用户数据；不衡量尚未接入的正式歌曲曲库推荐效果。",
             "", f"候选：`{result['candidate_version']}`；模型：`{result['model']}`；评分：`{scores['score_version']}`。",
             f"提示词 SHA-256：`{result['prompt_sha256']}`；Schema SHA-256：`{result['schema_sha256']}`；新加坡运行时间：`{result['started_at']}`。",
             f"冻结记录：`data/{MANIFEST.name}`。",
             "", "## 调用与校验阶段", "",
             f"实际调用 {scores['attempted_calls']}/{n}；API 返回可处理响应 {stage['api_success']}/{n}；完整 JSON {stage['json_complete']}/{n}；必填结构完整 {stage['required_structure_complete']}/{n}；简写转换完成 {stage['conversion_complete']}/{n}；V2 本地校验通过 {stage['local_valid']}/{n}。",
             f"无有效意图卡 {scores['failed_calls']}/{n}；提前停止：{'是' if result['stopped_early'] else '否'}。阶段通过只说明数据可处理，不代表意图判断正确。",
             "", "## 六个核心字段：主指标", "",
             "端到端分母包含无效调用；仅有效输出分母只包含通过转换及本地校验的意图卡。关键词基线对同一批原话直接输出六字段，没有 API、JSON 或结构通过率。",
             "", "| 字段 | AI 端到端 | AI 仅有效 | 关键词基线 |",
             "| --- | ---: | ---: | ---: |"]
    for field in CORE_FIELDS:
        item = scores["fields"][field]
        lines.append(f"| `{field}` | {_cell(item['end_to_end']['correct'], n)} | "
                     f"{_cell(item['valid_only']['correct'], valid)} | "
                     f"{_cell(item['baseline']['correct'], n)} |")
    lines.extend(["", "## 按批准答案是否明确表达划分", "",
                  "五个可空字段的非空批准答案属于明确表达子集，范围对象也算非空。`trajectory` 只有批准答案为 `from_to` 才算明确要求**歌曲顺序**；`single_target` 与 `none` 均属于未明确要求顺序。所有正确数都要求预测值与批准答案完全相等。",
                  "", "| 字段 | 明确子集句数 | AI 端到端 | AI 仅有效 | 关键词基线 |",
                  "| --- | ---: | ---: | ---: | ---: |"])
    for field in CORE_FIELDS:
        item = scores["fields"][field]["explicit"]
        lines.append(f"| `{field}` | {item['gold_cases']} | "
                     f"{_cell(item['ai_end_to_end_correct'], item['gold_cases'])} | "
                     f"{_cell(item['ai_valid_correct'], item['valid_cases'])} | "
                     f"{_cell(item['baseline_correct'], item['gold_cases'])} |")
    lines.extend(["", "未说明子集：五个可空字段的批准答案为 `null`；轨迹则指**未明确要求歌曲顺序**（包括 `single_target`、`none`）。AI 误填只在有效卡片内计算；失败调用另列未完成。轨迹的误填专指擅自输出 `from_to`，把 `single_target` 与 `none` 混淆另列。",
                  "", "| 字段 | 未说明子集句数 | AI 端到端精确 | AI 仅有效精确 | AI 有效误填 | 无效未完成 | 关键词基线精确 | 基线误填 |",
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
    lines.append(f"无顺序分类错误：AI {no_order['ai_no_order_classification_errors']}/{no_order['valid_cases']} 条有效卡片；关键词基线 {no_order['baseline_no_order_classification_errors']}/{no_order['gold_cases']}。")
    card = scores["core_cards"]
    melody = scores["requires_melody_present"]
    lines.extend(["", "## 严格补充指标与不支持条件", "",
                  f"六字段整卡全对：AI 端到端 {_cell(card['end_to_end_correct'], n)}；仅有效 {_cell(card['valid_correct'], valid)}；关键词基线 {_cell(card['baseline_correct'], n)}。整卡是严格补充指标，不单独代表理解能力。",
                  f"`requires_melody_present`：AI 端到端 {_cell(melody['end_to_end_correct'], n)}；仅有效 {_cell(melody['valid_correct'], valid)}。",
                  "", "| 不支持条件指标 | AI 端到端 | AI 仅有效 |",
                  "| --- | ---: | ---: |"])
    condition = scores["unsupported"]
    lines.append(f"| 是否正确判断存在无法保证条件 | {_cell(condition['status_end_to_end_correct'], n)} | "
                 f"{_cell(condition['status_valid_correct'], valid)} |")
    lines.append(f"| 截取原词集合完全一致 | {_cell(condition['exact_set_end_to_end_correct'], n)} | "
                 f"{_cell(condition['exact_set_valid_correct'], valid)} |")
    if valid:
        lines.append(f"仅有效卡片的原词：精确命中 {condition['valid_true_positive_phrases']}、误报 {condition['valid_false_positive_phrases']}、漏报 {condition['valid_missed_phrases']}。")
    else:
        lines.append("没有有效卡片，原词命中／误报／漏报未评估。")
    lines.append(f"端到端预期原词 {condition['expected_phrase_total']} 个、未完成 {condition['unfulfilled_phrases_end_to_end']} 个；其中 {condition['unfulfilled_phrases_due_to_invalid']} 个来自无效调用，不算模型原词漏报。")
    token = result["tokens"]
    lines.extend(["", "## 用量、失败和限制", "",
                  f"输入／完成／总 token：{token['prompt_tokens']}／{token['completion_tokens']}／{token['total_tokens']}；可取得推理 token：{token['reasoning_tokens']}（缺明细 {result['reasoning_unavailable_calls']} 次）。",
                  f"按标准费率估算 USD {result['estimated_cost_usd']:.6f}；缺少可估数据 {result['cost_unavailable_calls']} 次。实际账单以服务商为准。",
                  f"实际调用中的失败分组：{json.dumps(result['failure_groups'], ensure_ascii=False, sort_keys=True)}；安全错误类别：{json.dumps(result['error_categories'], ensure_ascii=False, sort_keys=True)}。", ""])
    for item in scores["case_summaries"]:
        if not item["valid"]:
            lines.append(f"- `{item['case_id']}`：无有效卡片 / `{item['error_category']}`")
        elif item["wrong_core_fields"] or item["unsupported_exact_set_wrong"]:
            wrong = ", ".join(item["wrong_core_fields"]) or "无"
            lines.append(f"- `{item['case_id']}`：有效；错误核心字段：{wrong}；不支持条件状态错误：{item['unsupported_status_wrong']}；原词集合错误：{item['unsupported_exact_set_wrong']}。")
    lines.extend(["", "关键词基线无需 JSON；结构通过率不是理解准确率。完整模型预测仅存于本机 Git 忽略目录，公开报告不含密钥、请求头或完整回复。冻结后不得暗改批准答案沿用本成绩。", ""])
    return "\n".join(lines)


def run(*, output_dir: Path | None = None,
        private_path: Path | None = None,
        run_label: str = "冻结后第一次正式运行") -> dict[str, Any]:
    run_reports = output_dir or REPORTS
    run_started = (run_reports / STARTED.name) if output_dir else STARTED
    run_trace = (run_reports / TRACE.name) if output_dir else TRACE
    run_result = (run_reports / RESULT.name) if output_dir else RESULT
    run_markdown = (run_reports / MARKDOWN.name) if output_dir else MARKDOWN
    run_private_file = private_path or PRIVATE_FILE
    run_private_dir = run_private_file.parent
    previous_run = verify_previous_run() if run_label == "冻结后第二次正式运行" else None
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
                run_label="冻结后第二次正式运行")
        else:
            run()
    except Exception:
        print("formal_evaluation=failed category=gate_or_local_error")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
