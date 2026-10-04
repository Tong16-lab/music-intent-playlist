"""Local link-only demo; fixed samples are offline, live text is opt-in paid."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "prototypes"))
sys.path.insert(0, str(ROOT / "scripts"))

from compact_dev_v2_request import load_v2_format  # noqa: E402
from evaluate import MODEL, verify_candidate_format  # noqa: E402
from evaluate_compact_dev import call_candidate_once, inspect_candidate_response  # noqa: E402
from music_intent.catalog import load_catalog  # noqa: E402
from music_intent.config import get_settings  # noqa: E402
from music_intent.display import fixed_samples, recommend, render_result  # noqa: E402
from music_intent.openrouter_client import OpenRouterFailure  # noqa: E402


def live_intent(text: str, allow_paid: bool) -> dict:
    if not allow_paid:
        raise ValueError("live_mode_requires_allow_paid")
    prompt, schema, digests = load_v2_format()
    verify_candidate_format(digests)
    key, model = get_settings()
    if model != MODEL:
        raise ValueError("configured_model_differs_from_formal_v2")
    payload = call_candidate_once(text, key, model, prompt, schema)
    record, _ = inspect_candidate_response(payload, "demo_live", text, model, schema)
    if record["intent"] is None:
        category = record.get("error_category") or "invalid_intent"
        field = record.get("error_field")
        raise ValueError(f"intent_validation_failed:{category}" + (f":{field}" if field else ""))
    return record["intent"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Show three reviewed, linked song suggestions")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--sample", choices=sorted(fixed_samples()))
    source.add_argument("--text", help="Live sentence; requires --allow-paid and uses OpenRouter once")
    parser.add_argument("--allow-paid", action="store_true", help="Allow one paid model call in live mode")
    parser.add_argument("--lang", choices=("zh", "en"), default="zh", help="Display language; does not change model input or selection")
    args = parser.parse_args()
    try:
        catalog = load_catalog(ROOT / "data" / "catalog.csv")
        if args.sample:
            utterance, intent = fixed_samples()[args.sample]
            kind = ("Offline fixed sample (prewritten intent card; no model call)" if args.lang == "en"
                    else "离线固定样例（预设意图卡，未调用模型）")
            if args.lang == "en":
                utterance = {
                    "explore": "Play me some music.",
                    "calm": "I want quiet, soothing music.",
                    "path": "Start with energetic songs, then gradually calm down.",
                    "melody": "I want songs with a clear melody and some surprising turns.",
                    "unsupported": "No English-language songs.",
                }[args.sample]
        else:
            utterance, intent = args.text, live_intent(args.text, args.allow_paid)
            kind = ("Live input (compact-dev-v2 passed local validation)" if args.lang == "en"
                    else "实时输入（compact-dev-v2 已通过本地校验）")
        if args.lang == "en":
            request_label = ("English translation of fixed request" if args.sample else "Original live request")
            print(f"# Music recommendation demonstration\n\nMode: {kind}.\n\n{request_label}: {utterance}\n")
        else:
            print(f"# 音乐推荐演示\n\n模式：{kind}。\n\n输入：{utterance}\n")
        print(render_result(recommend(intent, catalog), intent, language=args.lang))
    except (OSError, ValueError, OpenRouterFailure) as error:
        if isinstance(error, OpenRouterFailure):
            print(f"demo_failed:{error.category}", file=sys.stderr)
        else:
            # Error text is controlled locally. It contains no request or response body.
            print(f"demo_failed:{error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
