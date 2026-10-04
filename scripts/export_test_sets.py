"""Historical exporter for the pre-V2 example-answer draft; not used for submission."""

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


# Each phrase was copied verbatim from its own example sentence. These remain
# provisional draft answers until the author approves every test row.
EVIDENCE = {
    "dev_001": ev("My brain is buzzing", "My brain is buzzing", "Slow down", "Quietly let me slow down", "Don't be too fancy", "I want to hear something quiet to let me slow down"),
    "dev_002": ev("Enough of this annoyance", tv="Brighten up the mood", ta="Cheer up a bit", tr="Bring me something that perks me up and brightens my mood"),
    "dev_003": ev(tv="daydream a bit", ta="daydream a bit", tr="want to daydream a bit"),
    "dev_004": ev(cv="Feeling a bit stuffy inside", tv="Be gloomy for a while", tr="Want to listen to something that can accompany me in being gloomy for a while"),
    "dev_005": ev(ta="a bit exciting", tr="wanting something a bit exciting"),
    "dev_006": ev(ms="unexpected"),
    "dev_007": ev("heart pounding like crazy", "heart pounding like crazy", "feel at ease", "gradually feel at ease", tr="wanting to gradually feel at ease"),
    "dev_008": ev(cv="in a particularly good mood", tv="cheerful", tr="I want to listen to something cheerful"),
    "dev_009": ev(),
    "dev_010": ev(ta="super energetic", ms="unexpected place", tr="want to listen to something super energetic"),
    "dev_011": ev("a bit annoyed", "start with something intense", "slowly soften", "slowly soften", tr="start with something intense to vent, then slowly soften"),
    "dev_012": ev(tv="neither sad nor happy", tr="Just give me some background music that is neither sad nor happy"),
    "test_001": ev("I feel suffocated", "I feel suffocated", "calm down", "calm down slowly", tr="I want to listen to something that can help me calm down slowly"),
    "test_002": ev(tv="warm", ta="relaxing", tr="want to listen to something warm and relaxing"),
    "test_003": ev(),
    "test_004": ev(cv="Under a lot of pressure", tv="Healing", ms="Don't make it too complicated", tr="I want to listen to something healing"),
    "test_005": ev(ms="Don't make it so predictable right away"),
    "test_006": ev(tv="sad", tr="want to hear something sad"),
    "test_007": ev(ta="refreshing", tr="Bring something refreshing"),
    "test_008": ev(tv="upbeat", ta="upbeat", tr="I want to play something upbeat"),
    "test_009": ev(),
    "test_010": ev(cv="Just went through a breakup", tv="Slowly getting better", tr="First listen to something sad, cry it out, and then slowly get better"),
    "test_011": ev(ta="punchy", ms="don't beat around the bush", tr="I want to hear something punchy"),
    "test_012": ev(),
    "test_013": ev(cv="So happy", tv="Even more upbeat", ta="Even more upbeat", tr="I want to hear something more upbeat"),
    "test_014": ev(cv="feeling a bit anxious", tv="steady", ta="steady", ms="don't suddenly bring a big change", tr="want to listen to something steady"),
    "test_015": ev(ms="novelty"),
    "test_016": ev(tv="Gentle feeling", ta="Quiet", tr="I want to listen to something quiet"),
    "test_017": ev(cv="So annoying so annoying", ta="Make a noisy vent", tr="I want to listen to something noisy to vent"),
    "test_018": ev(),
    "test_019": ev(ca="nervous and exciting", tv="relax", ta="relax", tr="First give me something nervous and exciting, and then let me relax slowly"),
    "test_020": ev(tv="neither sad nor joyful", tr="I want to hear something neither sad nor joyful"),
    "test_021": ev(ms="Unexpected feeling", tr="Want a bit of an unexpected feeling"),
    "test_022": ev(cv="A bit lonely", tr="Want to listen to something that can accompany me"),
    "test_023": ev(tv="something to look forward to", tr="I want to hear something that makes people feel like dawn is breaking and gives them something to look forward to"),
    "test_024": ev(tv="Don't be too sad", tr="Don't be too sad, and don't make a fuss"),
    "test_025": ev(ca="From soft", tv="energetic", ta="becomes energetic", tr="Slowly changing from soft to energetic"),
    "test_026": ev(),
    "test_027": ev(ms="little surprise"),
    "test_028": ev(cv="Finally finished exams, feeling light as a feather", tv="happy", tr="Want to listen to something relaxing and happy"),
    "test_029": ev(cv="feeling very down", ta="quietly", tr="just want to stay quietly for a while"),
    "test_030": ev(),
}

