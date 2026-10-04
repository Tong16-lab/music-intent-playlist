"""Offline post-freeze recommendation routing audit of released validated cards."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from freeze_test_set import verify_manifest  # noqa: E402
from music_intent.catalog import load_catalog  # noqa: E402
from music_intent.display import recommend  # noqa: E402
from music_intent.intent import InvalidIntent, validate_intent  # noqa: E402

PUBLIC_CARDS = ROOT / "reports/formal_run_02/validated_cards_for_audit.jsonl"
ANSWERS = ROOT / "data/synthetic_intents_test.csv"
JSON_REPORT = ROOT / "reports/formal_run_02/recommendation_audit.json"
MD_REPORT = ROOT / "reports/formal_run_02/recommendation_audit.md"


def audit(private_path: Path = PUBLIC_CARDS, answer_path: Path = ANSWERS,
          catalog_path: Path | None = None) -> dict:
    verify_manifest()
    catalog = load_catalog(catalog_path or ROOT / "data/catalog.csv")
    with answer_path.open(encoding="utf-8", newline="") as handle:
        answers = {row["case_id"]: row["utterance"] for row in csv.DictReader(handle)}
    if len(answers) != 30:
        raise ValueError("formal_answer_count_changed")
    rows = [json.loads(line) for line in private_path.read_text(encoding="utf-8").splitlines()]
    if len(rows) != 30 or {row.get("case_id") for row in rows} != set(answers):
        raise ValueError("released_card_count_or_id_mismatch")
    counts = Counter()
    for row in rows:
        card = row.get("converted_v2")
        if not row.get("intent_valid") or card is None:
            counts["invalid_intent_card"] += 1
            continue
        try:
            intent = validate_intent(card, answers[row["case_id"]])
        except InvalidIntent:
            counts["invalid_intent_card"] += 1
            continue
        result = recommend(intent, catalog)
        status = result["status"]
        if status == "ready" and len(result["tracks"]) != 3:
            raise ValueError("ready_without_three")
        counts[status] += 1
    return {"source_run": "formal_run_02", "kind": "post_freeze_recommendation_layer_audit",
            "input_cases": 30, "catalog_tracks": len(catalog),
            "counts": {name: counts[name] for name in (
                "ready", "cannot_guarantee_constraint", "insufficient_catalog",
                "catalog_not_ready", "invalid_intent_card")}}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Check existing audit without writing")
    args = parser.parse_args()
    try:
        result = audit()
        encoded = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        counts = result["counts"]
        markdown = "\n".join([
            "# 冻结后第二次正式运行：推荐层离线审计", "",
            "仅使用已保存的本机私有预测、冻结的原句和 35 首正式曲库；没有 API 调用。"
            "这是推荐流程与条件可满足性检查，不是预先完成的推荐质量或用户喜好评估。", "",
            "| 状态 | 数量 |", "| --- | ---: |",
            *[f"| `{name}` | {counts[name]}/30 |" for name in counts], "",
            "无效意图卡不参与推荐；`cannot_guarantee_constraint` 不选歌；曲库不足时不补足。"
            "模型意图判断成绩仍以本运行原始评估报告为准。", ""])
        for path, expected in ((JSON_REPORT, encoded), (MD_REPORT, markdown)):
            if path.exists() and path.read_text(encoding="utf-8") != expected:
                raise ValueError(f"audit_file_differs:{path.name}")
            if not args.check and not path.exists():
                path.write_text(expected, encoding="utf-8")
            if args.check and not path.exists():
                raise ValueError(f"audit_file_missing:{path.name}")
        print("recommendation_audit=passed " + " ".join(f"{k}={v}" for k, v in counts.items()))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"recommendation_audit=failed reason={error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
