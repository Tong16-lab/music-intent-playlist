"""Human-readable, link-only results backed by reviewed song labels."""

from __future__ import annotations

from typing import Any

from .intent import EVIDENCE_FIELDS, validate_intent
from .recommender import select_tracks


def _card(utterance: str, *, target_valence: Any = None, target_arousal: Any = None,
          target_melodic_surprise: Any = None, requires_melody_present: Any = None,
          trajectory: Any = "none", evidence: dict[str, str] | None = None,
          constraints: list[dict[str, str]] | None = None) -> tuple[str, dict[str, Any]]:
    card = {name: None for name in EVIDENCE_FIELDS if name != "trajectory"}
    card.update({"target_valence": target_valence, "target_arousal": target_arousal,
                 "target_melodic_surprise": target_melodic_surprise,
                 "requires_melody_present": requires_melody_present,
                 "trajectory": trajectory, "evidence": {name: (evidence or {}).get(name)
                                                       for name in EVIDENCE_FIELDS},
                 "constraints": constraints or []})
    return utterance, validate_intent(card, utterance)


def fixed_samples() -> dict[str, tuple[str, dict[str, Any]]]:
    """Prewritten cards for selection demonstration; these are not model predictions."""
    return {
        "explore": _card("Play some music"),
        "calm": _card("I want to listen to quiet and soothing songs", target_arousal=1,
                      trajectory="single_target", evidence={"target_arousal": "quiet and soothing"}),
        "path": _card("Play an energetic song first, then gradually quiet down", target_arousal=1,
                      trajectory={"type": "from_to", "arousal": {"from": 3, "to": 1}},
                      evidence={"target_arousal": "quiet down", "trajectory": "Play an energetic song first, then gradually quiet down"}),
        "melody": _card("Want to hear a melody that is clear and has surprising progressions", target_melodic_surprise=3,
                        requires_melody_present=True,
                        evidence={"target_melodic_surprise": "surprising progressions",
                                  "requires_melody_present": "melody that is clear"}),
        "unsupported": _card("No English songs", constraints=[{
            "evidence": "No English songs", "classification": "unsupported_constraint",
            "polarity": "exclude"}]),
    }


def recommend(intent: dict[str, Any], catalog: list[dict[str, Any]]) -> dict[str, Any]:
    result = select_tracks(intent, catalog)
    by_id = {row["track_id"]: row for row in catalog}
    for item in result["tracks"]:
        song = by_id[item["track_id"]]
        item.update({"title": song["title"], "artist": song["artist"],
                     "source_url": song["source_url"], "valence": song["valence"],
                     "arousal": song["arousal"], "melody_present": song["melody_present"],
                     "melodic_surprise": song["melodic_surprise"],
                     "surprise_evidence": song.get("surprise_evidence", "")})
    return result


