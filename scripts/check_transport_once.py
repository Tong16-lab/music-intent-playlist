"""One future author-gated connection check on a held-out synthetic sentence."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "prototypes"))
sys.path.insert(0, str(ROOT / "scripts"))

import evaluate_compact_dev as candidate_runner  # noqa: E402
from compact_dev_v2_request import load_v2_format  # noqa: E402
from evaluate import MODEL, verify_candidate_format  # noqa: E402
from music_intent.config import get_settings  # noqa: E402
from music_intent.openrouter_client import OpenRouterFailure  # noqa: E402
from music_intent.pricing import estimate_standard_cost_usd  # noqa: E402

SYNTHETIC_SENTENCE = "我现在有点烦，想听一首安静、有清楚旋律的音乐。"


def _print_usage(usage: dict[str, int], model: str) -> None:
    estimate = estimate_standard_cost_usd(model, usage)
    print("tokens_input={} tokens_output={} tokens_reasoning={} estimated_cost_usd={}".format(
        usage.get("prompt_tokens", "unavailable"),
        usage.get("completion_tokens", "unavailable"),
        usage.get("reasoning_tokens", "unavailable"),
        "unavailable" if estimate is None else f"{estimate:.6f}"))


def run() -> int:
    with (ROOT / "data" / "user_intents_v2_review.tsv").open(encoding="utf-8", newline="") as handle:
        if SYNTHETIC_SENTENCE in {row["utterance"] for row in csv.DictReader(handle, delimiter="\t")}:
            raise ValueError("connection_sentence_not_held_out")
    prompt, schema, digests = load_v2_format()
    verify_candidate_format(digests)
    key, model = get_settings()
    if model != MODEL:
        raise ValueError("connection_model_mismatch")
    try:
        payload = candidate_runner.call_candidate_once(SYNTHETIC_SENTENCE, key, model, prompt, schema)
    except OpenRouterFailure as error:
        print("connection_check=failed category={} transport_phase={} http_status={} "
              "processable_response=false finish_reason={} model={} provider_reached=unknown".format(
            error.category, error.transport_phase or "unavailable",
            error.http_status if error.http_status is not None else "unavailable",
            error.finish_reason or "unavailable", model))
        _print_usage(error.usage, model)
        return 1
    record, _ = candidate_runner.inspect_candidate_response(
        payload, "connection_check", SYNTHETIC_SENTENCE, model, schema)
    if record["model"] != MODEL:
        print("connection_check=failed category=response_model_mismatch transport_phase=api_response "
              "http_status=unavailable processable_response=true finish_reason={} "
              "model={} provider_reached=unknown".format(record["finish_reason"], record["model"]))
        _print_usage(record["usage"], record["model"])
        return 1
    print("connection_check={} category={} transport_phase=api_response http_status=unavailable "
          "processable_response={} finish_reason={} model={} json_complete={} structure_complete={} "
          "conversion_complete={} local_valid={} provider_reached=unknown".format(
              "passed" if record["intent"] is not None else "failed",
              record["error_category"] or "none", isinstance(payload, dict),
              record["finish_reason"], record["model"], record["json_complete"],
              record["required_structure_complete"], record["conversion_complete"],
              record["intent"] is not None))
    _print_usage(record["usage"], record["model"])
    return 0 if record["intent"] is not None else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="One paid, held-out synthetic connection check")
    parser.add_argument("--allow-paid-connection", action="store_true")
    args = parser.parse_args(argv)
    if not args.allow_paid_connection:
        print("connection_check=not_run category=authorization_required")
        return 2
    try:
        return run()
    except (ValueError, OSError):
        print("connection_check=failed category=local_precheck")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
