"""Rebuild the verified 35-track, link-only catalog from its checked-in snapshot."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DOCUMENT = ROOT / "data" / "catalog_source_snapshot.md"
CATALOG = ROOT / "data" / "catalog.csv"
SNAPSHOT = "cafd8e20c265ed84f1e61f1c875327971f43a62f"
FIELDS = (
    "track_id", "title", "artist", "source_url", "duration_mm_ss",
    "mood_theme_tags", "listening_group", "link_identity_status", "link_checked_at",
    "page_artist", "identity_confirmed_by", "identity_confirmed_at",
    "current_audio_license_status", "display_policy", "valence", "arousal",
    "melody_present", "melodic_surprise", "surprise_evidence", "review_note",
    "label_status",
)
SOURCE_HEADERS = ("track_id", "title / track_url", "artist", "duration_mm_ss",
                  "mood_theme_tags", "listening_group", "license_record_original",
                  "current_audio_license_status", "link_identity_status", "link_checked_at")
LABEL_HEADERS = ("track_id", "title", "artist", "valence", "arousal",
                 "melody_present", "melodic_surprise", "surprise_evidence", "review_note")
PAGE_ARTIST_VARIANTS = {
    "track_1028896": "Dave Imbernon",
    "track_1231364": "LEEAAV",
    "track_1133285": "Veaceslav Draganov",
}
CONFIRMED_ARTIST_VARIANTS = {"track_1231364", "track_1133285"}


def _section(document: str, start: str, end: str) -> str:
    if document.count(start) != 1 or document.count(end) != 1:
        raise ValueError("catalog_document_section_missing_or_duplicated")
    return document.split(start, 1)[1].split(end, 1)[0]


def _table(section: str, headers: tuple[str, ...]) -> dict[str, dict[str, str]]:
    header = "| " + " | ".join(headers) + " |"
    if headers == LABEL_HEADERS:
        # The label table is padded for Markdown alignment.
        candidates = [line for line in section.splitlines() if line.startswith("| track_id")]
        if len(candidates) != 1 or tuple(cell.strip() for cell in candidates[0].strip("|").split("|")) != headers:
            raise ValueError("catalog_label_headers_changed")
    elif section.count(header) != 1:
        raise ValueError("catalog_source_headers_changed")
    rows: dict[str, dict[str, str]] = {}
    for line in section.splitlines():
        if not re.match(r"^\|\s*track_\d+\s*\|", line):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != len(headers):
            raise ValueError("catalog_table_column_count")
        row = dict(zip(headers, cells))
        track_id = row["track_id"]
        if not re.fullmatch(r"track_\d{7}", track_id) or track_id in rows:
            raise ValueError("catalog_duplicate_or_invalid_track_id")
        rows[track_id] = row
    if len(rows) != 35:
        raise ValueError("catalog_requires_exactly_35_rows")
    return rows


def build_rows(document: str) -> list[dict[str, str]]:
    source = _table(_section(document, "## Source rows", "## Label rows"), SOURCE_HEADERS)
    label_section = _section(document, "## Label rows", "## End of catalog source")
    labels = _table(label_section, LABEL_HEADERS)
    if set(source) != set(labels):
        raise ValueError("catalog_source_label_id_mismatch")
    if "35 tracks have label_status=verified" not in document or "Niu Tong confirmed artist variants on 2026-10-02" not in document:
        raise ValueError("catalog_author_verification_statement_missing")
    if {track_id for track_id, row in source.items()
            if row["link_identity_status"] == "artist_variant_confirmed"} != CONFIRMED_ARTIST_VARIANTS:
        raise ValueError("catalog_artist_confirmation_mismatch")
    rows = []
    for track_id in sorted(source):
        item, annotation = source[track_id], labels[track_id]
        link = re.fullmatch(r"\[([^\]]+)\]\((https://www\.jamendo\.com/track/(\d+))\)",
                            item["title / track_url"])
        if not link or int(link.group(3)) != int(track_id.split("_", 1)[1]):
            raise ValueError(f"catalog_invalid_source_link:{track_id}")
        title, source_url = link.group(1), link.group(2)
        artist = item["artist"]
        if not title or not artist or annotation["title"] != title or annotation["artist"] != artist:
            raise ValueError(f"catalog_source_label_identity_mismatch:{track_id}")
        if not re.fullmatch(r"\d+:[0-5]\d", item["duration_mm_ss"]):
            raise ValueError(f"catalog_invalid_duration:{track_id}")
        tags = item["mood_theme_tags"].split("; ")
        if not tags or any(not re.fullmatch(r"mood/theme---[a-z]+", tag) for tag in tags):
            raise ValueError(f"catalog_invalid_source_tags:{track_id}")
        if not item["license_record_original"].startswith("Available under a Creative Commons "):
            raise ValueError(f"catalog_missing_historical_license_record:{track_id}")
        if item["current_audio_license_status"] != "not_checked":
            raise ValueError(f"catalog_unexpected_current_audio_license_status:{track_id}")
        status = item["link_identity_status"]
        if status not in {"matched", "minor_spelling_variant", "artist_variant_confirmed",
                          "review_needed", "unavailable"}:
            raise ValueError(f"catalog_invalid_identity_status:{track_id}")
        date.fromisoformat(item["link_checked_at"])
        if annotation["valence"] not in {"-1", "0", "1", "unknown"} or annotation["arousal"] not in {
                "1", "2", "3", "unknown"}:
            raise ValueError(f"catalog_invalid_emotion_label:{track_id}")
        melody, surprise = annotation["melody_present"], annotation["melodic_surprise"]
        if melody not in {"yes", "no", "unknown"} or surprise not in {"1", "2", "3", "unknown"}:
            raise ValueError(f"catalog_invalid_melody_label:{track_id}")
        if (melody != "yes" and surprise != "unknown") or (surprise in {"2", "3"}
                                                             and not annotation["surprise_evidence"]):
            raise ValueError(f"catalog_melody_evidence_conflict:{track_id}")
        if status == "artist_variant_confirmed":
            confirmed_by, confirmed_at = "Niu Tong", "2026-10-02"
        else:
            confirmed_by = confirmed_at = ""
        if status == "minor_spelling_variant" and track_id != "track_1028896":
            raise ValueError(f"catalog_unrecorded_spelling_variant:{track_id}")
        rows.append({
            "track_id": track_id, "title": title, "artist": artist, "source_url": source_url,
            "duration_mm_ss": item["duration_mm_ss"],
            "mood_theme_tags": item["mood_theme_tags"], "listening_group": item["listening_group"],
            "link_identity_status": status, "link_checked_at": item["link_checked_at"],
            "page_artist": PAGE_ARTIST_VARIANTS.get(track_id, ""),
            "identity_confirmed_by": confirmed_by, "identity_confirmed_at": confirmed_at,
            "current_audio_license_status": item["current_audio_license_status"],
            "display_policy": "external_link_only",
            "valence": annotation["valence"], "arousal": annotation["arousal"],
            "melody_present": melody, "melodic_surprise": surprise,
            "surprise_evidence": annotation["surprise_evidence"],
            "review_note": annotation["review_note"], "label_status": "verified",
        })
    return rows


def render_csv(rows: list[dict[str, str]]) -> str:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export or verify the 35-track catalog")
    parser.add_argument("command", choices=("export", "check"))
    args = parser.parse_args(argv)
    try:
        document_bytes = SOURCE_DOCUMENT.read_bytes()
        rows = build_rows(document_bytes.decode("utf-8"))
        expected = render_csv(rows)
        if args.command == "export":
            if CATALOG.exists() and CATALOG.read_text(encoding="utf-8") != expected:
                raise ValueError("catalog_exists_with_different_content")
            if not CATALOG.exists():
                CATALOG.write_text(expected, encoding="utf-8")
        elif not CATALOG.exists() or CATALOG.read_text(encoding="utf-8") != expected:
            raise ValueError("catalog_does_not_match_source_document")
    except (OSError, UnicodeError, ValueError) as error:
        print(f"catalog_{args.command}=failed reason={error}")
        return 1
    print(f"catalog_{args.command}=passed tracks={len(rows)} unique_ids={len({r['track_id'] for r in rows})} "
          f"source_document_sha256={hashlib.sha256(document_bytes).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
