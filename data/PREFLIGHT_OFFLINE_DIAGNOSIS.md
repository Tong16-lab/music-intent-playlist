# Single-Sentence Pre-check Offline Troubleshooting (2026-10-03)

This record only inspects local code and previously reported safety usage data; no keys in `.env` were read, no API requests were initiated, the test set was not frozen, and no formal evaluation was run this time. The JSON below is a manually constructed **offline estimation sample**, not a model reply, nor is it the test set standard answer.

## Actual Request Settings and Local Processing

- `build_request` sends one system message and one user message; the model is provided by `OPENROUTER_MODEL`. The models reported in the previous two pre-checks were `google/gemini-3.1-flash-lite`. `.env` was not read this time, so the current runtime environment variable values are not re-asserted.
- The current code sends `max_tokens=2048`, `reasoning={"effort":"minimal"}`, `temperature=0`, `response_format.type=json_schema`, `json_schema.strict=true`, `provider.require_parameters=true`, and `usage.include=true`. There is no concurrent second token upper limit or reasoning parameter, nor are there duplicate system messages.
- The JSON Schema is about 3192 UTF-8 bytes when compressed: 9 required fields at the top level, 7 required fields in `evidence`, plus range values, playlist paths, and unsupported condition structures. The system prompt is about 734 characters. They indeed have some complexity, but do not require outputting song lists or long explanations; both the prompt and Schema require all fields, serving as mutually corresponding constraints.
- Response parsing checks `finish_reason` first, then parses content and verbatim evidence. `length` is directly categorized as `output_token_limit`, and even if the response already contains partial content, it will not be treated as a valid intent card.
- Usage parsing previously read `usage.completion_tokens_details.reasoning_tokens`, but the preview terminal did not display this value. It is now changed to display when a value is present, and compatible with the top-level `usage.reasoning_tokens`; when no value is present, it displays `unavailable`, and cannot be written as 0. The finish reason retains only allowed status words, and other provider texts are classified as `other` without being printed as-is.

## Valid Example for Length Estimation Only

Corresponding to the existing non-test single-sentence preflight input, the following sample passes the field and verbatim evidence validation of `validate_intent`:

```json
{
  "current_valence": -1,
  "current_arousal": null,
  "target_valence": null,
  "target_arousal": 1,
  "target_melodic_surprise": null,
  "trajectory": "single_target",
  "requires_melody_present": true,
  "evidence": {
    "current_valence": "feeling a bit annoyed",
    "current_arousal": null,
    "target_valence": null,
    "target_arousal": "quiet",
    "target_melodic_surprise": null,
    "trajectory": "I want to listen to a quiet piece of music with a clear melody",
    "requires_melody_present": "has clear melody"
  },
  "constraints": []
}
```

After removing display spaces and line breaks, it has **394 characters and 444 UTF-8 bytes**. According to the rough magnitude of general text tokenization, the requirement to complete such JSON can first be estimated as **about 100–250 tokens**; Gemini's actual tokenization may differ, and this range cannot be taken as a billing measurement. Even if written as indented JSON, thousands of tokens are not required. This comparison cannot prove that the model actually spent its output quota on reasoning, verbose content, or other locations.

## What Existing Records Can Determine

- The two preflight checks hit the setting limits of 1024 and 2048 respectively; previous security reports recorded `completion_tokens=1008` and `2032` respectively, with `prompt_tokens=409` for the second one. Both were classified as `output_token_limit` due to `finish_reason=length`, and no successful preflight marker was generated.
- The repository does not save the raw responses or reasoning token details for these two instances; previous terminal reports also did not display `reasoning_tokens`. Judging from existing local records, **the number of reasoning tokens for both instances is untraceable**. Without accessing the provider's backend this time, it is impossible to confirm whether there are other queryable records.
- No obvious parameter conflicts or accidental duplicate messages were found in the current static request. The old 1024 setting is not the current code's setting; the complete request of the first call cannot be reconstructed solely from the current code.

## Possible Causes and Next Minimal Diagnosis

1. **Confirmed proximate cause: Completion token budget exhausted.** Both ended with `length`, and the reported completion usage was close to their respective limits; a short JSON by itself is insufficient to explain the full usage.
2. **To be verified: Reasoning tokens consumed the completion budget.** Although the current tier is `minimal`, the old report did not break down usage. The next step should first check whether `tokens_reasoning` is returned and how much of the completion usage it accounts for.
3. **To be verified: Actually generated content is too long or the structured output process exhausts the budget.** Existing code does not save or print raw responses, making it impossible to distinguish such situations; if the reasoning usage is very low next time and still hits the limit, it can only be confirmed as "non-reported reasoning token consumption", and specific text content cannot be judged out of thin air.
4. **Weaker possibility: Schema and prompt complexity cause generation difficulties.** Both have multiple nested structures, but the valid sample is very short, and no duplicate messages were found. Finish reasons and usage details are needed to determine whether it is worth further simplifying the wording; fields or evidence validation cannot be relaxed just to pass preflight.
5. **Currently no code evidence: parameter conflict or configuration error.** Static requests have only one model, reasoning tier, and token limit. The next single-sentence pre-check should verify the actual response model in the safety report; this run did not read `.env` or override configuration.

The next paid pre-check must be separately authorized by the author, calling only a single existing example sentence without automatic retries. The core issue is whether the provider supplies `reasoning_tokens` and whether it can explain `completion_tokens` approaching the limit. Without this breakdown, continuing to increase the limit will not become an evidence-based fix. The test set is currently unfrozen, and the 30 formal evaluations have not yet been run.
