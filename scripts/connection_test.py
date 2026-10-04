"""Exactly one synthetic OpenRouter request; never prints a key or headers."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from music_intent.config import get_settings  # noqa: E402
from music_intent.openrouter_client import OpenRouterFailure, parse_once  # noqa: E402
from music_intent.pricing import estimate_standard_cost_usd  # noqa: E402

SYNTHETIC_SENTENCE = "I'm a bit annoyed right now and want to listen to some quiet music with a clear melody."
PREFLIGHT = ROOT / "data" / "connection_preflight.json"
CODE_FILES = ("src/music_intent/intent.py", "src/music_intent/openrouter_client.py",
              "src/music_intent/pricing.py")


def code_hashes() -> dict[str, str]:
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in CODE_FILES}


def main() -> int:
    parser = argparse.ArgumentParser(description="One synthetic OpenRouter connection test")
    parser.add_argument("--env-file", type=Path, default=None)
    parser.add_argument("--expected-model", default=None)
    args = parser.parse_args()
    with (ROOT / "data" / "user_intents_v2_review.tsv").open(encoding="utf-8", newline="") as handle:
        if SYNTHETIC_SENTENCE in {row["utterance"] for row in csv.DictReader(handle, delimiter="\t")}:
            print("connection=failed category=synthetic_sentence_not_held_out")
            return 2
    try:
        key, model = get_settings(args.env_file)
    except ValueError as error:
        print(f"connection=failed category={error}")
        return 2
    if args.expected_model is not None and model != args.expected_model:
        print("connection=failed category=model_mismatch")
        return 2
    try:
        _, info = parse_once(SYNTHETIC_SENTENCE, key, model)
    except OpenRouterFailure as error:
        print(f"connection=failed model={error.model or model} structured_output_valid=false category={error}")
        print("json_complete={} required_structure_complete={} intent_valid=false".format(
            "unknown" if error.json_complete is None else str(error.json_complete).lower(),
            "unknown" if error.required_structure_complete is None else
            str(error.required_structure_complete).lower()))
        usage = error.usage
        print("finish_reason={} tokens_prompt={} tokens_completion={} tokens_total={} tokens_reasoning={}".format(
            error.finish_reason or "unavailable",
            usage.get("prompt_tokens", "unavailable"),
            usage.get("completion_tokens", "unavailable"),
            usage.get("total_tokens", "unavailable"),
            usage.get("reasoning_tokens", "unavailable"),
        ))
        if error.category == "output_token_limit" and error.content_shape is not None:
            shape = error.content_shape
            def display(value: bool | int | None) -> str:
                return "unavailable" if value is None else str(value).lower()
            print("content_empty={} content_chars={} repeated_suffix={}".format(
                display(shape.get("content_empty")), display(shape.get("content_chars")),
                display(shape.get("repeated_suffix")),
            ))
        print("estimated_cost=" + estimate_cost(error.model or model, usage))
        return 1
    usage = info["usage"]
    prompt = usage.get("prompt_tokens")
    completion = usage.get("completion_tokens")
    total = usage.get("total_tokens")
    print(f"connection=success model={info['model']} structured_output_valid=true")
    print("json_complete=true required_structure_complete=true intent_valid=true")
    print("finish_reason={} tokens_prompt={} tokens_completion={} tokens_total={} tokens_reasoning={}".format(
        info.get("finish_reason", "unavailable"), prompt, completion, total,
        usage.get("reasoning_tokens", "unavailable"),
    ))
    print("estimated_cost=" + estimate_cost(info["model"], usage))
    marker = {"validated_at": datetime.now(ZoneInfo("Asia/Singapore")).isoformat(timespec="seconds"),
              "model": model, "code_sha256": code_hashes(),
              "sentence_sha256": hashlib.sha256(SYNTHETIC_SENTENCE.encode("utf-8")).hexdigest()}
    if PREFLIGHT.exists():
        print("preflight_marker=already_exists; inspect before any formal run")
        return 2
    with PREFLIGHT.open("x", encoding="utf-8") as handle:
        json.dump(marker, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print("preflight_marker=recorded")
    return 0


def estimate_cost(model: str, usage: dict[str, int]) -> str:
    estimate = estimate_standard_cost_usd(model, usage)
    if estimate is None:
        return "unavailable"
    return f"USD {estimate:.6f} (standard list-rate estimate)"


if __name__ == "__main__":
    raise SystemExit(main())
