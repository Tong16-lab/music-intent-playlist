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

OLD_RANGE = '明确的音乐情绪／活跃度边界可在原 target 字段用 {"relation":"at_least|at_most","value":整数}，不要把范围改成单个档位。'
NEW_RANGE = 'target_valence、target_arousal 必须使用简写：精确档位写 "=N"，明确下限写 ">=N"，明确上限写 "<=N"，未提及写 null；不要把范围改成单个档位。'
OLD_PATH = '只有明确要求歌曲按顺序变化，trajectory 才用 {"type":"from_to","arousal":{"from":起点,"to":终点}} 或同结构的 valence 路径；终点必须与对应 target 精确值相同。'
NEW_PATH = '只有明确要求歌曲按顺序变化，trajectory 才用 "arousal:A->B" 或 "valence:A->B"；若两维都明确，可用 "valence:A->B;arousal:C->D"；终点必须与对应 target 的 "=N" 精确值相同。'


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
