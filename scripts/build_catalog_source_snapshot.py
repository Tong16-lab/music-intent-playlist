"""One-time mechanical extraction of the two catalog input tables."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT.parent / "PE6201_Music_Data_Licensing_and_Evaluation_Fillable.md"
SNAPSHOT = ROOT / "data/catalog_source_snapshot.md"
SOURCE_HEADER = "| track_id | title / track_url | artist | duration_mm_ss | mood_theme_tags | listening_group | license_record_original | current_audio_license_status | link_identity_status | link_checked_at |"


def rows(section: str) -> list[str]:
    found = [line for line in section.splitlines() if re.match(r"^\|\s*track_\d{7}\s*\|", line)]
    if len(found) != 35 or len({line.split("|", 2)[1].strip() for line in found}) != 35:
        raise ValueError("expected_35_unique_track_rows")
    return found


def main() -> None:
    source = ORIGINAL.read_text(encoding="utf-8")
    source_part = source.split("## 3. 来源记录、歌曲链接与许可边界", 1)[1].split("## 4. 歌曲标签", 1)[0]
    label_part = source.split("### 逐首标签记录", 1)[1].split("### 程序接口与选歌规则", 1)[0]
    if source_part.count(SOURCE_HEADER) != 1:
        raise ValueError("source_header_missing")
    label_header = next(line for line in label_part.splitlines() if line.startswith("| track_id"))
    content = "\n".join([
        "# Catalog source snapshot", "",
        "This file preserves the 35 source rows and 35 reviewed label rows needed to rebuild `catalog.csv`.",
        "It is a project data snapshot, not a claim that external pages or audio permissions remain unchanged.",
        "Niu Tong reviewed all 35 listening labels on 2026-10-01; 35 tracks have label_status=verified.",
        "Niu Tong confirmed artist variants on 2026-10-02. Original song titles and artist names are retained.",
        "", "## Source rows", "", SOURCE_HEADER,
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        *rows(source_part), "", "## Label rows", "", label_header,
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        *rows(label_part), "", "## End of catalog source", "",
    ])
    if SNAPSHOT.exists() and SNAPSHOT.read_text(encoding="utf-8") != content:
        raise ValueError("snapshot_already_exists_with_different_content")
    if not SNAPSHOT.exists():
        SNAPSHOT.write_text(content, encoding="utf-8")
    print("catalog_snapshot=passed source_rows=35 label_rows=35")


if __name__ == "__main__":
    main()
