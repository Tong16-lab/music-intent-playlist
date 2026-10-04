"""Author-gated V2 freeze and SHA-256 verification."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from review_test_answers import DATA, validate_all

MANIFEST = DATA / "test_set_freeze.json"
TEST_FILES = ("user_intents_v2_review.tsv", "synthetic_intents_test.csv", "unsupported_conditions_test.csv")
CONFIRMATION = "我确认冻结V2正式测试答案"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_manifest(data_dir: Path = DATA) -> None:
    manifest_path = data_dir / MANIFEST.name
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 2 or manifest.get("timezone") != "Asia/Singapore" or set(manifest.get("files", {})) != set(TEST_FILES):
        raise ValueError("bad_freeze_manifest")
    try:
        frozen_at = datetime.fromisoformat(manifest["frozen_at"])
    except (KeyError, TypeError, ValueError):
        raise ValueError("bad_freeze_timestamp") from None
    if frozen_at.utcoffset() is None or frozen_at.utcoffset().total_seconds() != 8 * 3600:
        raise ValueError("bad_freeze_timestamp")
    for name in TEST_FILES:
        if digest(data_dir / name) != manifest["files"][name]:
            raise ValueError(f"modified_after_freeze:{name}")
    validate_all(data_dir, approved=True)


def freeze(data_dir: Path = DATA) -> None:
    manifest_path = data_dir / MANIFEST.name
    if manifest_path.exists():
        raise ValueError("already_frozen")
    validate_all(data_dir, approved=True)
    if not sys.stdin.isatty():
        raise ValueError("interactive_author_confirmation_required")
    print("确认前请逐行核对 V2 正式答案。输入以下完整句子才会冻结：")
    print(CONFIRMATION)
    if input("确认：").strip() != CONFIRMATION:
        raise ValueError("author_confirmation_missing")
    manifest = {
        "schema_version": 2,
        "frozen_at": datetime.now(ZoneInfo("Asia/Singapore")).isoformat(timespec="seconds"),
        "timezone": "Asia/Singapore",
        "files": {name: digest(data_dir / name) for name in TEST_FILES},
    }
    with manifest_path.open("x", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    verify_manifest(data_dir)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("check", "freeze", "verify"))
    args = parser.parse_args()
    try:
        if args.command == "check":
            summary = validate_all()
            print("review_check=passed " + " ".join(f"{k}={v}" for k, v in summary.items()))
        elif args.command == "freeze":
            freeze()
            print(f"freeze=complete manifest={MANIFEST}")
        else:
            verify_manifest()
            print("freeze_verification=passed")
    except (ValueError, FileNotFoundError, json.JSONDecodeError) as error:
        print(f"{args.command}=failed reason={error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
