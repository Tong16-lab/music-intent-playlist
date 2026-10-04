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
    versions = (("原版", original), ("简写 v1", v1), ("提示词 v2", result))
    lines = ["| 指标 | 原版端到端 | 简写 v1 端到端 | 提示词 v2 端到端 | 同一关键词基线 |",
             "| --- | ---: | ---: | ---: | ---: |"]
    for field in CORE_FIELDS:
        values = [f"{item['scores']['end_to_end']['core_fields'][field]}/{item['scores']['end_to_end']['denominator']}"
                  for _, item in versions]
        base = result["scores"]["keyword_baseline"]
        lines.append(f"| `{field}` | {' | '.join(values)} | {base['core_fields'][field]}/{base['denominator']} |")
    for label, key in (("六字段整卡", "core_cards"),
                       ("requires_melody_present", "requires_melody_present"),
                       ("不支持条件原词集合全对", "unsupported_exact_sets"),
                       ("cannot_guarantee_constraint 状态正确", "cannot_guarantee_constraint_status")):
        values = [f"{item['scores']['end_to_end'][key]}/{item['scores']['end_to_end']['denominator']}"
                  for _, item in versions]
        baseline = (f"{result['scores']['keyword_baseline']['core_cards']}/{result['scores']['keyword_baseline']['denominator']}"
                    if key == "core_cards" else "—")
        lines.append(f"| {label} | {' | '.join(values)} | {baseline} |")
    lines.extend(["", "仅有效输出的分母分别为原版 6、简写 v1 9、提示词 v2 " +
                  str(result["scores"]["valid_only"]["denominator"]) + "；下表只衡量通过转换及本地校验的卡片。",
                  "", "| 指标 | 原版仅有效 | 简写 v1 仅有效 | 提示词 v2 仅有效 |",
                  "| --- | ---: | ---: | ---: |"])
    for field in CORE_FIELDS:
        values = [f"{item['scores']['valid_only']['core_fields'][field]}/{item['scores']['valid_only']['denominator']}"
                  for _, item in versions]
        lines.append(f"| `{field}` | {' | '.join(values)} |")
    for label, key in (("六字段整卡", "core_cards"),
                       ("不支持条件原词集合全对", "unsupported_exact_sets"),
                       ("cannot_guarantee_constraint 状态正确", "cannot_guarantee_constraint_status")):
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
    lines = ["# compact-dev-v2：只改提示词的合成开发集比较", "",
             "本轮沿用简写 v1 的 Schema、转换器、模型、请求参数、V2 已批准答案、关键词基线和本地校验器；只增加通用意图判定说明。所有请求只发送单条合成开发原话，不发送答案。没有使用正式测试句设计规则或进行调用。",
             "", f"版本：`{VERSION}`；v2 提示词 SHA-256：`{result['prompt_sha256']}`；v1 提示词 SHA-256：`{result['v1_prompt_sha256']}`；两版共同 Schema SHA-256：`{result['schema_sha256']}`。",
             f"模型：`{result['model']}`；新加坡开始时间：`{result['started_at']}`。",
             f"预先估算费用 USD {result['pre_run_estimate']['estimated_cost_usd']:.6f}（依据 v1 实测，用新增字符每字 2 个输入 token、完成 token 增加 25% 的假设）。",
             f"实际调用 {attempted}/12；提前停止：{'是' if result['stopped_early'] else '否'}。完整 JSON {result['json_complete_calls']}/{attempted}；必填结构完整 {result['required_structure_complete_calls']}/{attempted}；简写转换完成 {result['conversion_complete_calls']}/{attempted}；V2 本地校验通过 {result['locally_valid_calls']}/{attempted}。",
             f"无有效卡片 {scores['failed_calls']} 次，其中 API 失败 {result['failure_groups'].get('api', 0)} 次；失败分组 {json.dumps(result['failure_groups'], ensure_ascii=False, sort_keys=True)}；安全错误类别 {json.dumps(result['error_categories'], ensure_ascii=False, sort_keys=True)}。",
             "", "## 三版与同一关键词基线", ""]
    if attempted != 12:
        lines.extend(["v2 提前停止，仅统计已调用的句子；其他版本覆盖 12 句，因此横向正确数不是同一分母。", ""])
    lines.extend(_metric_tables(result, original, v1))
    lines.extend(["", "端到端分母包含无有效卡片的调用；这种调用不记作模型原词误报或漏报。格式完整只表示输出可解析，不表示意图判断正确。",
                  "", "## 不支持条件：状态与原词分别计分", "",
                  f"状态正确（端到端）：原版 {original['scores']['end_to_end']['cannot_guarantee_constraint_status']}/12、简写 v1 {v1['scores']['end_to_end']['cannot_guarantee_constraint_status']}/12、v2 {end['cannot_guarantee_constraint_status']}/{attempted}。",
                  f"原词集合完全一致（端到端）：原版 {original['scores']['end_to_end']['unsupported_exact_sets']}/12、简写 v1 {v1['scores']['end_to_end']['unsupported_exact_sets']}/12、v2 {end['unsupported_exact_sets']}/{attempted}。",
                  f"v2 仅有效输出：预期原词 {valid['unsupported_expected_phrases']} 个；精确命中 {valid['unsupported_true_positive_phrases'] if valid['denominator'] else '未评估'}、误报 {valid['unsupported_false_positive_phrases'] if valid['denominator'] else '未评估'}、漏报 {valid['unsupported_missed_phrases'] if valid['denominator'] else '未评估'}（{valid['denominator']} 条有效卡片）。端到端未完成原词 {end['unsupported_unfulfilled_phrases']} 个，其中 {end['unsupported_unfulfilled_due_to_call_failure']} 个来自无有效卡片。",
                  "", "## 安全错误摘要", ""])
    for stage, count in sorted(result["failure_stages"].items()):
        lines.append(f"- `{stage}`：{count} 次")
    for case in result["case_summaries"]:
        if not case["intent_valid"]:
            lines.append(f"- `{case['case_id']}`：{case['failure_group']} / {case['error_category']}" +
                         (f" / {case['error_field']}" if case.get("error_field") else ""))
        elif case["wrong_core_fields"] or case["unsupported_exact_set_wrong"]:
            wrong = ", ".join(case["wrong_core_fields"]) or "无"
            lines.append(f"- `{case['case_id']}`：有效；核心字段错误：{wrong}；原词集合错误：{'是' if case['unsupported_exact_set_wrong'] else '否'}。")
    t = result["tokens"]
    lines.extend(["", "## 用量和边界", "",
                  f"v2 输入／完成／总 token：{t['prompt_tokens']}／{t['completion_tokens']}／{t['total_tokens']}；可取得的推理 token：{t['reasoning_tokens']}（缺明细 {result['reasoning_unavailable_calls']} 次）。",
                  f"v2 估算费用 USD {result['estimated_cost_usd']:.6f}；缺可估数据 {result['cost_unavailable_calls']} 次。原版 USD {original['estimated_cost_usd']:.6f}；简写 v1 USD {v1['estimated_cost_usd']:.6f}。实际账单以服务商为准。",
                  "原始模型预测和转换卡只存在本机被 Git 忽略的私有目录；公开报告不包含完整原始回复、请求头或密钥。未接入正式运行时、冻结或评估正式测试集。", ""])
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
