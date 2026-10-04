"""Single-call OpenRouter client. Never log credentials or raw error bodies."""

from __future__ import annotations

import json
import errno
import re
import socket
import ssl
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .intent import SYSTEM_PROMPT, InvalidIntent, response_schema, validate_intent

ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterFailure(RuntimeError):
    def __init__(self, category: str, usage: dict[str, int] | None = None,
                 model: str | None = None, field: str | None = None,
                 finish_reason: str | None = None,
                 content_shape: dict[str, bool | int | None] | None = None,
                 json_complete: bool | None = None,
                 required_structure_complete: bool | None = None,
                 http_status: int | None = None,
                 transport_phase: str | None = None):
        super().__init__(f"{category}:{field}" if field else category)
        self.category = category
        self.field = field
        self.usage = usage or {}
        self.model = model
        self.finish_reason = finish_reason
        self.content_shape = content_shape
        self.json_complete = json_complete
        self.required_structure_complete = required_structure_complete
        self.http_status = http_status if type(http_status) is int and 100 <= http_status <= 599 else None
        self.transport_phase = transport_phase if transport_phase in {
            "open_or_headers", "response_body", "http_status"} else None


def classify_transport_error(error: BaseException, phase: str) -> str:
    """Map known exception types to fixed labels; never retain exception text."""
    reason = error.reason if isinstance(error, URLError) else error
    if isinstance(reason, socket.gaierror):
        return "network_dns"
    if isinstance(reason, ssl.SSLCertVerificationError):
        return "network_tls_certificate"
    if isinstance(reason, ssl.SSLError):
        return "network_tls"
    if isinstance(reason, TimeoutError):
        return "network_timeout_body" if phase == "response_body" else "network_timeout_open_or_headers"
    if isinstance(reason, PermissionError) or (isinstance(reason, OSError) and reason.errno in {errno.EPERM, errno.EACCES}):
        return "network_local_permission"
    if isinstance(reason, ConnectionRefusedError):
        return "network_connection_refused"
    if isinstance(reason, ConnectionResetError):
        return "network_connection_reset"
    if isinstance(reason, OSError) and reason.errno in {errno.ENETUNREACH, errno.EHOSTUNREACH}:
        return "network_unreachable"
    # urllib can encode a proxy CONNECT failure as an OSError reason rather than HTTPError.
    if isinstance(reason, (OSError, str)) and str(reason).startswith("Tunnel connection failed:"):
        return "network_proxy_tunnel"
    return "network_other"


def required_structure_complete(schema: dict[str, Any], value: Any) -> bool:
    """Check known required keys and JSON types, without judging values or evidence."""
    branches = schema.get("anyOf")
    if isinstance(branches, list):
        return any(required_structure_complete(branch, value) for branch in branches)
    allowed = schema.get("type")
    if isinstance(allowed, list):
        return any(required_structure_complete({"type": kind}, value) for kind in allowed)
    if allowed == "object":
        if not isinstance(value, dict) or not set(schema.get("required", [])) <= set(value):
            return False
        return all(required_structure_complete(child, value[name])
                   for name, child in schema.get("properties", {}).items() if name in value)
    if allowed == "array":
        return isinstance(value, list) and all(
            required_structure_complete(schema["items"], item) for item in value)
    if allowed == "integer":
        return type(value) is int
    if allowed == "string":
        return type(value) is str
    if allowed == "boolean":
        return type(value) is bool
    if allowed == "null":
        return value is None
    return False


def safe_finish_reason(value: Any) -> str:
    """Keep only known completion reasons; never echo arbitrary provider text."""
    if type(value) is str and value in {"stop", "length", "content_filter", "tool_calls", "function_call"}:
        return value
    return "unavailable" if value is None else "other"


