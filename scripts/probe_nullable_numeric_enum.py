"""One-call diagnostic removing only five nullable numeric enums from the flat probe."""

from __future__ import annotations

import argparse
import csv
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from probe_intermediate_schema import (  # Reuse the same held-out sentence and local value checks.
    ENDPOINT, MODEL, ROOT, SYNTHETIC_SENTENCE,
    build_probe_request as build_intermediate_request,
    classify_http_error, get_settings, inspect_response,
)
from music_intent.pricing import estimate_standard_cost_usd

NUMERIC_FIELDS = (
    "current_valence", "current_arousal", "target_valence", "target_arousal",
    "target_melodic_surprise",
)


def build_probe_request() -> dict[str, Any]:
    """The only request difference is removal of five enum entries in the Schema."""
    request = build_intermediate_request()
    properties = request["response_format"]["json_schema"]["schema"]["properties"]
    for name in NUMERIC_FIELDS:
        if properties[name]["type"] != ["integer", "null"]:
            raise ValueError("unexpected_numeric_type")
        del properties[name]["enum"]
    return request


def report(result: dict[str, Any]) -> None:
    """Print fixed, safe diagnostics only; never print response content."""
    usage = result["usage"]
    print("probe={} model={} finish_reason={} category={}".format(
        "success" if result["category"] == "none" else "failed",
        result["model"], result["finish_reason"], result["category"]))
    print("json_complete={} required_fields_present={} missing_fields={} field_values_valid={} evidence_valid={}".format(
        str(result["json_complete"]).lower(),
        "unavailable" if result["required_fields_present"] is None else
        str(result["required_fields_present"]).lower(),
        ",".join(result["missing_fields"]) if result["missing_fields"] else "none",
        str(result["schema_valid"]).lower(),
        "unavailable" if result["evidence_valid"] is None else
        str(result["evidence_valid"]).lower()))
    if result.get("field"):
        print("local_error_field=" + result["field"])
    print("tokens_prompt={} tokens_completion={} tokens_total={} tokens_reasoning={}".format(
        usage.get("prompt_tokens", "unavailable"), usage.get("completion_tokens", "unavailable"),
        usage.get("total_tokens", "unavailable"), usage.get("reasoning_tokens", "unavailable")))
    cost = estimate_standard_cost_usd(result["model"], usage)
    print("estimated_cost=" + ("unavailable" if cost is None else
                                f"USD {cost:.6f} (standard list-rate estimate)"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Isolated paid diagnostic; no formal preflight marker")
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
