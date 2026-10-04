"""Prompt-only v2 of the compact development request; v1 Schema is unchanged."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from compact_dev_request import build_candidate_request, load_versioned_format

ROOT = Path(__file__).resolve().parents[1]
VERSION = "compact-dev-v2"
PROMPT_FILE = ROOT / "data" / "COMPACT_DEV_PROMPT_v2.txt"

# The v2 prompt consists only of these generic additions to v1. No case text,
# approved answer, new dimension, or changed format instruction appears here.
ADDITIONS = (
    (
        "Use null for unsupported fields, and use null for the corresponding items in evidence.",
        "Use null for unsupported fields, and use null for the corresponding items in evidence. Search field by field for direct evidence; do not guess unmentioned values just to fill the object.",
    ),
    (
        "Events or scenes themselves do not automatically generate emotional values.",
        "Events or scenarios themselves do not automatically generate emotional values. First distinguish the user's current state, use case, and the songs they want to hear; scenarios like bedtime or commuting cannot support specific levels for current_* or target_*. Only fill in current_* when the user's state is explicitly described, and only fill in target_* when music expression is explicitly requested.",
    ),
    (
        "Do not change the range to a single level.",
        "Do not change the range to a single level. Write =N only when it happens to be a specific level; write >=N or <=N for at least or at most a level respectively, and do not treat boundaries as exact targets.",
    ),
    (
        "The end point must be identical to the \"=N\" exact value of the corresponding target.",
        "The end point must be identical to the \"=N\" exact value of the corresponding target. If the original sentence does not support consistent end points and targets, path endpoints or target values must not be fabricated.",
    ),
    (
        "Requirements that can be expressed via emotion, arousal, or melody dimensions should not be redundantly listed in constraints.",
        "Requirements that can be expressed via emotion, arousal, or melody dimensions should not be redundantly listed in constraints. First check whether existing emotion, arousal, melodic surprise, and identifiable melody tags can reliably express this preference; if they can, do not list it as an unsupported condition. Scenarios, background uses, and expected psychological effects are not hard constraints on song attributes by themselves. Only song attribute constraints that are explicitly requested and cannot be reliably verified by existing song library tags should be listed in constraints; their evidence must retain negation, degree, and target, capturing the complete contiguous phrase expressing that constraint in the original sentence rather than just extracting keywords.",
    ),
)


def expected_prompt_v2(v1_prompt: str) -> str:
    result = v1_prompt
    for old, new in ADDITIONS:
        if result.count(old) != 1:
            raise ValueError("v1_prompt_anchor_mismatch")
        result = result.replace(old, new)
    return result


def load_v2_format() -> tuple[str, dict[str, Any], dict[str, str]]:
    v1_prompt, schema, v1_digests = load_versioned_format()
    v2_prompt = PROMPT_FILE.read_text(encoding="utf-8")
    if v2_prompt != expected_prompt_v2(v1_prompt):
        raise ValueError("v2_prompt_snapshot_mismatch")
    return v2_prompt, schema, {
        "prompt_sha256": hashlib.sha256(v2_prompt.encode("utf-8")).hexdigest(),
        "schema_sha256": v1_digests["schema_sha256"],
        "v1_prompt_sha256": v1_digests["prompt_sha256"],
    }


def build_v2_request(utterance: str, model: str, prompt: str,
                     schema: dict[str, Any]) -> dict[str, Any]:
    return build_candidate_request(utterance, model, prompt, schema)
