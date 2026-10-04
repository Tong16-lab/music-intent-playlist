"""Export provisional synthetic intent answers from the supplied project specification."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT.parent / "PE6201_Music_Data_Licensing_and_Evaluation_Fillable.md"
DATA = ROOT / "data"


def ev(cv=None, ca=None, tv=None, ta=None, ms=None, tr=None):
    return dict(zip(("current_valence", "current_arousal", "target_valence", "target_arousal", "target_melodic_surprise", "trajectory"), (cv, ca, tv, ta, ms, tr)))


# Each phrase is copied verbatim from its own synthetic sentence. These remain
# provisional draft answers until the author approves every test row.
EVIDENCE = {
    "dev_001": ev("脑子嗡嗡的", "脑子嗡嗡的", "缓缓", "安静的让我缓缓", "别太花里胡哨的", "想听点安静的让我缓缓"),
    "dev_002": ev("够烦了", tv="心情亮堂点", ta="精神一点", tr="来点让人精神一点、心情亮堂点的"),
    "dev_003": ev(tv="放空一下", ta="放空一下", tr="想放空一下"),
    "dev_004": ev(cv="心里有点堵", tv="丧一会儿", tr="想听点能陪我一起丧一会儿的"),
    "dev_005": ev(ta="有点带劲的", tr="想要有点带劲的"),
    "dev_006": ev(ms="没想到的"),
    "dev_007": ev("心慌得不行", "心慌得不行", "踏实下来", "慢慢踏实下来", tr="想让自己慢慢踏实下来"),
    "dev_008": ev(cv="心情特别好", tv="欢快的", tr="想听点欢快的"),
    "dev_009": ev(),
    "dev_010": ev(ta="特别带劲的", ms="出乎意料的地方", tr="想听特别带劲的"),
    "dev_011": ev("有点烦", "先来点猛的", "慢慢软下来", "慢慢软下来", tr="先来点猛的发泄一下，然后慢慢软下来"),
    "dev_012": ev(tv="不悲不喜的", tr="随便来点不悲不喜的背景音乐"),
    "test_001": ev("心里堵得慌", "心里堵得慌", "静下来", "慢慢静下来", tr="想听点能让我慢慢静下来的"),
    "test_002": ev(tv="暖暖的", ta="轻松的", tr="想听点暖暖的、轻松的"),
    "test_003": ev(),
    "test_004": ev(cv="压力特别大", tv="治愈的", ms="别搞得太复杂", tr="想听点治愈的"),
    "test_005": ev(ms="别一听就能猜到后面"),
    "test_006": ev(tv="忧伤的", tr="想听点忧伤的"),
    "test_007": ev(ta="提神的", tr="来点提神的"),
    "test_008": ev(tv="轻快的", ta="轻快的", tr="想放点轻快的"),
    "test_009": ev(),
    "test_010": ev(cv="刚失恋", tv="慢慢好起来", tr="先听点难过的，哭一哭，然后慢慢好起来"),
    "test_011": ev(ta="劲儿大的", ms="别太绕", tr="想听点劲儿大的"),
    "test_012": ev(),
    "test_013": ev(cv="太开心了", tv="更嗨的", ta="更嗨的", tr="想听点更嗨的"),
    "test_014": ev(cv="有点焦虑", tv="稳稳的", ta="稳稳的", ms="别忽然来个大变化", tr="想听点稳稳的"),
    "test_015": ev(ms="新鲜感"),
    "test_016": ev(tv="温柔的感觉", ta="安静的", tr="想听点安静的"),
    "test_017": ev(cv="烦死了烦死了", ta="吵吵闹闹的发泄一下", tr="想听点吵吵闹闹的发泄一下"),
    "test_018": ev(),
    "test_019": ev(ca="紧张刺激的", tv="放松下来", ta="放松下来", tr="先来点紧张刺激的，后面慢慢让我放松下来"),
    "test_020": ev(tv="不悲不喜的", tr="想听点不悲不喜的"),
    "test_021": ev(ms="出乎意料的感觉", tr="想要点出乎意料的感觉"),
    "test_022": ev(cv="有点孤单", tr="想听点能陪着我的"),
    "test_023": ev(tv="有盼头的", tr="想听点让人觉得天亮了、有盼头的"),
    "test_024": ev(tv="别太悲", tr="别太悲，也别太闹"),
    "test_025": ev(ca="从软软的", tv="有精神", ta="变得有精神", tr="从软软的慢慢变得有精神"),
    "test_026": ev(),
    "test_027": ev(ms="小惊喜"),
    "test_028": ev(cv="终于考完了，整个人轻飘飘的", tv="开心的", tr="想听点放松又开心的"),
    "test_029": ev(cv="心情很低落", ta="安安静静", tr="就想安安静静待一会儿"),
    "test_030": ev(),
}

UNSUPPORTED = {
    "test_003": ["电子乐", "不要太吵", "别给我放土嗨歌"],
    "test_007": ["别放慢歌"],
    "test_009": ["别放有人唱词的"],
    "test_012": ["别放那种慢悠悠的抒情歌", "别放口水歌"],
    "test_015": ["别是土嗨歌那种"],
    "test_018": ["别放英文歌", "不想听土嗨歌"],
    "test_021": ["别太吵"],
    "test_022": ["能陪着我的"],
    "test_024": ["别太闹", "口水歌", "土嗨歌"],
    "test_026": ["没人唱的"],
}
UNSUPPORTED_NOTES = {
    "test_003": "电子乐是正向风格要求；音量与土嗨歌也无法由现有曲库保证。",
    "test_022": "陪伴效果属主观效果；请作者确认是否应列为不可保证条件。",
    "test_024": "别太悲可由 valence 处理；别太闹是否指音量需作者核对。",
}
AMBIGUITY_NOTES = {
    "test_021": "来源表将 trajectory 标为 single_target，但未给出可靠 arousal 目标。",
    "test_022": "来源表将 trajectory 标为 single_target，但目标情绪与唤醒度未说明。",
    "test_028": "来源表明确提示 expected_arousal 依据不足。",
}

FIELDS = [
    "case_id", "synthetic_role_id", "utterance", "split", "current_valence", "current_valence_evidence",
    "current_arousal", "current_arousal_evidence", "target_valence", "target_valence_evidence",
    "target_arousal", "target_arousal_evidence", "target_melodic_surprise", "target_melodic_surprise_evidence",
    "trajectory", "trajectory_evidence", "ambiguous", "ambiguity_note", "review_status",
]


def parse_source() -> list[list[str]]:
    text = SPEC.read_text(encoding="utf-8")
    section = text.split("## 5. AI 合成的找歌表达与意图标注", 1)[1].split("## 6. GitHub 仓库交付", 1)[0]
    rows = []
    for line in section.splitlines():
        if re.match(r"^\| (?:dev|test)_\d{3} \|", line):
            cells = [cell.strip() for cell in line.split("|")[1:-1]]
            if len(cells) != 8:
                raise ValueError("source_table_shape")
            rows.append(cells)
    return rows


def parse_state(text: str, key: str):
    match = re.search(rf"{key}=(neg|neutral|pos|未说明)", text)
    if not match:
        raise ValueError(f"missing_{key}")
    return {"neg": -1, "neutral": 0, "pos": 1, "未说明": None}[match.group(1)]


def parse_arousal(text: str) -> tuple[int | None, int | None]:
    if "高唤醒→低唤醒" in text or "高→低唤醒" in text or "先高唤醒后降低" in text:
        return 3, 1
    if "低→高唤醒" in text:
        return 1, 3
    match = re.search(r"expected_arousal=(低|中|高)", text)
    return None, {"低": 1, "中": 2, "高": 3}[match.group(1)] if match else None


def build_rows():
    source = parse_source()
    if len(source) != 42 or set(EVIDENCE) != {row[0] for row in source}:
        raise ValueError("case_count_or_evidence_map")
    answer_rows = {"dev": [], "test": []}
    unsupported_rows = []
    roles = {"dev": set(), "test": set()}
    for case_id, role, quote, split, states, path_arousal, melody, _reference in source:
        if split not in answer_rows or not case_id.startswith(split + "_"):
            raise ValueError("split_mismatch")
        roles[split].add(role)
        utterance = quote[1:-1] if quote.startswith('"') and quote.endswith('"') else quote
        current_arousal, target_arousal = parse_arousal(path_arousal)
        trajectory = "from_to" if path_arousal.startswith("from_A_to_B") else ("single_target" if path_arousal.startswith("single_target") else "none")
        if trajectory == "none" and not path_arousal.startswith("none"):
            raise ValueError(f"bad_trajectory_{case_id}")
        values = {
            "current_valence": parse_state(states, "current_state"),
            "current_arousal": current_arousal,
            "target_valence": parse_state(states, "target_state"),
            "target_arousal": target_arousal,
            "target_melodic_surprise": {"low": 1, "medium": 2, "high": 3, "未说明": None}[melody],
            "trajectory": trajectory,
        }
        evidence = EVIDENCE[case_id]
        row = {"case_id": case_id, "synthetic_role_id": role, "utterance": utterance, "split": split}
        for field, value in values.items():
            phrase = evidence[field]
            needs_phrase = value is not None and value != "none"
            if needs_phrase != bool(phrase) or (phrase and phrase not in utterance):
                raise ValueError(f"evidence_mismatch_{case_id}_{field}")
            row[field] = "" if value is None else value
            row[f"{field}_evidence"] = phrase or ""
        row["ambiguous"] = "true" if case_id in AMBIGUITY_NOTES else "false"
        row["ambiguity_note"] = AMBIGUITY_NOTES.get(case_id, "")
        row["review_status"] = "needs_author_review"
        answer_rows[split].append(row)
        if split == "test":
            phrases = UNSUPPORTED.get(case_id, [])
            if any(phrase not in utterance for phrase in phrases):
                raise ValueError(f"unsupported_phrase_not_in_sentence_{case_id}")
            unsupported_rows.append({
                "case_id": case_id, "utterance": utterance,
                "unsupported_condition_phrases": json.dumps(phrases, ensure_ascii=False),
                "expected_cannot_guarantee_constraint": "true" if phrases else "false",
                "draft_note": UNSUPPORTED_NOTES.get(case_id, ""),
                "review_status": "needs_author_review",
            })
    if len(answer_rows["dev"]) != 12 or len(answer_rows["test"]) != 30 or len(unsupported_rows) != 30:
        raise ValueError("split_counts")
    if roles["dev"] & roles["test"]:
        raise ValueError("role_leakage")
    return answer_rows, unsupported_rows


def write_new(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    answers, unsupported = build_rows()
    DATA.mkdir(exist_ok=True)
    write_new(DATA / "synthetic_intents_dev.csv", FIELDS, answers["dev"])
    write_new(DATA / "synthetic_intents_test.csv", FIELDS, answers["test"])
    write_new(DATA / "unsupported_conditions_test.csv", [
        "case_id", "utterance", "unsupported_condition_phrases",
        "expected_cannot_guarantee_constraint", "draft_note", "review_status",
    ], unsupported)
    print("Exported provisional drafts: dev=12 test=30 unsupported=30; no freeze recorded")


if __name__ == "__main__":
    main()
