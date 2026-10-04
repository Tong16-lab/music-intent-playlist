"""Deterministic selection over verified catalog rows; no audio or title inference."""

from __future__ import annotations

import math
from typing import Any

from .intent import route_status

IDENTITY_OK = {"matched", "minor_spelling_variant", "artist_variant_confirmed"}
WEIGHTS = {"valence": 0.35, "arousal": 0.35, "melodic_surprise": 0.30}
SPAN = {"valence": 2, "arousal": 2, "melodic_surprise": 2}


def known_int(value: Any, allowed: set[int]) -> int | None:
    if type(value) is int and value in allowed:
        return value
    if isinstance(value, str) and value.lstrip("-").isdigit():
        parsed = int(value)
        return parsed if parsed in allowed else None
    return None


def path_target(intent: dict[str, Any], dimension: str, position: int) -> float | None:
    path = intent["trajectory"]
    if not isinstance(path, dict) or dimension not in path:
        return None
    start, end = path[dimension]["from"], path[dimension]["to"]
    return start + (end - start) * position / 2


def matches_hard(track: dict[str, Any], intent: dict[str, Any], position: int) -> bool:
    if intent["requires_melody_present"] is True and track.get("melody_present") != "yes":
        return False
    for dimension, domain in (("valence", {-1, 0, 1}), ("arousal", {1, 2, 3})):
        value = known_int(track.get(dimension), domain)
        target = intent[f"target_{dimension}"]
        if isinstance(target, dict):
            if value is None or (target["relation"] == "at_least" and value < target["value"]):
                return False
            if value is None or (target["relation"] == "at_most" and value > target["value"]):
                return False
        path_value = path_target(intent, dimension, position)
        if path_value is not None and (value is None or value not in {math.floor(path_value), math.ceil(path_value)}):
            return False
    for dimension, domain in (("valence", {-1, 0, 1}), ("arousal", {1, 2, 3}),
                              ("melodic_surprise", {1, 2, 3})):
        target = intent[f"target_{dimension}"]
        if target is not None and known_int(track.get(dimension), domain) is None:
            return False
    return True


def score_track(track: dict[str, Any], intent: dict[str, Any], position: int) -> tuple[float, dict[str, Any]]:
    contributions: dict[str, float] = {}
    used: dict[str, Any] = {}
    for dimension, domain in (("valence", {-1, 0, 1}), ("arousal", {1, 2, 3}),
                              ("melodic_surprise", {1, 2, 3})):
        target = path_target(intent, dimension, position)
        if target is None:
            target = intent[f"target_{dimension}"]
        if target is None:
            continue
        song_value = known_int(track.get(dimension), domain)
        if song_value is None:
            raise ValueError("unknown_relevant_song_label")
        if isinstance(target, dict):
            affinity = 1.0  # matches_hard already enforced the range
        else:
            affinity = 1 - abs(song_value - target) / SPAN[dimension]
        contributions[dimension] = affinity * WEIGHTS[dimension]
        used[dimension] = song_value
    weight_total = sum(WEIGHTS[dimension] for dimension in contributions)
    return (sum(contributions.values()) / weight_total if weight_total else 0.0), used


def select_tracks(intent: dict[str, Any], tracks: list[dict[str, Any]], count: int = 3) -> dict[str, Any]:
    if route_status(intent) == "cannot_guarantee_constraint":
        return {"status": "cannot_guarantee_constraint", "tracks": []}
    catalog = [track for track in tracks if track.get("link_identity_status") in IDENTITY_OK
               and track.get("label_status") == "verified" and track.get("track_id")
               and track.get("artist")]
    if not catalog:
        return {"status": "catalog_not_ready", "tracks": []}
    selected: list[dict[str, Any]] = []
    used_ids: set[str] = set()
    used_artists: set[str] = set()
    used_signatures: set[tuple[Any, ...]] = set()
    for position in range(count):
        candidates = [track for track in catalog if track["track_id"] not in used_ids
                      and matches_hard(track, intent, position)]
        if not candidates:
            return {"status": "insufficient_catalog", "tracks": selected}
        scored = [(score_track(track, intent, position), track) for track in candidates]
        # Diversity only breaks equal-score ties; never displace a closer explicit match.
        scored.sort(key=lambda pair: (-pair[0][0], pair[1]["artist"] in used_artists,
                                      tuple(pair[1].get(name) for name in (
                                          "valence", "arousal", "melody_present",
                                          "melodic_surprise")) in used_signatures,
                                      pair[1]["track_id"]))
        (score, used), chosen = scored[0]
        selected.append({"track_id": chosen["track_id"], "artist": chosen["artist"],
                         "score": round(score, 6), "used_labels": used})
        used_ids.add(chosen["track_id"])
        used_artists.add(chosen["artist"])
        used_signatures.add(tuple(chosen.get(name) for name in (
            "valence", "arousal", "melody_present", "melodic_surprise")))
    return {"status": "ready", "tracks": selected,
            "mode": "exploration" if all(intent[f"target_{d}"] is None for d in WEIGHTS)
            and intent["requires_melody_present"] is None
            and not isinstance(intent["trajectory"], dict) else "matched"}