UNSUPPORTED = {
    "test_003": ["electronic music", "not too noisy", "don't play cheesy club music for me"],
    "test_007": ["Don't play slow songs"],
    "test_009": ["Don't play anything with vocals"],
    "test_012": ["Don't play those slow lyrical songs", "Don't play cheesy pop songs"],
    "test_015": ["Don't be that kind of tacky cheesy techno song"],
    "test_018": ["Don't play English songs", "Don't want to listen to cheesy dance music"],
    "test_021": ["Don't be too noisy"],
    "test_022": ["You can stay with me"],
    "test_024": ["Don't make a fuss", "spittle song", "tuhai song"],
    "test_026": ["nobody sings"],
}
UNSUPPORTED_NOTES = {
    "test_003": "Electronic music is a positive style requirement; neither the volume nor the cheesy upbeat tracks can be guaranteed by the existing music library.",
    "test_022": "The companionship effect is a subjective effect; please have the author confirm whether it should be classified as an unguaranteeable condition.",
    "test_024": "\"Don't be too sad\" can be handled by valence; whether \"Don't be too noisy\" refers to volume needs to be checked by the author.",
}
AMBIGUITY_NOTES = {
    "test_021": "The source table marks trajectory as single_target, but does not provide a reliable arousal target.",
    "test_022": "Source table marks trajectory as single_target, but target emotion and arousal are not specified.",
    "test_028": "The source table explicitly indicates that expected_arousal lacks sufficient basis.",
}

FIELDS = [
    "case_id", "synthetic_role_id", "utterance", "split", "current_valence", "current_valence_evidence",
    "current_arousal", "current_arousal_evidence", "target_valence", "target_valence_evidence",
    "target_arousal", "target_arousal_evidence", "target_melodic_surprise", "target_melodic_surprise_evidence",
    "trajectory", "trajectory_evidence", "ambiguous", "ambiguity_note", "review_status",
]


def parse_source() -> list[list[str]]:
    text = SPEC.read_text(encoding="utf-8")
    section = re.split(r"^## 5\. ", text, maxsplit=1, flags=re.MULTILINE)[1]
    section = re.split(r"^## 6\. ", section, maxsplit=1, flags=re.MULTILINE)[0]
    rows = []
    for line in section.splitlines():
        if re.match(r"^\| (?:dev|test)_\d{3} \|", line):
            cells = [cell.strip() for cell in line.split("|")[1:-1]]
            if len(cells) != 8:
                raise ValueError("source_table_shape")
            rows.append(cells)
    return rows


def parse_state(text: str, key: str):
    match = re.search(rf"{key}=(neg|neutral|pos|not specified)", text)
    if not match:
        raise ValueError(f"missing_{key}")
    return {"neg": -1, "neutral": 0, "pos": 1, "not specified": None}[match.group(1)]


def parse_arousal(text: str) -> tuple[int | None, int | None]:
    if "high arousal → low arousal" in text or "high → low arousal" in text or "first high arousal then decreasing" in text:
        return 3, 1
    if "low→high arousal" in text:
        return 1, 3
    match = re.search(r"expected_arousal=(low|medium|high)", text)
    return None, {"Low": 1, "Medium": 2, "High": 3}[match.group(1)] if match else None


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
            "target_melodic_surprise": {"low": 1, "medium": 2, "high": 3, "unspecified": None}[melody],
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