def safe_content_shape(choice: dict[str, Any]) -> dict[str, bool | int | None]:
    """Summarize truncated content without retaining or printing its text."""
    message = choice.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str):
        return {"content_empty": None, "content_chars": None, "repeated_suffix": None}
    repeated_suffix = any(
        content[-3 * width:] == content[-width:] * 3
        for width in range(16, min(256, len(content) // 3) + 1)
    )
    return {"content_empty": content == "", "content_chars": len(content),
            "repeated_suffix": repeated_suffix}


def classify_http_error(status: int) -> str:
    if status == 407:
        return "proxy_authentication"
    if status in {401, 403}:
        return "key_or_permission"
    if status == 402:
        return "insufficient_credits"
    if status == 404:
        return "model_unavailable"
    if status == 429:
        return "rate_or_quota_limit"
    if status in {400, 422}:
        return "request_or_schema_format"
    return "service_error"


def build_request(utterance: str, model: str) -> dict[str, Any]:
    if not isinstance(utterance, str) or not utterance.strip():
        raise ValueError("empty_utterance")
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": utterance},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "music_intent", "strict": True, "schema": response_schema()},
        },
        "provider": {"require_parameters": True},
        "usage": {"include": True},
        "reasoning": {"effort": "minimal"},
        # Completion tokens can include reasoning, so leave room for the JSON.
        "max_tokens": 2048,
    }


def parse_response(payload: Any, utterance: str, requested_model: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate an API response without exposing its content in failures."""
    if not isinstance(payload, dict):
        raise OpenRouterFailure("invalid_response_shape", model=requested_model)
    raw_usage = payload.get("usage")
    usage = {
        name: value for name in ("prompt_tokens", "completion_tokens", "total_tokens")
        if isinstance(raw_usage, dict)
        for value in [raw_usage.get(name)]
        if type(value) is int and value >= 0
    }
    details = raw_usage.get("completion_tokens_details") if isinstance(raw_usage, dict) else None
    reasoning_tokens = details.get("reasoning_tokens") if isinstance(details, dict) else None
    if reasoning_tokens is None and isinstance(raw_usage, dict):
        reasoning_tokens = raw_usage.get("reasoning_tokens")
    if type(reasoning_tokens) is int and reasoning_tokens >= 0:
        usage["reasoning_tokens"] = reasoning_tokens
    raw_model = payload.get("model")
    response_model = (raw_model if isinstance(raw_model, str)
                      and re.fullmatch(r"[A-Za-z0-9._:/-]{1,120}", raw_model)
                      else requested_model)
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        raise OpenRouterFailure("missing_content", usage, response_model)
    choice = choices[0]
    finish_reason = safe_finish_reason(choice.get("finish_reason"))
    if finish_reason == "length":
        raise OpenRouterFailure("output_token_limit", usage, response_model, finish_reason=finish_reason,
                                content_shape=safe_content_shape(choice))
    if finish_reason != "stop":
        raise OpenRouterFailure("incomplete_response", usage, response_model, finish_reason=finish_reason)
    message = choice.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if content is None or content == "":
        raise OpenRouterFailure("missing_content", usage, response_model, finish_reason=finish_reason)
    if not isinstance(content, str):
        raise OpenRouterFailure("invalid_content_type", usage, response_model, finish_reason=finish_reason)
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        raise OpenRouterFailure("invalid_content_json", usage, response_model, finish_reason=finish_reason) from None
    structure_complete = required_structure_complete(response_schema(), parsed)
    try:
        intent = validate_intent(parsed, utterance)
    except InvalidIntent as error:
        raise OpenRouterFailure(error.category, usage, response_model, error.field,
                                finish_reason=finish_reason, json_complete=True,
                                required_structure_complete=structure_complete) from None
    return intent, {"model": response_model, "usage": usage, "finish_reason": finish_reason,
                    "json_complete": True, "required_structure_complete": structure_complete}


def parse_once(utterance: str, key: str, model: str, timeout: int = 30) -> tuple[dict[str, Any], dict[str, Any]]:
    body = json.dumps(build_request(utterance, model), ensure_ascii=False).encode("utf-8")
    request = Request(
        ENDPOINT, data=body, method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
    except HTTPError as error:
        raise OpenRouterFailure(classify_http_error(error.code), model=model) from None
    except (URLError, TimeoutError, OSError):
        raise OpenRouterFailure("network", model=model) from None
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise OpenRouterFailure("invalid_response_json", model=model) from None
    return parse_response(payload, utterance, model)