def render_result(result: dict[str, Any], intent: dict[str, Any],
                  *, heading: str | None = None, heading_level: int = 2,
                  language: str = "zh") -> str:
    if language == "en":
        return _render_result_en(result, intent, heading=heading, heading_level=heading_level)
    if language != "zh":
        raise ValueError("unsupported_display_language")
    lines = [f"{'#' * heading_level} {heading or 'Recommended Results'}", "",
             f"Status: `{result['status']}`."]
    if result["status"] == "cannot_guarantee_constraint":
        lines.append("Current music library tags cannot reliably guarantee hard conditions in the original sentence; no song selected.")
    elif result["status"] == "catalog_not_ready":
        lines.append("No available songs passed the identity and tag verification; no songs selected.")
    elif result["status"] == "insufficient_catalog":
        lines.append(f"Fewer than three songs meet the current hard conditions; only found {len(result['tracks'])}, not supplementing.")
    elif result.get("mode") == "exploration":
        lines.append("No executable song target specified; exploring by verified tag combinations.")
    else:
        lines.append("The following matches are based on verified song tags and clear musical goals.")
    if result["tracks"]:
        lines.extend(["", "| Order | Song (Jamendo Original Page) | Artist | Verified Tags | Basis |",
                      "| ---: | --- | --- | --- | --- |"])
    listening_hints = []
    for index, item in enumerate(result["tracks"], 1):
        labels = (f"valence={item['valence']};arousal={item['arousal']};"
                  f"melody_present={item['melody_present']};"
                  f"melodic_surprise={item['melodic_surprise']}")
        reasons = [f"{name}={value}" for name, value in item["used_labels"].items()]
        if intent["requires_melody_present"] is True:
            reasons.append("distinguishable_melody=yes")
        if isinstance(intent["trajectory"], dict):
            reasons.append(f"Song sequence path, track {index} in playlist")
        reason = ";".join(reasons) if reasons else "Checked tags; explored options"
        title = item["title"].replace("|", "\\|").replace("[", "\\[").replace("]", "\\]")
        artist = item["artist"].replace("|", "\\|")
        lines.append(f"| {index} | [{title}]({item['source_url']}) | {artist} | {labels} | {reason} |")
        if intent["target_melodic_surprise"] is not None and item["surprise_evidence"]:
            listening_hints.append(f"- Track {index} ({item['track_id']}): {item['surprise_evidence']}")
    if listening_hints:
        lines.extend(["", "Audition tips (author's original notes):", "", *listening_hints])
    lines.extend(["", "Tag matching and rule passing do not mean real people like these songs; audio licensing has not been verified, and this page only provides external links.", ""])
    return "\n".join(lines)


def _render_result_en(result: dict[str, Any], intent: dict[str, Any],
                      *, heading: str | None, heading_level: int) -> str:
    """Translate presentation only; retain the validated card and selection unchanged."""
    lines = [f"{'#' * heading_level} {heading or 'Recommendation result'}", "",
             f"Status: `{result['status']}`."]
    if result["status"] == "cannot_guarantee_constraint":
        lines.append("The reviewed catalog cannot reliably guarantee a requested song property; no tracks selected.")
    elif result["status"] == "catalog_not_ready":
        lines.append("No tracks have passed identity and label review; no tracks selected.")
    elif result["status"] == "insufficient_catalog":
        lines.append(f"Only {len(result['tracks'])} eligible tracks were found; the list is not padded to three.")
    elif result.get("mode") == "exploration":
        lines.append("No actionable song target was specified; explore varied combinations of reviewed labels.")
    else:
        lines.append("Track selection uses reviewed song labels and explicit music targets.")
    if result["tracks"]:
        lines.extend(["", "| Position | Track (Jamendo page) | Artist | Reviewed labels | Selection basis |",
                      "| ---: | --- | --- | --- | --- |"])
    for index, item in enumerate(result["tracks"], 1):
        labels = (f"valence={item['valence']}; arousal={item['arousal']}; "
                  f"melody_present={item['melody_present']}; "
                  f"melodic_surprise={item['melodic_surprise']}")
        reasons = [f"{name}={value}" for name, value in item["used_labels"].items()]
        if intent["requires_melody_present"] is True:
            reasons.append("identifiable melody=yes")
        if isinstance(intent["trajectory"], dict):
            reasons.append(f"song-path position {index}")
        reason = "; ".join(reasons) if reasons else "reviewed labels; exploration selection"
        title = item["title"].replace("|", "\\|").replace("[", "\\[").replace("]", "\\]")
        artist = item["artist"].replace("|", "\\|")
        lines.append(f"| {index} | [{title}]({item['source_url']}) | {artist} | {labels} | {reason} |")
    if intent["target_melodic_surprise"] is not None and any(
            item.get("surprise_evidence") for item in result["tracks"]):
        lines.extend(["", "English translations of the listening notes appear in data/CATALOG_LABELS_EN.md."])
    lines.extend(["", "A label match does not establish listener enjoyment. Audio-use permissions have not been verified; only external links are shown.", ""])
    return "\n".join(lines)
