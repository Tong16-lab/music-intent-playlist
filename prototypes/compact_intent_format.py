"""Offline-only candidate wire format; not imported by the production client."""

from __future__ import annotations

import copy
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from music_intent.intent import (  # noqa: E402
    DOMAINS, EVIDENCE_FIELDS, InvalidIntent, check_fields, response_schema,
    validate_intent,
)

NUMBER = r"(?:0|-[1-9][0-9]*|[1-9][0-9]*)"
TARGET = re.compile(rf"^(=|<=|>=)({NUMBER})$")
PATH = re.compile(rf"^(valence|arousal):({NUMBER})->({NUMBER})$")
TOP_LEVEL = {*EVIDENCE_FIELDS, "evidence", "constraints"}


def candidate_schema() -> dict[str, Any]:
    """Keep the nine-field envelope; simplify only two targets and trajectory."""
    schema = copy.deepcopy(response_schema())
    for field in ("target_valence", "target_arousal"):
        schema["properties"][field] = {
            "type": ["string", "null"],
            "description": "Exact =N, inclusive lower >=N, inclusive upper <=N, or null. Local domain validation applies.",
        }
    schema["properties"]["trajectory"] = {
        "type": "string",
        "description": "none, single_target, valence:A->B, arousal:A->B, or valence:A->B;arousal:C->D. Local validation applies.",
    }
    return schema


def _target(value: Any, field: str) -> Any:
    if value is None:
        return None
    if type(value) is not str:
        raise InvalidIntent("invalid_field_value", field)
    match = TARGET.fullmatch(value)
    if match is None:
        raise InvalidIntent("invalid_field_value", field)
    operator, digits = match.groups()
    number = int(digits)
    if number not in DOMAINS[field]:
        raise InvalidIntent("numeric_out_of_range", field)
    if operator == "=":
        return number
    return {"relation": "at_least" if operator == ">=" else "at_most", "value": number}


def _trajectory(value: Any) -> Any:
    if value in ("none", "single_target") and type(value) is str:
        return value
    if type(value) is not str:
        raise InvalidIntent("invalid_field_value", "trajectory")
    pieces = value.split(";")
    if not 1 <= len(pieces) <= 2:
        raise InvalidIntent("invalid_field_value", "trajectory")
    result: dict[str, Any] = {"type": "from_to"}
    dimensions: list[str] = []
    for piece in pieces:
        match = PATH.fullmatch(piece)
        if match is None:
            raise InvalidIntent("invalid_field_value", "trajectory")
        dimension, start, end = match.groups()
        dimensions.append(dimension)
        options = DOMAINS[f"target_{dimension}"]
        if int(start) not in options:
            raise InvalidIntent("numeric_out_of_range", f"trajectory.{dimension}.from")
        if int(end) not in options:
            raise InvalidIntent("numeric_out_of_range", f"trajectory.{dimension}.to")
        result[dimension] = {"from": int(start), "to": int(end)}
    if dimensions != [name for name in ("valence", "arousal") if name in dimensions]:
        raise InvalidIntent("invalid_field_value", "trajectory")
    return result


def convert_syntax(raw: Any) -> dict[str, Any]:
    """Convert only the three abbreviated fields; never infer missing values."""
    check_fields(raw, TOP_LEVEL, "")
    converted = copy.deepcopy(raw)
    converted["target_valence"] = _target(raw["target_valence"], "target_valence")
    converted["target_arousal"] = _target(raw["target_arousal"], "target_arousal")
    converted["trajectory"] = _trajectory(raw["trajectory"])
    return converted


def convert_candidate(raw: Any, utterance: str) -> dict[str, Any]:
    """Convert syntax, then run the existing strict V2/evidence validator.

    No field, evidence, constraint polarity, or intended meaning is inferred.
    """
    return validate_intent(convert_syntax(raw), utterance)
