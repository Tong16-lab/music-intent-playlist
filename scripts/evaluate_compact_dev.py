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
    rows = ["| 指标 | 原版端到端 | 候选端到端 | 原版仅有效 | 候选仅有效 | 同一关键词基线 |",
            "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for field in CORE_FIELDS:
        rows.append(f"| `{field}` | {old_score['end_to_end']['core_fields'][field]}/{old_n} | "
                    f"{new_score['end_to_end']['core_fields'][field]}/{n} | "
                    f"{old_score['valid_only']['core_fields'][field]}/{old_valid_n} | "
                    f"{new_score['valid_only']['core_fields'][field]}/{valid_n} | "
                    f"{new_score['keyword_baseline']['core_fields'][field]}/{n} |")
    for label, name in (("六字段整卡", "core_cards"),
                        ("requires_melody_present", "requires_melody_present"),
                        ("不支持条件原词集合全对", "unsupported_exact_sets"),
                        ("cannot_guarantee_constraint 状态", "cannot_guarantee_constraint_status")):
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
    lines = ["# 九字段简写格式：合成开发集受控比较", "",
             "本次对照改变了**输出 Schema 和解释简写格式所需的提示词两处文字**，并非只改一个 API 参数。模型、12 条合成开发句、其他请求参数、V2 答案、关键词基线与本地校验保持一致。未调用正式测试句。",
             "", f"候选版本：`{result['version']}`；提示词 SHA-256：`{result['prompt_sha256']}`；Schema SHA-256：`{result['schema_sha256']}`。",
             f"模型：`{result['model']}`；新加坡开始时间：`{result['started_at']}`。",
             f"调用 {attempted}/12，提前停止：{'是' if result['stopped_early'] else '否'}；完整 JSON {result['json_complete_calls']}/{attempted}，必填结构完整 {result['required_structure_complete_calls']}/{attempted}，简写转换完成 {result['conversion_complete_calls']}/{attempted}，V2 本地校验通过 {result['locally_valid_calls']}/{attempted}。",
             f"未取得有效意图卡 {score['failed_calls']} 次（其中 API 失败 {result['failure_groups'].get('api', 0)} 次）；分组 {json.dumps(result['failure_groups'], ensure_ascii=False, sort_keys=True)}；安全错误类别 {json.dumps(result['error_categories'], ensure_ascii=False, sort_keys=True)}。",
             "", "## 与原版及关键词基线比较", ""]
    if attempted != 12:
        lines.append("候选版提前停止，候选和基线只统计已调用的开发句；原版统计全部 12 句，横向数值不可直接作为同一分母的性能差异。")
        lines.append("")
    lines.extend(_metric_rows(result, old))
    lines.extend(["", "端到端分母包括无有效意图卡的调用；仅有效输出分母只包括通过转换及 V2 本地校验的意图卡。无效输出不算模型对条件的误报或漏报。关键词基线仍使用项目原有实现。",
                  "", "## 不支持条件原词", "",
                  f"候选端到端预期原词 {end['unsupported_expected_phrases']} 个，未完成 {end['unsupported_unfulfilled_phrases']} 个；其中 {end['unsupported_unfulfilled_due_to_call_failure']} 个属于无有效意图卡。",
                  (f"候选仅有效输出：命中 {valid['unsupported_true_positive_phrases']}、误报 {valid['unsupported_false_positive_phrases']}、漏报 {valid['unsupported_missed_phrases']}；分母为 {valid['denominator']} 条有效输出、其中预期原词 {valid['unsupported_expected_phrases']} 个。"
                   if valid['denominator'] else "候选没有有效输出，不计算模型原词命中／误报／漏报。"),
                  f"原版仅有效输出：命中 {old['scores']['valid_only']['unsupported_true_positive_phrases']}、误报 {old['scores']['valid_only']['unsupported_false_positive_phrases']}、漏报 {old['scores']['valid_only']['unsupported_missed_phrases']}；分母为 {old['scores']['valid_only']['denominator']} 条。",
                  "", "## 错误与用量", ""])
    for stage, count in sorted(result["failure_stages"].items()):
        lines.append(f"- `{stage}`：{count} 次")
    for case in result["case_summaries"]:
        if not case["intent_valid"]:
            lines.append(f"- `{case['case_id']}`：{case['failure_group']} / {case['error_category']}" +
                         (f" / {case['error_field']}" if case.get("error_field") else ""))
        else:
            wrong = ", ".join(case["wrong_core_fields"]) or "无"
            lines.append(f"- `{case['case_id']}`：有效；核心字段错误：{wrong}；条件集合错误：{'是' if case['unsupported_exact_set_wrong'] else '否'}。")
    token = result["tokens"]
    false_positive_cases = sum(
        case.get("unsupported_false_positive_count", 0) > 0
        for case in result["case_summaries"] if case["intent_valid"]
    )
    lines.extend(["", f"候选输入／完成／总 token：{token['prompt_tokens']}／{token['completion_tokens']}／{token['total_tokens']}；可取得的推理 token：{token['reasoning_tokens']}（缺明细 {result['reasoning_unavailable_calls']} 次）。",
                  f"候选估算费用 USD {result['estimated_cost_usd']:.6f}；缺少可估数据的调用 {result['cost_unavailable_calls']} 次。原版输入／完成／总 token：{old['tokens']['prompt_tokens']}／{old['tokens']['completion_tokens']}／{old['tokens']['total_tokens']}；原版估算费用 USD {old['estimated_cost_usd']:.6f}。实际账单以服务商为准。",
                  "", "## 对照判断", "",
                  f"格式方面：原版必填结构 {old['required_structure_complete_calls']}/12、本地有效 {old['locally_valid_calls']}/12；候选必填结构 {result['required_structure_complete_calls']}/{attempted}、转换完成 {result['conversion_complete_calls']}/{attempted}、本地有效 {result['locally_valid_calls']}/{attempted}。这显示本次候选输出更常满足结构要求，但不能单凭一次开发集对照证明原因就是简写 Schema。",
                  f"意图方面：原版六字段整卡 {old['scores']['end_to_end']['core_cards']}/12，候选 {end['core_cards']}/{attempted}，关键词基线 {score['keyword_baseline']['core_cards']}/{attempted}。候选的有效输出更多，但整卡正确数没有随之增加；有效输出分母也不同（原版 {old['scores']['valid_only']['denominator']}，候选 {valid['denominator']}），不能把格式成功写成意图判断成功。",
                  f"约束方面：候选在 {false_positive_cases}/{valid['denominator']} 条有效输出中仍有原词误报，共 {valid['unsupported_false_positive_phrases']} 个；另有 {valid['unsupported_missed_phrases']} 个漏报。原版有效输出中有 {old['scores']['valid_only']['unsupported_false_positive_phrases']} 个误报、{old['scores']['valid_only']['unsupported_missed_phrases']} 个漏报。两版有效集合不同，不能仅用总数判定误报率变化。",
                  "建议：暂不采用候选格式作为正式运行时。它值得保留为结构改善的开发原型，但需先在开发集上解决意图整卡与约束误报，再考虑另一轮受控比较；不得用本次结果改动已批准答案或推断正式测试成绩。",
                  "", "本报告只比较合成开发句的意图解析。结构或转换成功并不等于意图判断正确；模型原始预测和转换结果仅存于本机被 Git 忽略的目录。未生成正式预检标记，未冻结或运行正式测试。", ""])
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
