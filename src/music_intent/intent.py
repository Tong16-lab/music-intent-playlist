"""V2 structured intent schema and strict source-evidence validation."""

from __future__ import annotations

from typing import Any

CORE_FIELDS = (
    "current_valence", "current_arousal", "target_valence", "target_arousal",
    "target_melodic_surprise", "trajectory",
)
EVIDENCE_FIELDS = (*CORE_FIELDS, "requires_melody_present")
DOMAINS = {
    "current_valence": {-1, 0, 1}, "current_arousal": {1, 2, 3},
    "target_valence": {-1, 0, 1}, "target_arousal": {1, 2, 3},
    "target_melodic_surprise": {1, 2, 3},
}


def nullable_integer(options: set[int], description: str) -> dict[str, Any]:
    """Wire type only; validate_intent still enforces the numeric domain."""
    return {"type": ["integer", "null"], "description": description}


def target_schema(options: set[int], description: str) -> dict[str, Any]:
    return {
        "description": description,
        "anyOf": [
            nullable_integer(options, "Exact value or null when absent"),
            {"type": "object", "additionalProperties": False,
             "required": ["relation", "value"],
             "properties": {
                 "relation": {"type": "string", "enum": ["at_least", "at_most"]},
                 "value": {"type": "integer", "enum": sorted(options)},
             }},
        ],
    }


def response_schema() -> dict[str, Any]:
    def path(values: set[int]) -> dict[str, Any]:
        return {
            "type": "object", "additionalProperties": False,
            "required": ["from", "to"],
            "properties": {"from": {"type": "integer", "enum": sorted(values)},
                           "to": {"type": "integer", "enum": sorted(values)}},
        }
    return {
        "type": "object", "additionalProperties": False,
        "required": [*CORE_FIELDS, "requires_melody_present", "evidence", "constraints"],
        "properties": {
            "current_valence": nullable_integer(DOMAINS["current_valence"], "Current human emotion only, not first-song target"),
            "current_arousal": nullable_integer(DOMAINS["current_arousal"], "Current human activation only"),
            "target_valence": target_schema(DOMAINS["target_valence"], "Requested music emotion; range when an explicit bound is stated"),
            "target_arousal": target_schema(DOMAINS["target_arousal"], "Requested music activation; range when an explicit bound is stated"),
            "target_melodic_surprise": nullable_integer(DOMAINS["target_melodic_surprise"], "Requested melodic surprise"),
            "requires_melody_present": {"type": ["boolean", "null"],
                                         "description": "True only for an explicit request for a discernible melody; otherwise null"},
            "trajectory": {"description": "Music sequence, not change in the listener's own state", "anyOf": [
                {"type": "string", "enum": ["single_target", "none"]},
                {"type": "object", "additionalProperties": False, "required": ["type"],
                 "properties": {"type": {"type": "string", "enum": ["from_to"]},
                                "valence": path(DOMAINS["target_valence"]),
                                "arousal": path(DOMAINS["target_arousal"])}},
            ]},
            "evidence": {"type": "object", "additionalProperties": False,
                         "description": "Exact contiguous substrings from the user's sentence; null when field absent",
                         "required": list(EVIDENCE_FIELDS),
                         "properties": {field: {"type": ["string", "null"]} for field in EVIDENCE_FIELDS}},
            "constraints": {"type": "array", "description": "Unsupported explicit song attributes; use [] when none",
                            "items": {"type": "object", "additionalProperties": False,
                                      "required": ["evidence", "classification", "polarity"],
                                      "properties": {
                                          "evidence": {"type": "string"},
                                          "classification": {"type": "string", "enum": ["unsupported_constraint"]},
                                          "polarity": {"type": "string", "enum": ["include", "exclude"]},
                                      }}},
        },
    }


SYSTEM_PROMPT = """你是中文找歌原话解析器，只读取用户原句，不读取歌曲或标准答案。严格输出 schema 中的全部字段；无不支持条件时 constraints 必须是 []，没有依据的字段用 null，evidence 中对应项也用 null。
current_* 只指人现在的状态；target_* 只指想听到的音乐。事件或场景本身不自动产生情绪值。valence 为 -1/0/1，arousal 与 melodic_surprise 为 1/2/3。
明确的音乐情绪／活跃度边界可在原 target 字段用 {"relation":"at_least|at_most","value":整数}，不要把范围改成单个档位。
只有明确要求歌曲按顺序变化，trajectory 才用 {"type":"from_to","arousal":{"from":起点,"to":终点}} 或同结构的 valence 路径；终点必须与对应 target 精确值相同。人的状态慢慢改变不代表歌曲需要这个顺序。有音乐目标但无音乐顺序时用 single_target；仅旋律偏好、仅不支持条件或仅软愿望时用 none。
只有明确要求可辨旋律才填 requires_melody_present=true，否则为 null；不要从旋律意外感推断。可辨旋律也不能证明无人声。
constraints 只列曲库没有可靠字段可保证的明确歌曲属性要求，如人声、语言、流派、速度、音量及主观风格词；主观陪伴或治愈效果不当作硬约束。可由情绪、活跃度或旋律维度表达的要求不要重复列入 constraints。
from_to 的 trajectory 必须有原句逐字证据；none 的 trajectory 证据必须为 null。single_target 是由明确音乐目标推得的无顺序目标，其 trajectory 证据可为 null；若填写仍须是原句逐字片段。其他非空意图字段及每项约束都必须有原句逐字证据。不得输出额外字段、解释或歌曲。"""


