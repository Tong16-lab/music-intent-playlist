"""Convert author-approved V2 TSV into runtime CSVs, preserving V1 files."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SOURCE = DATA / "user_intents_v2_review.tsv"
NAMES = ("synthetic_intents_dev.csv", "synthetic_intents_test.csv", "unsupported_conditions_test.csv")
CORE = ("current_valence", "current_arousal", "target_valence", "target_arousal", "target_melodic_surprise", "trajectory")
EVIDENCE_FIELDS = (*CORE, "requires_melody_present")
ANSWER_FIELDS = [
    "case_id", "synthetic_role_id", "utterance", "split",
    *(part for field in (*CORE[:5], "requires_melody_present", "trajectory")
      for part in (field, f"{field}_evidence")),
    "ambiguous", "other_request_or_note", "review_status",
]
UNSUPPORTED_FIELDS = ["case_id", "utterance", "unsupported_condition_phrases",
                      "expected_cannot_guarantee_constraint", "review_status"]


def read_rows(path: Path, delimiter: str = ",") -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        rows = list(reader)
    if not rows or any(None in row for row in rows):
        raise ValueError(f"bad_table:{path.name}")
    return rows


def source_rows() -> list[dict[str, str]]:
    rows = read_rows(SOURCE, "\t")
    expected_ids = {f"dev_{i:03d}" for i in range(1, 13)} | {f"test_{i:03d}" for i in range(1, 31)}
    if len(rows) != 42 or {row["case_id"] for row in rows} != expected_ids:
        raise ValueError("v2_ids_or_count")
    roles = {"dev": set(), "test": set()}
    for row in rows:
        case_id = row["case_id"]
        split = row["split"]
        if split not in roles or not case_id.startswith(split + "_") or row["review_status"] != "approved":
            raise ValueError(f"v2_split_or_approval:{case_id}")
        if row["ambiguous"] != "false" or not row["role_id"].startswith("P"):
            raise ValueError(f"v2_ambiguity_or_role:{case_id}")
        roles[split].add(row["role_id"])
        try:
            evidence = json.loads(row["evidence_json"])
            phrases = json.loads(row["unsupported_condition_phrases"])
        except json.JSONDecodeError:
            raise ValueError(f"v2_bad_json:{case_id}") from None
        if not isinstance(evidence, dict) or set(evidence) - set(EVIDENCE_FIELDS):
            raise ValueError(f"v2_evidence_shape:{case_id}")
        if not isinstance(phrases, list) or any(
            not isinstance(p, str) or not p or p not in row["utterance"] for p in phrases
        ):
            raise ValueError(f"v2_unsupported_evidence:{case_id}")
        for field in EVIDENCE_FIELDS:
            value = row[field]
            phrase = evidence.get(field, "")
            active = bool(value) and value != "none"
            if active != bool(phrase) or (phrase and (not isinstance(phrase, str) or phrase not in row["utterance"])):
                raise ValueError(f"v2_evidence:{case_id}:{field}")
    if roles["dev"] & roles["test"] or len(roles["dev"]) != 4 or len(roles["test"]) != 10:
        raise ValueError("v2_role_leakage_or_count")
    return rows


def expected_outputs() -> dict[str, tuple[list[str], list[dict[str, str]]]]:
    output = {
        "synthetic_intents_dev.csv": (ANSWER_FIELDS, []),
        "synthetic_intents_test.csv": (ANSWER_FIELDS, []),
        "unsupported_conditions_test.csv": (UNSUPPORTED_FIELDS, []),
    }
    for source in source_rows():
        evidence = json.loads(source["evidence_json"])
        answer = {"case_id": source["case_id"], "synthetic_role_id": source["role_id"],
                  "utterance": source["utterance"], "split": source["split"],
                  "ambiguous": source["ambiguous"],
                  "other_request_or_note": source["other_request_or_note"],
                  "review_status": source["review_status"]}
        for field in EVIDENCE_FIELDS:
            answer[field] = source[field]
            answer[f"{field}_evidence"] = evidence.get(field, "")
        output[f"synthetic_intents_{source['split']}.csv"][1].append(answer)
        if source["split"] == "test":
            phrases = json.loads(source["unsupported_condition_phrases"])
            output["unsupported_conditions_test.csv"][1].append({
                "case_id": source["case_id"], "utterance": source["utterance"],
                "unsupported_condition_phrases": source["unsupported_condition_phrases"],
                "expected_cannot_guarantee_constraint": "true" if phrases else "false",
                "review_status": source["review_status"],
            })
    return output


def render(fields: list[str], rows: list[dict[str, str]]) -> str:
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


def check() -> dict[str, int]:
    outputs = expected_outputs()
    for name, (fields, expected) in outputs.items():
        path = DATA / name
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != fields or list(reader) != expected:
                raise ValueError(f"not_v2_exact:{name}")
    return {name: len(rows) for name, (_, rows) in outputs.items()}


def apply() -> None:
    outputs = expected_outputs()
    legacy = DATA / "legacy_v1"
    if legacy.exists():
        for name in NAMES:
            if (DATA / name).read_text(encoding="utf-8") != render(*outputs[name]):
                raise ValueError(f"existing_v2_or_user_edit_not_overwritten:{name}")
        return
    legacy.mkdir(exist_ok=False)
    old_hashes = {}
    for name in NAMES:
        raw = (DATA / name).read_bytes()
        (legacy / name).write_bytes(raw)
        old_hashes[name] = hashlib.sha256(raw).hexdigest()
    for name, (fields, rows) in outputs.items():
        (DATA / name).write_text(render(fields, rows), encoding="utf-8")
    summary = check()
    source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    note = ["# V2 Answer Migration Record", "", "The only source verified by the author: `user_intents_v2_review.tsv`. The old CSV is kept as is in `legacy_v1/`.",
            "", f"V2 TSV SHA-256: `{source_hash}`", "", "| File | Legacy SHA-256 | V2 Lines |", "| --- | --- | ---: |"]
    for name in NAMES:
        note.append(f"| `{name}` | `{old_hashes[name]}` | {summary[name]} |")
    note.extend(["", "Migration only changes the answer file used by the program; it neither freezes nor runs the formal evaluation."])
    (DATA / "V2_MIGRATION.md").write_text("\n".join(note) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("apply", "check"))
    args = parser.parse_args()
    try:
        if args.command == "apply":
            apply()
        print("v2_sync=passed " + " ".join(f"{name}={count}" for name, count in check().items()))
    except (ValueError, OSError) as error:
        raise SystemExit(f"v2_sync=failed reason={error}") from None
