"""Parse one user-supplied Chinese music request with OpenRouter."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from music_intent.config import get_settings  # noqa: E402
from music_intent.intent import route_status  # noqa: E402
from music_intent.openrouter_client import OpenRouterFailure, parse_once  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse one music request; never prints API credentials")
    parser.add_argument("text", help="The original Chinese request sentence")
    args = parser.parse_args()
    try:
        key, model = get_settings()
        intent, info = parse_once(args.text, key, model)
    except ValueError as error:
        print(f"parse=failed category={error}")
        return 2
    except OpenRouterFailure as error:
        print(f"parse=failed category={error}")
        return 1
    print(json.dumps({"model": info["model"], "intent": intent, "routing_status": route_status(intent)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
