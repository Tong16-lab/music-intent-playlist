"""Standard OpenRouter list-rate estimates; never reuse another model's rate."""

from __future__ import annotations

# USD per million tokens, standard text routing. Verify before future paid runs.
# https://openrouter.ai/google/gemini-3.1-flash-lite
# https://openrouter.ai/google/gemini-3.5-flash-lite
STANDARD_RATES = {
    "google/gemini-3.1-flash-lite": (0.25, 1.50),
    "google/gemini-3.5-flash-lite": (0.30, 2.50),
}


def estimate_standard_cost_usd(model: str, usage: dict[str, int]) -> float | None:
    rates = STANDARD_RATES.get(model)
    prompt = usage.get("prompt_tokens")
    completion = usage.get("completion_tokens")
    if rates is None or type(prompt) is not int or prompt < 0 or type(completion) is not int or completion < 0:
        return None
    return (prompt * rates[0] + completion * rates[1]) / 1_000_000
