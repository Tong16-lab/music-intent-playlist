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
    ("current_valence", "当前情绪"),
    ("current_arousal", "当前唤醒度"),
    ("target_valence", "想听的情绪"),
    ("target_arousal", "想听的活跃度"),
    ("target_melodic_surprise", "旋律意外感"),
)
VALUE_LABELS = {
    "current_valence": {"-1": "偏负", "0": "中性", "1": "偏正"},
    "target_valence": {"-1": "偏负", "0": "中性", "1": "偏正"},
    "current_arousal": {"1": "低", "2": "中", "3": "高"},
    "target_arousal": {"1": "低", "2": "中", "3": "高"},
    "target_melodic_surprise": {"1": "低", "2": "中", "3": "高"},
}
TRAJECTORY_LABELS = {
    "none": "没有明确音乐顺序",
    "single_target": "单一目标",
    "from_to": "明确的先后变化",
}


def field_text(row: dict[str, str], evidence: dict[str, str], field: str) -> str:
    value = row[field]
    if not value:
        return "未说明"
    if value.startswith("{"):
        rule = json.loads(value)
        relation = {"at_most": "不高于", "at_least": "不低于"}[rule["relation"]]
        level = str(rule["value"])
        detail = f"{relation} {level}（{VALUE_LABELS[field][level]}为边界，不是精确目标）"
    else:
        detail = f"{value}（{VALUE_LABELS[field][value]}）"
    return f"{detail}；证据：“{evidence[field]}”"


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
        lines.append(f"- {label}：{field_text(row, evidence, field)}")
    if row["requires_melody_present"] == "true":
        lines.append(
            "- 明确要求可辨旋律：是；证据：“"
            + evidence["requires_melody_present"]
            + "”"
        )
    else:
        lines.append("- 明确要求可辨旋律：未说明")
    trajectory = row["trajectory"]
    if trajectory.startswith("{"):
        path = json.loads(trajectory)
        levels = path["arousal"]
        path_label = path["type"]
        sequence = f"歌曲活跃度从 {levels['from']} 逐渐到 {levels['to']}"
    else:
        path_label = trajectory
        sequence = TRAJECTORY_LABELS[trajectory]
    if path_label != "none":
        sequence += f"；证据：“{evidence['trajectory']}”"
    lines.append(f"- 歌单路径：{path_label}（{sequence}）")
    lines.append(
        "- 无法保证的明确条件："
        + ("；".join(f"“{phrase}”" for phrase in unsupported) if unsupported else "无")
    )
    if row["other_request_or_note"]:
        lines.append(f"- 标注说明：{row['other_request_or_note']}")
    if row["ambiguous"] == "true":
        lines.append("- 待裁定：是；暂不能直接当作完整、唯一的整卡金标准。")
    status = {"approved": "作者已核对", "needs_author_review": "待作者核对"}[row["review_status"]]
    lines += [f"- 审核状态：{status}", ""]
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
        "# 用户表达与意图标注 V2（作者已核对，正式测试已完成）",
        "",
        "本页由 [V2 标注表](user_intents_v2_review.tsv) 机械转换；保留原有 42 条表达示例（12 条开发、30 条测试），不是从受访者收集的原话。作者已核对这些 V2 标注，现已迁移到正式 CSV；判定规则见 [V2 说明](USER_INTENT_ANNOTATION_V2_README.md)。冻结记录见 [test_set_freeze.json](test_set_freeze.json)，完成的结果见 [第二次正式评估](../reports/formal_run_02/EVALUATION_EN.md)。",
        "",
        "空白字段显示为“未说明”；每个非空字段后面列出原句中的证据。可辨旋律要求是六个核心意图字段之外的独立字段。42 条记录均已由作者核对。",
        "",
    ]
    for split, title in (("dev", "开发样例（12 条）"), ("test", "测试样例（30 条）")):
        parts += [f"## {title}", ""]
        parts.extend(render_case(row) for row in rows if row["split"] == split)
    DESTINATION.write_text("\n".join(parts).rstrip() + "\n", encoding="utf-8")
    print(f"created={DESTINATION} cases={len(rows)}")


if __name__ == "__main__":
    main()
