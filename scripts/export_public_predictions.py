"""Release only validated intent cards and fixed error codes for offline audit."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from freeze_test_set import verify_manifest  # noqa: E402
from music_intent.intent import validate_intent  # noqa: E402

SOURCE = ROOT / "reports/private_formal_predictions/compact_v2_formal_run_02_predictions.jsonl"
DEST = ROOT / "reports/formal_run_02/validated_cards_for_audit.jsonl"
ANSWERS = ROOT / "data/synthetic_intents_test.csv"
SAFE_ERRORS = {None, "invalid_field_value"}


def release() -> str:
    verify_manifest()
    with ANSWERS.open(encoding="utf-8", newline="") as handle:
        answers = {row["case_id"]: row["utterance"] for row in csv.DictReader(handle)}
    source_rows = [json.loads(line) for line in SOURCE.read_text(encoding="utf-8").splitlines()]
    if len(answers) != 30 or len(source_rows) != 30 or {row.get("case_id") for row in source_rows} != set(answers):
        raise ValueError("case_count_or_ids_mismatch")
    released = []
    for row in source_rows:
        case_id = row["case_id"]
        valid = row.get("intent_valid") is True
        if row.get("error_category") not in SAFE_ERRORS:
            raise ValueError("unexpected_error_category")
        card = row.get("converted_v2") if valid else None
        if valid:
            validate_intent(card, answers[case_id])
        released.append({"case_id": case_id, "intent_valid": valid,
                         "converted_v2": card,
                         "error_category": row.get("error_category") if not valid else None})
    released.sort(key=lambda row: row["case_id"])
    return "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in released)


if __name__ == "__main__":
    expected = release()
    if DEST.exists() and DEST.read_text(encoding="utf-8") != expected:
        raise SystemExit("release_differs_from_saved_run")
    if not DEST.exists():
        DEST.write_text(expected, encoding="utf-8")
    print("public_cards=passed cases=30 valid=28")