class InvalidIntent(ValueError):
    """Safe category and schema path only; never include model output text."""

    def __init__(self, category: str, field: str | None = None):
        self.category, self.field = category, field
        super().__init__(f"{category}:{field}" if field else category)


def check_fields(raw: Any, expected: set[str], path: str) -> None:
    if not isinstance(raw, dict):
        raise InvalidIntent("invalid_field_value", path or None)
    missing = expected - set(raw)
    if missing:
        # Only names from our fixed schema are included; never echo unknown model keys.
        safe_names = ",".join(f"{path}.{name}".lstrip(".") for name in sorted(missing))
        raise InvalidIntent("missing_field", safe_names)
    if set(raw) - expected:
        raise InvalidIntent("extra_field", path or None)


def exact_integer(value: Any, choices: set[int]) -> bool:
    return type(value) is int and value in choices


def validate_target(value: Any, field: str) -> bool:
    if value is None:
        return False
    if type(value) is int:
        if value not in DOMAINS[field]:
            raise InvalidIntent("numeric_out_of_range", field)
        return True
    if not isinstance(value, dict):
        raise InvalidIntent("invalid_numeric_type", field)
    if (set(value) != {"relation", "value"} or type(value["relation"]) is not str
            or value["relation"] not in {"at_least", "at_most"}):
        raise InvalidIntent("invalid_field_value", field)
    if type(value["value"]) is not int:
        raise InvalidIntent("invalid_numeric_type", f"{field}.value")
    if value["value"] not in DOMAINS[field]:
        raise InvalidIntent("numeric_out_of_range", f"{field}.value")
    return True


def validate_trajectory(value: Any, raw: dict[str, Any]) -> bool:
    if type(value) is str and value in ("none", "single_target"):
        if (value == "single_target" and raw["target_valence"] is None
                and raw["target_arousal"] is None):
            raise InvalidIntent("invalid_field_value", "trajectory")
        return value == "single_target"
    if not isinstance(value, dict) or value.get("type") != "from_to":
        raise InvalidIntent("invalid_field_value", "trajectory")
    if not set(value) <= {"type", "valence", "arousal"} or len(value) < 2:
        raise InvalidIntent("invalid_field_value", "trajectory")
    for dimension in ("valence", "arousal"):
        if dimension not in value:
            continue
        path = value[dimension]
        options = DOMAINS[f"target_{dimension}"]
        if (not isinstance(path, dict) or set(path) != {"from", "to"}
                or not exact_integer(path["from"], options) or not exact_integer(path["to"], options)
                or path["from"] == path["to"]
                or raw[f"target_{dimension}"] != path["to"]):
            raise InvalidIntent("invalid_field_value", f"trajectory.{dimension}")
    return True


def validate_intent(raw: Any, utterance: str) -> dict[str, Any]:
    check_fields(raw, {*EVIDENCE_FIELDS, "evidence", "constraints"}, "")
    evidence = raw["evidence"]
    check_fields(evidence, set(EVIDENCE_FIELDS), "evidence")
    for field in EVIDENCE_FIELDS:
        value = raw[field]
        if field == "trajectory":
            active = validate_trajectory(value, raw)
        elif field in {"target_valence", "target_arousal"}:
            active = validate_target(value, field)
        elif field == "requires_melody_present":
            if value is not None and value is not True:
                raise InvalidIntent("invalid_field_value", field)
            active = value is True
        else:
            if value is not None:
                if type(value) is not int:
                    raise InvalidIntent("invalid_numeric_type", field)
                if value not in DOMAINS[field]:
                    raise InvalidIntent("numeric_out_of_range", field)
            active = value is not None
        phrase = evidence[field]
        if field == "trajectory" and value == "single_target":
            if phrase is None:
                continue
            if not isinstance(phrase, str) or not phrase:
                raise InvalidIntent("invalid_evidence_value", field)
            if phrase not in utterance:
                raise InvalidIntent("evidence_not_in_utterance", field)
            continue
        if active:
            if phrase is None or phrase == "":
                raise InvalidIntent("missing_evidence", field)
            if not isinstance(phrase, str):
                raise InvalidIntent("invalid_evidence_value", field)
            if phrase not in utterance:
                raise InvalidIntent("evidence_not_in_utterance", field)
        elif phrase is not None:
            raise InvalidIntent("unexpected_evidence", field)
    constraints = raw["constraints"]
    if not isinstance(constraints, list):
        raise InvalidIntent("invalid_constraint_format", "constraints")
    for index, item in enumerate(constraints):
        if not isinstance(item, dict) or set(item) != {"evidence", "classification", "polarity"}:
            raise InvalidIntent("invalid_constraint_format", f"constraints[{index}]")
        if (not isinstance(item["evidence"], str) or not item["evidence"]
                or item["classification"] != "unsupported_constraint"
                or type(item["polarity"]) is not str or item["polarity"] not in {"include", "exclude"}):
            raise InvalidIntent("invalid_constraint_format", f"constraints[{index}]")
        if item["evidence"] not in utterance:
            raise InvalidIntent("evidence_not_in_utterance", f"constraints[{index}].evidence")
    return raw


def route_status(intent: dict[str, Any]) -> str:
    return "cannot_guarantee_constraint" if intent["constraints"] else "ready"
