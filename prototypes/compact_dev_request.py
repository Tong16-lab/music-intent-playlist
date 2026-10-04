"""Versioned request for the independent compact-format development comparison."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from music_intent.intent import SYSTEM_PROMPT  # noqa: E402
from music_intent.openrouter_client import build_request  # noqa: E402
from compact_intent_format import candidate_schema  # noqa: E402

VERSION = "compact-dev-v1"
PROMPT_FILE = ROOT / "data" / "COMPACT_DEV_PROMPT_v1.txt"
SCHEMA_FILE = ROOT / "data" / "COMPACT_DEV_SCHEMA_v1.json"

OLD_RANGE = 'Clear music mood/arousal boundaries can be specified in the original target field using {"relation":"at_least|at_most","value":integer}, do not change the range to a single tier.'
NEW_RANGE = 'target_valence and target_arousal must use shorthand notation: write exact tiers as "=N", clear lower bounds as ">=N", clear upper bounds as "<=N", and use null if not mentioned; do not change ranges to a single tier.'
OLD_PATH = 'Only when the songs are explicitly requested to change in sequence, trajectory uses {"type":"from_to","arousal":{"from":start,"to":end}} or the same structure for valence paths; the end point must be identical to the corresponding target exact value.'
NEW_PATH = 'Only when songs are explicitly requested to change in sequence, trajectory uses "arousal:A->B" or "valence:A->B"; if both dimensions are explicit, "valence:A->B;arousal:C->D" can be used; the end point must be identical to the corresponding target "=N" exact value.'


def expected_prompt() -> str:
    if SYSTEM_PROMPT.count(OLD_RANGE) != 1 or SYSTEM_PROMPT.count(OLD_PATH) != 1:
        raise ValueError("formal_prompt_version_mismatch")
    return SYSTEM_PROMPT.replace(OLD_RANGE, NEW_RANGE).replace(OLD_PATH, NEW_PATH)


def load_versioned_format() -> tuple[str, dict[str, Any], dict[str, str]]:
    prompt = PROMPT_FILE.read_text(encoding="utf-8")
    schema_bytes = SCHEMA_FILE.read_bytes()
    schema = json.loads(schema_bytes)
    if prompt != expected_prompt() or schema != candidate_schema():
        raise ValueError("candidate_format_snapshot_mismatch")
    digests = {
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "schema_sha256": hashlib.sha256(schema_bytes).hexdigest(),
    }
    return prompt, schema, digests


def build_candidate_request(utterance: str, model: str,
                            prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
    request = build_request(utterance, model)
    request["messages"][0]["content"] = prompt
    request["response_format"]["json_schema"]["schema"] = schema
    return request
