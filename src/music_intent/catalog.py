"""Load the author-reviewed catalog without inferring any missing metadata."""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

from .recommender import IDENTITY_OK

REQUIRED = {"track_id", "title", "artist", "source_url", "link_identity_status",
            "label_status", "valence", "arousal", "melody_present",
            "melodic_surprise", "current_audio_license_status", "display_policy"}


def load_catalog(path: Path, expected_count: int = 35) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not REQUIRED <= set(reader.fieldnames):
            raise ValueError("catalog_missing_columns")
        rows = list(reader)
    if len(rows) != expected_count or len({row["track_id"] for row in rows}) != expected_count:
        raise ValueError("catalog_count_or_duplicate_id")
    for row in rows:
        track_id = row["track_id"]
        if (not re.fullmatch(r"track_\d{7}", track_id)
                or row["source_url"] != f"https://www.jamendo.com/track/{int(track_id[6:])}"
                or not row["title"].strip() or not row["artist"].strip()):
            raise ValueError("catalog_invalid_identity")
        if (row["link_identity_status"] not in IDENTITY_OK
                or row["label_status"] != "verified"
                or row["current_audio_license_status"] != "not_checked"
                or row["display_policy"] != "external_link_only"):
            raise ValueError("catalog_invalid_status")
        if (row["valence"] not in {"-1", "0", "1", "unknown"}
                or row["arousal"] not in {"1", "2", "3", "unknown"}
                or row["melody_present"] not in {"yes", "no", "unknown"}
                or row["melodic_surprise"] not in {"1", "2", "3", "unknown"}):
            raise ValueError("catalog_invalid_labels")
        if row["melody_present"] != "yes" and row["melodic_surprise"] != "unknown":
            raise ValueError("catalog_melody_conflict")
    return rows
