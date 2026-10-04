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
        "没有依据的字段用 null，evidence 中对应项也用 null。",
        "没有依据的字段用 null，evidence 中对应项也用 null。逐字段查找直接证据；不要为了填满对象猜测未提及的值。",
    ),
    (
        "事件或场景本身不自动产生情绪值。",
        "事件或场景本身不自动产生情绪值。先区分本人当前状态、使用场景和想听的歌曲；睡前、通勤等场景本身不能支持 current_* 或 target_* 的具体档位。只有明确描述本人状态才填 current_*，只有明确要求音乐表达才填 target_*。",
    ),
    (
        "不要把范围改成单个档位。",
        "不要把范围改成单个档位。恰好某档才写 =N；至少、至多某档分别写 >=N、<=N，不能把边界当作精确目标。",
    ),
    (
        "终点必须与对应 target 的 \"=N\" 精确值相同。",
        "终点必须与对应 target 的 \"=N\" 精确值相同。若原句不支持一致的终点和目标，不得补造路径端点或目标值。",
    ),
    (
        "可由情绪、活跃度或旋律维度表达的要求不要重复列入 constraints。",
        "可由情绪、活跃度或旋律维度表达的要求不要重复列入 constraints。先检查现有情绪、活跃度、旋律意外感及可辨旋律标签能否可靠表达该偏好；能表达就不要列为不支持条件。场景、背景用途及期望心理效果本身不是歌曲属性硬限制。只有明确要求、且现有曲库标签无法可靠核验的歌曲属性限制才列入 constraints；其 evidence 保留否定、程度和对象，截取原句中表达该限制的完整连续短语，不只摘关键词。",
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
