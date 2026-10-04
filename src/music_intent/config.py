"""Load local OpenRouter settings without printing secrets."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RECOMMENDED_MODEL = "google/gemini-3.5-flash-lite"


def load_dotenv(path: Path | None = None) -> None:
    """Load simple KEY=VALUE lines; existing process variables take precedence."""
    source = path or ROOT / ".env"
    if not source.is_file():
        return
    for raw in source.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[7:]
        name, value = line.split("=", 1)
        name = name.strip()
        if name not in {"OPENROUTER_API_KEY", "OPENROUTER_MODEL"}:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ.setdefault(name, value)


def get_settings(path: Path | None = None) -> tuple[str, str]:
    load_dotenv(path)
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    model = os.environ.get("OPENROUTER_MODEL", "").strip()
    if not key:
        raise ValueError("missing_key")
    if not model:
        raise ValueError("missing_model")
    return key, model
