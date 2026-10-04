"""Independent nine-field, flat-schema probe. Never a formal preflight."""

from __future__ import annotations

import argparse
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
from music_intent.intent import DOMAINS, response_schema  # noqa: E402
from music_intent.openrouter_client import (  # noqa: E402
    ENDPOINT, build_request, classify_http_error, safe_finish_reason,
)
from music_intent.pricing import estimate_standard_cost_usd  # noqa: E402

MODEL = "google/gemini-3.5-flash-lite"
SYNTHETIC_SENTENCE = "I'm a bit annoyed right now and want to listen to some quiet music with a clear melody."
PROMPT_FILE = ROOT / "data" / "FULL_SCHEMA_SHORT_PROMPT.txt"
KNOWN_FIELDS = tuple(response_schema()["required"])


def intermediate_schema() -> dict[str, Any]:
    """Pin the original enumerated nine-field flat probe after runtime changes."""
    schema = response_schema()
    fields = schema["properties"]
    for name in ("target_valence", "target_arousal", "trajectory"):
        fields[name] = fields[name]["anyOf"][0]
    for name in ("current_valence", "current_arousal", "target_valence",
                 "target_arousal", "target_melodic_surprise"):
        fields[name]["enum"] = [*sorted(DOMAINS[name]), None]
    fields["evidence"] = {
        "type": ["string", "null"],
        "description": "One exact substring from the user sentence, or null; diagnostic only",
    }
    fields["constraints"] = {
        "type": "array", "items": {"type": "string"},
        "description": "Unsupported conditions as strings, or [] when none; diagnostic only",
    }
    return schema


def build_probe_request() -> dict[str, Any]:
    request = build_request(SYNTHETIC_SENTENCE, MODEL)
    request["messages"][0]["content"] = PROMPT_FILE.read_text(encoding="utf-8")
    request["response_format"]["json_schema"]["schema"] = intermediate_schema()
    return request


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


def schema_error(value: dict[str, Any]) -> tuple[str, str | None]:
    """Validate this diagnostic shape; return only predefined field names."""
    if set(value) - set(KNOWN_FIELDS):
        return "extra_field", None
    for name in KNOWN_FIELDS:
        item = value[name]
        if name in DOMAINS:
            if item is not None and (type(item) is not int or item not in DOMAINS[name]):
                return "invalid_field_value", name
        elif name == "requires_melody_present":
            if item is not None and type(item) is not bool:
                return "invalid_field_value", name
        elif name == "trajectory":
            if type(item) is not str or item not in {"none", "single_target"}:
                return "invalid_field_value", name
        elif name == "evidence":
            if item is not None and type(item) is not str:
                return "invalid_field_value", name
        elif name == "constraints":
            if not isinstance(item, list) or any(type(part) is not str for part in item):
                return "invalid_field_value", name
    return "none", None


def inspect_response(payload: Any) -> dict[str, Any]:
    result: dict[str, Any] = {
        "model": MODEL, "finish_reason": "unavailable", "usage": {},
        "json_complete": False, "required_fields_present": None,
        "missing_fields": [], "schema_valid": False, "evidence_valid": None,
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
    missing = sorted(name for name in KNOWN_FIELDS if name not in parsed)
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
    category, field = schema_error(parsed)
    if category != "none":
        result["category"] = category
        result["field"] = field
        return result
    result["schema_valid"] = True
    evidence = parsed["evidence"]
    result["evidence_valid"] = evidence is None or bool(evidence and evidence in SYNTHETIC_SENTENCE)
    result["category"] = "none" if result["evidence_valid"] else "evidence_not_in_utterance"
    return result


def report(result: dict[str, Any]) -> None:
    usage = result["usage"]
    print("probe={} model={} finish_reason={} category={}".format(
        "success" if result["category"] == "none" else "failed",
        result["model"], result["finish_reason"], result["category"]))
    print("json_complete={} required_fields_present={} missing_fields={} schema_valid={} evidence_valid={}".format(
        str(result["json_complete"]).lower(),
        "unavailable" if result["required_fields_present"] is None else
        str(result["required_fields_present"]).lower(),
        ",".join(result["missing_fields"]) if result["missing_fields"] else "none",
        str(result["schema_valid"]).lower(),
        "unavailable" if result["evidence_valid"] is None else
        str(result["evidence_valid"]).lower()))
    if result.get("field"):
        print("diagnostic_error_field=" + result["field"])
    print("tokens_prompt={} tokens_completion={} tokens_total={} tokens_reasoning={}".format(
        usage.get("prompt_tokens", "unavailable"), usage.get("completion_tokens", "unavailable"),
        usage.get("total_tokens", "unavailable"), usage.get("reasoning_tokens", "unavailable")))
    cost = estimate_standard_cost_usd(result["model"], usage)
    print("estimated_cost=" + ("unavailable" if cost is None else
                                f"USD {cost:.6f} (standard list-rate estimate)"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Isolated diagnostic; requires future paid-call authorization")
    parser.add_argument("--allow-paid-probe", action="store_true")
    args = parser.parse_args(argv)
    if not args.allow_paid_probe:
        print("probe=not_run category=authorization_required")
        return 2
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
    return 0 if result["category"] == "none" else 1


if __name__ == "__main__":
    raise SystemExit(main())
