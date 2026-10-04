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


SYSTEM_PROMPT = """You are a parser for Chinese-language song requests. Read only the user's original sentence, not songs or gold answers. Output every schema field. Use constraints=[] when there are no unsupported conditions; use null for fields without evidence and for their corresponding evidence entries.
current_* refers only to the person's current state; target_* refers only to the music they want to hear. Events or scenes themselves do not automatically generate emotional values. valence is -1/0/1, arousal and melodic_surprise are 1/2/3.
Explicit music mood/energy boundaries can be set in the original target field using `{"relation":"at_least|at_most","value":integer}`, do not change the range into a single tier.
Only when songs are explicitly requested to change in order should trajectory use {"type":"from_to","arousal":{"from":start,"to":end}} or a valence path of the same structure; the end point must be identical to the exact value of the corresponding target. A gradual change in a person's state does not mean the songs need to follow this order. Use single_target when there is a musical goal but no musical order; use none for melody preference only, unsupported conditions only, or soft wishes only.
Fill in requires_melody_present=true only when recognizable melody is explicitly requested, otherwise null; do not infer from melody surprise. Recognizable melody also does not prove the absence of vocals.
constraints lists only explicit song property requirements that the music library has no reliable fields to guarantee, such as vocals, language, genre, tempo, volume, and subjective style words; subjective companionship or healing effects are not treated as hard constraints. Requirements that can be expressed by emotion, arousal, or melody dimensions should not be repeatedly listed in constraints.
The trajectory of from_to must have verbatim evidence from the original sentence; the trajectory evidence for none must be null. single_target is an unordered target derived from a clear music target, and its trajectory evidence can be null; if filled, it must still be a verbatim segment from the original sentence. Other non-empty intent fields and each constraint must have verbatim evidence from the original sentence. Do not output extra fields, explanations, or songs. """


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
