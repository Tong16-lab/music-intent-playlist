"""Historical short-prompt probe pinned to the original enumerated full Schema."""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from music_intent.config import get_settings  # noqa: E402
from music_intent.intent import DOMAINS, InvalidIntent, response_schema, validate_intent  # noqa: E402
from music_intent.openrouter_client import (  # noqa: E402
    ENDPOINT, build_request, classify_http_error, safe_finish_reason,
)
from music_intent.pricing import estimate_standard_cost_usd  # noqa: E402

MODEL = "google/gemini-3.5-flash-lite"
SYNTHETIC_SENTENCE = "我现在有点烦，想听一首安静、有清楚旋律的音乐。"
PROMPT_FILE = ROOT / "data" / "FULL_SCHEMA_SHORT_PROMPT.txt"
LEGACY_NUMERIC_ENUM_FIELDS = (
    "current_valence", "current_arousal", "target_valence", "target_arousal",
    "target_melodic_surprise",
)


def historical_schema() -> dict[str, Any]:
    """Pin the original enumerated full Schema used by this historical probe."""
    schema = response_schema()
    for name in LEGACY_NUMERIC_ENUM_FIELDS:
        node = (schema["properties"][name]["anyOf"][0]
                if name in {"target_valence", "target_arousal"}
                else schema["properties"][name])
        node["enum"] = [*sorted(DOMAINS[name]), None]
    return schema


def build_probe_request() -> dict[str, Any]:
    request = build_request(SYNTHETIC_SENTENCE, MODEL)
    request["messages"][0]["content"] = PROMPT_FILE.read_text(encoding="utf-8")
    request["response_format"]["json_schema"]["schema"] = historical_schema()
    return request


def missing_known_required(schema: dict[str, Any], value: Any, path: str = "") -> list[str]:
    """List only names defined by the formal schema, including nested objects."""
    variants = schema.get("anyOf")
    if isinstance(variants, list):
        if isinstance(value, dict):
            matching = next((item for item in variants if item.get("type") == "object"), None)
            return missing_known_required(matching, value, path) if matching else []
        return []
    if isinstance(value, dict):
        required = schema.get("required", [])
        missing = [f"{path}.{name}".lstrip(".") for name in required if name not in value]
        for name, child_schema in schema.get("properties", {}).items():
            if name in value:
                missing.extend(missing_known_required(child_schema, value[name],
                                                      f"{path}.{name}".lstrip(".")))
        return sorted(missing)
    if isinstance(value, list) and isinstance(schema.get("items"), dict):
        missing = []
        for index, item in enumerate(value):
            missing.extend(missing_known_required(schema["items"], item, f"{path}[{index}]"))
        return sorted(missing)
    return []


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


def inspect_response(payload: Any) -> dict[str, Any]:
    result: dict[str, Any] = {
        "model": MODEL, "finish_reason": "unavailable", "usage": {},
        "json_complete": False, "required_fields_present": None,
        "missing_fields": [], "local_validation": "not_run",
        "category": "invalid_response_shape",
    }
    if not isinstance(payload, dict):
        return result
    result["usage"] = safe_usage(payload.get("usage"))
    raw_model = payload.get("model")
    if isinstance(raw_model, str) and re.fullmatch(r"[A-Za-z0-9._:/-]{1,120}", raw_model):
        result["model"] = raw_model
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        result["category"] = "missing_content"
        return result
    choice = choices[0]
    finish_reason = safe_finish_reason(choice.get("finish_reason"))
    result["finish_reason"] = finish_reason
    message = choice.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content:
        result["category"] = "output_token_limit" if finish_reason == "length" else "missing_content"
        return result
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        result["category"] = "output_token_limit" if finish_reason == "length" else "invalid_content_json"
        return result
    result["json_complete"] = finish_reason == "stop"
    if not isinstance(parsed, dict):
        result["required_fields_present"] = False
        result["category"] = "invalid_root_type"
        return result
    missing = missing_known_required(historical_schema(), parsed)
    result["missing_fields"] = missing
    result["required_fields_present"] = not missing
    if finish_reason == "length":
        result["category"] = "output_token_limit"
        return result
    if finish_reason != "stop":
        result["category"] = "incomplete_response"
        return result
    if missing:
        result["category"] = "missing_field"
        return result
    try:
        validate_intent(parsed, SYNTHETIC_SENTENCE)
    except InvalidIntent as error:
        result["local_validation"] = "failed"
        result["category"] = error.category
        result["field"] = error.field
        return result
    result["local_validation"] = "passed"
    result["category"] = "none"
    return result


def report(result: dict[str, Any]) -> None:
    usage = result["usage"]
    print("probe={} model={} finish_reason={} category={}".format(
        "success" if result["local_validation"] == "passed" else "failed",
        result["model"], result["finish_reason"], result["category"]))
    print("json_complete={} required_fields_present={} missing_fields={} local_validation={}".format(
        str(result["json_complete"]).lower(),
        "unavailable" if result["required_fields_present"] is None else
        str(result["required_fields_present"]).lower(),
        ",".join(result["missing_fields"]) if result["missing_fields"] else "none",
        result["local_validation"]))
    if result.get("field"):
        print("local_error_field=" + result["field"])
    print("tokens_prompt={} tokens_completion={} tokens_total={} tokens_reasoning={}".format(
        usage.get("prompt_tokens", "unavailable"), usage.get("completion_tokens", "unavailable"),
        usage.get("total_tokens", "unavailable"), usage.get("reasoning_tokens", "unavailable")))
    cost = estimate_standard_cost_usd(result["model"], usage)
    print("estimated_cost=" + ("unavailable" if cost is None else
                                f"USD {cost:.6f} (standard list-rate estimate)"))


def main() -> int:
    with (ROOT / "data" / "user_intents_v2_review.tsv").open(encoding="utf-8", newline="") as handle:
        if SYNTHETIC_SENTENCE in {row["utterance"] for row in csv.DictReader(handle, delimiter="\t")}:
            print("probe=failed category=synthetic_sentence_not_held_out")
            return 2
    try:
        key, configured_model = get_settings()
    except ValueError as error:
        print(f"probe=failed category={error}")
        return 2
    if configured_model != MODEL:
        print("probe=failed category=model_mismatch")
        return 2
    request = Request(ENDPOINT, data=json.dumps(build_probe_request(), ensure_ascii=False).encode("utf-8"),
                      method="POST", headers={"Authorization": f"Bearer {key}",
                                              "Content-Type": "application/json"})
    try:
        with urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except HTTPError as error:
        print("probe=failed category=" + classify_http_error(error.code))
        return 1
    except (URLError, TimeoutError, OSError):
        print("probe=failed category=network")
        return 1
    except (json.JSONDecodeError, UnicodeDecodeError):
        print("probe=failed category=invalid_response_json")
        return 1
    result = inspect_response(payload)
    report(result)
    return 0 if result["local_validation"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
