"""Render the V2 intent-review TSV as a readable Markdown document."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "user_intents_v2_review.tsv"
DESTINATION = ROOT / "data" / "USER_INTENT_ANNOTATION_V2.md"

FIELD_LABELS = (
    ("current_valence", "Current valence"),
    ("current_arousal", "Current arousal"),
    ("target_valence", "Target valence"),
    ("target_arousal", "Target arousal"),
    ("target_melodic_surprise", "Target melodic surprise"),
)
VALUE_LABELS = {
    "current_valence": {"-1": "slightly negative", "0": "neutral", "1": "slightly positive"},
    "target_valence": {"-1": "negative", "0": "neutral", "1": "positive"},
    "current_arousal": {"1": "Low", "2": "Medium", "3": "High"},
    "target_arousal": {"1": "Low", "2": "Medium", "3": "High"},
    "target_melodic_surprise": {"1": "Low", "2": "Medium", "3": "High"},
}
TRAJECTORY_LABELS = {
    "none": "No explicit music order",
    "single_target": "single target",
    "from_to": "Explicit sequential change",
}


def field_text(row: dict[str, str], evidence: dict[str, str], field: str) -> str:
    value = row[field]
    if not value:
        return "Unspecified"
    if value.startswith("{"):
        rule = json.loads(value)
        relation = {"at_most": "not higher than", "at_least": "not lower than"}[rule["relation"]]
        level = str(rule["value"])
        detail = f"{relation} {level} (boundary: {VALUE_LABELS[field][level]}, not an exact target)"
    else:
        detail = f"{value} ({VALUE_LABELS[field][value]})"
    return f'{detail}; evidence: "{evidence[field]}"'


def render_case(row: dict[str, str]) -> str:
    evidence = json.loads(row["evidence_json"])
    unsupported = json.loads(row["unsupported_condition_phrases"])
    lines = [
        f"### {row['case_id']} · {row['role_id']}",
        "",
        f"> {row['utterance']}",
        "",
    ]
    for field, label in FIELD_LABELS:
        lines.append(f"- {label}: {field_text(row, evidence, field)}")
    if row["requires_melody_present"] == "true":
        lines.append(
            "- Explicitly requires discernible melody: Yes; Evidence: \""
            + evidence["requires_melody_present"]
            + '"'
        )
    else:
        lines.append("- Explicitly requires discernible melody: Not specified")
    trajectory = row["trajectory"]
    if trajectory.startswith("{"):
        path = json.loads(trajectory)
        levels = path["arousal"]
        path_label = path["type"]
        sequence = f"Song activity gradually changes from {levels['from']} to {levels['to']}"
    else:
        path_label = trajectory
        sequence = TRAJECTORY_LABELS[trajectory]
    if path_label != "none":
        sequence += f'; evidence: "{evidence["trajectory"]}"'
    lines.append(f"- Playlist path: {path_label} ({sequence})")
    lines.append(
        "- Unguaranteed explicit conditions: "
        + ("; ".join(f'"{phrase}"' for phrase in unsupported) if unsupported else "None")
    )
    if row["other_request_or_note"]:
        lines.append(f"- Annotation notes: {row['other_request_or_note']}")
    if row["ambiguous"] == "true":
        lines.append("- Pending adjudication: Yes; not ready as a whole-card gold answer.")
    status = {"approved": "Author Verified", "needs_author_review": "Pending Author Verification"}[row["review_status"]]
    lines += [f"- Audit status: {status}", ""]
    return "\n".join(lines)


def main() -> None:
    with SOURCE.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    if len(rows) != 42 or Counter(row["split"] for row in rows) != {"dev": 12, "test": 30}:
        raise ValueError("unexpected_case_count")
    if any(row["review_status"] != "approved" for row in rows):
        raise ValueError("unexpected_review_status")
    for row in rows:
        request = row["requires_melody_present"]
        evidence = json.loads(row["evidence_json"])
        for field, phrase in evidence.items():
            if not isinstance(phrase, str) or phrase not in row["utterance"]:
                raise ValueError(f"invalid_evidence:{row['case_id']}:{field}")
        if request not in {"", "true"}:
            raise ValueError(f"invalid_melody_request:{row['case_id']}")
        phrase = evidence.get("requires_melody_present")
        if request == "true" and (not phrase or phrase not in row["utterance"]):
            raise ValueError(f"missing_melody_evidence:{row['case_id']}")
        if request == "" and phrase is not None:
            raise ValueError(f"unexpected_melody_evidence:{row['case_id']}")
        for field in ("target_valence", "target_arousal"):
            value = row[field]
            if value.startswith("{"):
                rule = json.loads(value)
                if rule.get("relation") not in {"at_most", "at_least"}:
                    raise ValueError(f"invalid_relation:{row['case_id']}:{field}")
                if str(rule.get("value")) not in VALUE_LABELS[field]:
                    raise ValueError(f"invalid_boundary:{row['case_id']}:{field}")
        trajectory = row["trajectory"]
        if trajectory.startswith("{"):
            path = json.loads(trajectory)
            if path.get("type") != "from_to" or set(path) != {"type", "arousal"}:
                raise ValueError(f"invalid_path:{row['case_id']}")
            levels = path["arousal"]
            if set(levels) != {"from", "to"} or levels["from"] not in {1, 2, 3} or levels["to"] not in {1, 2, 3}:
                raise ValueError(f"invalid_path_levels:{row['case_id']}")
            if row["target_arousal"] != str(levels["to"]):
                raise ValueError(f"path_target_mismatch:{row['case_id']}")
        elif trajectory not in TRAJECTORY_LABELS:
            raise ValueError(f"invalid_trajectory:{row['case_id']}")
    parts = [
        "# User Expression and Intent Annotation V2 (Verified by author, formal testing completed)",
        "",
        "This page is generated from the [English V2 annotation table](user_intents_v2_review.tsv) and presents all 42 examples (12 development and 30 test). These are not quotations collected from participants. The author approved the annotations. This English rendering was not used in the recorded Chinese-input evaluation; the exact evaluated table is preserved at commit `a39e3fc`. See the [V2 README](USER_INTENT_ANNOTATION_V2_README.md) for the rules and the [completed result](../reports/formal_run_02/EVALUATION_EN.md) for the historical score.",
        "",
        "Blank fields are displayed as \"Unspecified\"; each non-empty field is followed by evidence from its English rendering. Recognizable melody is separate from the six core intent fields. All 42 records were reviewed by the author.",
        "",
    ]
    for split, title in (("dev", "Development Examples (12 items)"), ("test", "Test Examples (30 items)")):
        parts += [f"## {title}", ""]
        parts.extend(render_case(row) for row in rows if row["split"] == split)
    DESTINATION.write_text("\n".join(parts).rstrip() + "\n", encoding="utf-8")
    print(f"created={DESTINATION} cases={len(rows)}")


if __name__ == "__main__":
    main()
