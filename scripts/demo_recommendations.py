"""Local link-only demonstration of the translated submission's fixed cards.

The scored live parser and its Chinese inputs are preserved at commit a39e3fc.
This English reading branch must not silently turn those scores into an
English-input evaluation.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "prototypes"))
sys.path.insert(0, str(ROOT / "scripts"))

from music_intent.catalog import load_catalog  # noqa: E402
from music_intent.display import fixed_samples, recommend, render_result  # noqa: E402


def live_intent(text: str, allow_paid: bool) -> dict:
    raise ValueError("live_parser_is_historical_only_use_commit_a39e3fc")


def main() -> int:
    parser = argparse.ArgumentParser(description="Show three reviewed, linked song suggestions")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--sample", choices=sorted(fixed_samples()))
    source.add_argument("--text", help="Unavailable in this translated branch; use original commit a39e3fc")
    parser.add_argument("--allow-paid", action="store_true", help="Allow one paid model call in live mode")
    parser.add_argument("--lang", choices=("en",), default="en", help="English display")
    args = parser.parse_args()
    try:
        catalog = load_catalog(ROOT / "data" / "catalog.csv")
        if args.sample:
            utterance, intent = fixed_samples()[args.sample]
            kind = "Offline fixed sample (prewritten intent card; no model call)"
            utterance = {
                "explore": "Play me some music.",
                "calm": "I want quiet, soothing music.",
                "path": "Start with energetic songs, then gradually calm down.",
                "melody": "I want songs with a clear melody and some surprising turns.",
                "unsupported": "No English-language songs.",
            }[args.sample]
        else:
            utterance, intent = args.text, live_intent(args.text, args.allow_paid)
            kind = "Live input"
        print(f"# Music recommendation demonstration\n\nMode: {kind}.\n\nFixed request: {utterance}\n")
        print(render_result(recommend(intent, catalog), intent, language="en"))
    except (OSError, ValueError) as error:
        # Error text is controlled locally. It contains no request or response body.
        print(f"demo_failed:{error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
