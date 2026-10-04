"""Verify the recorded Chinese-input freeze against the original Git commit.

The current English files are reading translations and intentionally have
different bytes. This script makes no API call and never changes the checkout.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_COMMIT = "a39e3fc"
MANIFEST = ROOT / "data" / "test_set_freeze.json"


def verify() -> None:
    expected = json.loads(MANIFEST.read_text(encoding="utf-8"))["files"]
    for filename, digest in expected.items():
        original = subprocess.check_output(
            ["git", "show", f"{SOURCE_COMMIT}:data/{filename}"], cwd=ROOT
        )
        if hashlib.sha256(original).hexdigest() != digest:
            raise ValueError(f"historical_freeze_mismatch:{filename}")


if __name__ == "__main__":
    verify()
    print(f"historical_freeze_verification=passed commit={SOURCE_COMMIT}")
