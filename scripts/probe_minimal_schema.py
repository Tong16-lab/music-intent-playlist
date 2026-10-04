"""One independent, two-field diagnostic call; never creates a formal preflight marker."""

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
from music_intent.openrouter_client import ENDPOINT, classify_http_error, safe_finish_reason  # noqa: E402
from music_intent.pricing import estimate_standard_cost_usd  # noqa: E402

MODEL = "google/gemini-3.5-flash-lite"
SYNTHETIC_SENTENCE = "I'm a bit annoyed right now and want to listen to some quiet music with a clear melody."
PROBE_PROMPT = (
    "Output only JSON that conforms to the schema based on the user's song-seeking query, without any explanation."
    "mood only indicates the music you want to hear: enter calm for explicitly quiet music, otherwise enter other."
    "constraints should only list explicitly specified vocal types, lyric language, or genre requirements as original terms; if none, fill in []."
)
PROBE_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["mood", "constraints"],
    "properties": {
        "mood": {"type": "string", "enum": ["calm", "other"]},
        "constraints": {"type": "array", "items": {"type": "string"}},
    },
}


def build_probe_request() -> dict[str, Any]:
    return {
        "model": MODEL,
        "messages": [{"role": "system", "content": PROBE_PROMPT},
                     {"role": "user", "content": SYNTHETIC_SENTENCE}],
        "response_format": {"type": "json_schema", "json_schema": {
            "name": "minimal_music_probe", "strict": True, "schema": PROBE_SCHEMA}},
        "provider": {"require_parameters": True},
        "usage": {"include": True},
        "reasoning": {"effort": "minimal"},
        "max_tokens": 2048,
    }


def safe_usage(payload: Any) -> dict[str, int]:
    if not isinstance(payload, dict):
        return {}
    result = {name: value for name in ("prompt_tokens", "completion_tokens", "total_tokens")
              if type(value := payload.get(name)) is int and value >= 0}
    details = payload.get("completion_tokens_details")
    reasoning = details.get("reasoning_tokens") if isinstance(details, dict) else None
    if reasoning is None:
        reasoning = payload.get("reasoning_tokens")
    if type(reasoning) is int and reasoning >= 0:
        result["reasoning_tokens"] = reasoning
    return result


def inspect_response(payload: Any) -> dict[str, Any]:
    result: dict[str, Any] = {"model": MODEL, "finish_reason": "unavailable",
                              "usage": {}, "required_fields_present": None,
                              "schema_valid": False, "category": "invalid_response_shape"}
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
    result["finish_reason"] = safe_finish_reason(choice.get("finish_reason"))
    message = choice.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content:
        result["category"] = "missing_content"
        return result
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        result["category"] = "invalid_content_json"
        return result
    if not isinstance(parsed, dict):
        result["category"] = "invalid_field_value"
        return result
    missing = set(PROBE_SCHEMA["required"]) - set(parsed)
    result["required_fields_present"] = not missing
    if result["finish_reason"] == "length":
        result["category"] = "output_token_limit"
    elif result["finish_reason"] != "stop":
        result["category"] = "incomplete_response"
    elif missing:
        result["category"] = "missing_field:" + ",".join(sorted(missing))
    elif set(parsed) - set(PROBE_SCHEMA["required"]):
        result["category"] = "extra_field"
    elif type(parsed["mood"]) is not str or parsed["mood"] not in {"calm", "other"}:
        result["category"] = "invalid_field_value:mood"
    elif not isinstance(parsed["constraints"], list) or not all(
            type(item) is str for item in parsed["constraints"]):
        result["category"] = "invalid_field_value:constraints"
    else:
        result["schema_valid"] = True
        result["category"] = "none"
    return result


def report(result: dict[str, Any]) -> None:
    usage = result["usage"]
    print("probe={} model={} finish_reason={} category={}".format(
        "success" if result["schema_valid"] else "failed", result["model"],
        result["finish_reason"], result["category"]))
    present = result["required_fields_present"]
    print("required_fields_present={} schema_valid={}".format(
        "unavailable" if present is None else str(present).lower(),
        str(result["schema_valid"]).lower()))
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
    return 0 if result["schema_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
