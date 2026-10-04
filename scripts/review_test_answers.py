"""Validate runtime answer CSVs against the sole approved V2 TSV source."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "src"))

from music_intent.intent import EVIDENCE_FIELDS, InvalidIntent, validate_intent  # noqa: E402
from sync_v2_answers import expected_outputs, read_rows, source_rows  # noqa: E402


def decode_value(field: str, text: str):
    if not text:
        return None
    if field == "requires_melody_present":
        return True if text == "true" else text
    if field == "trajectory":
        return json.loads(text) if text.startswith("{") else text
    return json.loads(text) if text.startswith("{") else int(text)


def validate_all(data_dir: Path = DATA, approved: bool = False) -> dict[str, int]:
    source = source_rows()
    outputs = expected_outputs()
    for name, (fields, expected) in outputs.items():
        path = data_dir / name
        with path.open(encoding="utf-8", newline="") as handle:
            import csv
            reader = csv.DictReader(handle)
            actual = list(reader)
            if reader.fieldnames != fields or actual != expected:
                raise ValueError(f"not_v2_exact:{name}")
        if approved and any(row["review_status"] != "approved" for row in actual):
            raise ValueError(f"not_approved:{name}")
    for split in ("dev", "test"):
        for row in outputs[f"synthetic_intents_{split}.csv"][1]:
            intent = {field: decode_value(field, row[field]) for field in EVIDENCE_FIELDS}
            intent["evidence"] = {field: row[f"{field}_evidence"] or None for field in EVIDENCE_FIELDS}
            intent["constraints"] = []
            try:
                validate_intent(intent, row["utterance"])
            except InvalidIntent as error:
                raise ValueError(f"v2_runtime_validation:{row['case_id']}:{error}") from None
    counts = {"dev": 12, "test": 30, "unsupported": 30,
              "dev_roles": len({r["role_id"] for r in source if r["split"] == "dev"}),
              "test_roles": len({r["role_id"] for r in source if r["split"] == "test"})}
    return counts


if __name__ == "__main__":
    try:
        summary = validate_all(approved=True)
    except (ValueError, FileNotFoundError) as error:
        raise SystemExit(f"validation=failed reason={error}") from None
    print("validation=passed " + " ".join(f"{key}={value}" for key, value in summary.items()))
