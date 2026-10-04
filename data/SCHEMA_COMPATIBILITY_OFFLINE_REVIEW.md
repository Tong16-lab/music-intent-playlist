# Complete Structured Output Schema: Offline Compatibility Check

> **Historical Audit Record.** This document records the formal Schema that previously contained five nullable `enum` values. In subsequent official runs, the Schema only removed these five `enum`s; the old complete Schema short-prompt probe and the old nine-field intermediate probe each fixed their respective enumerations in their scripts to preserve contrast and reproducibility. The "current formal Schema" in this article refers to the version at the time of writing.

This record only checks local code and official public documentation; no inference requests were sent to OpenRouter or Gemini. The existing observations are: for the same model and the same example sentence, two-field minimal probes succeeded, while the full nine-field Schema with both long and short prompts previously returned missing-field results. They only indicate that **the results of these combinations differ**, and cannot determine the root cause. Historical calls did not save complete responses, nor can they reconstruct the actual provider endpoints hit at the time.

## Boundaries Between Official Documentation and Current Routing

| Feature | Current Formal Schema Usage | Google Gemini Official Documentation | OpenRouter Official Documentation / Current Routing |
| --- | --- | --- | --- |
| `anyOf` | One each for `target_valence`, `target_arousal`, and `trajectory`; branches contain scalars and objects | **Explicitly supports syntax**: Structured output examples use `anyOf`, and the GenerateContent JSON Schema support list also lists it. | **Does not specify how this keyword is handled at the current endpoint**. Documentation states that the execution of `strict=true` varies by endpoint. |
| Nullable types | Multiple `type:["integer","null"]`, `["boolean","null"]`, `["string","null"]`; numeric enums also include `null` | **Explicitly supports** putting `"null"` in the `type` array. Integer enums and nullable types have respective explanations; **does not explicitly explain** the combination of "enum containing both numbers and `null`". | **Does not itemize** the support for nullable types or mixed enums by the current OpenRouter→Gemini endpoint. |
| Nested required objects | Seven required keys for `evidence`; three required keys for `constraints[]`; range objects and path objects further nested | **Explicitly supports syntax**: Object `properties`/`required` are listed, and official examples also show nested objects and required fields. Documentation also warns that very large or very deep Schemas may be rejected, but does not provide threshold values for this model. | Examples explicitly show **top-level** `required`; **does not itemize** the extent to which multi-level nested guarantees are supported at the current endpoint. |
| `additionalProperties:false` | Used across top-level, range, path, evidence, and constraint objects | **Explicitly supports syntax**: Object property list includes `additionalProperties`. | Official examples explicitly use `false` at the top level; **does not itemize** nested usage for the current endpoint. |

Sources: [OpenRouter Structured Outputs](https://openrouter.ai/docs/guides/features/structured-outputs), [OpenRouter Gemini 3.5 Flash Lite Model Page](https://openrouter.ai/google/gemini-3.5-flash-lite), [Google Gemini Structured Outputs](https://ai.google.dev/gemini-api/docs/structured-output), [Google GenerateContent API](https://ai.google.dev/api/generate-content). Google documentation describes the capabilities of Gemini's own interface, and **cannot be directly presumed** to mean that the endpoint chosen by OpenRouter fully preserves every Schema constraint. OpenRouter explicitly states that support is determined by the provider endpoint; `require_parameters=true` helps select endpoints that claim to support parameters, and `strict=true` may not guarantee complete compliance across all endpoints.

**Local Code Inference:** The current formal Schema uses only basic keywords listed in the documentation, with no obvious spelling errors or invalid JSON observed; however, whether the **combination** of its multiple nullable enumerations, union branches, and nested required objects executes stably on actual routing is not proven by the documentation. Past "HTTP success but missing fields" means that the response failed to satisfy local validation checks, and one cannot reverse-engineer which layer ignored the Schema, nor assert whether the model, routing, or prompt caused it.

## Formal Schema and Local Validation

The following discrepancies only suggest directions for correction in subsequent versions; the formal Schema, prompts, validator, or V2 answers were not modified in this round.

1. The Schema for `requires_melody_present` allows `false`, but local `validate_intent` only accepts `true`/`null`. Future iterations could consider having the Schema accept only these two values, provided it is first confirmed whether the current endpoint can execute the corresponding boolean/null enums; local hard validation should be retained.
2. The object branches for `trajectory` only require `type`, so the Schema can accept `{"type":"from_to"}` without paths. Local requirements dictate at least one `valence` or `arousal` path, differing start and end points, and that the endpoint matches the target value. Future versions could express "at least one path" in the **new version** of the Schema, while cross-field consistency still requires local validation.
3. The Schema allows empty `evidence` strings, and does not express cross-field rules such as "active fields must have evidence, invalid fields must have `null` evidence, and evidence must appear verbatim in the source sentence". Local checks are already strict. Future versions can add executable non-empty constraints; verbatim verification remains left to local programs.
4. The `evidence` in `constraints[]` can be an empty string or any string in the Schema, whereas local checks require it to be non-empty and exist verbatim in the source sentence. Future versions can tighten non-empty conditions; verbatim verification is still handled locally.
5. `additionalProperties:false` at the top level and across objects **matches** local rejection of extra keys. The exact value/range value domains of `target_*` also basically match local checks; do not attribute all failures to inconsistencies between the Schema and the validator.

Even if future Schemas align more closely with local rules, a Schema only represents structural validity and cannot prove accurate intent understanding, guaranteed song constraints, or pass verbatim evidence checks.

## Precise Differences of the Independent Intermediate Probe

Script: `scripts/probe_intermediate_schema.py`. It reuses the model `google/gemini-3.5-flash-lite` from the previous **full Schema + short prompt probe**, the same example sentence outside the development/test set, the same `data/FULL_SCHEMA_SHORT_PROMPT.txt`, the same OpenRouter endpoint, and all request parameters: `strict=true`, `require_parameters=true`, `reasoning.effort=minimal`, `max_tokens=2048`, and default temperature. The JSON Schema name also remains `music_intent`. **Only the Schema content changes in the request.**

Unchanged: the top-level object's **nine property names, nine `required` items and their order, and `additionalProperties:false`**; the property Schemas for `current_valence`, `current_arousal`, `target_melodic_surprise`, and `requires_melody_present` are retained as-is.

Only modify the following five properties:

| Property | Official Schema | Intermediate Probe Schema |
| --- | --- | --- |
| `target_valence`, `target_arousal` | `anyOf`: nullable exact integer or required range object with `{relation,value}` | Takes only the first branch of the original `anyOf`: nullable exact integer; **cannot represent V2 ranges** |
| `trajectory` | `anyOf`: `none` / `single_target` or `from_to` object with nested paths | Takes only the string branch: `none` / `single_target`; **cannot represent sequential paths** |
| `evidence` | Object containing seven required nullable subfields | A single nullable string representing a snippet of verbatim evidence; no more nested keys |
| `constraints` | Array, where each item is an object with three required fields | Array of strings; remains `[]` when there are no conditions |

The intermediate probe does not contain `anyOf` or nested objects, but still retains the nine top-level required fields and the four original nullable scalar fields. It is a **diagnostic protocol**, cannot express approved complete V2 answers, and cannot enter official preflight or formal evaluation. It only checks its simplified structure and whether scalar evidence is verbatim-extracted from the example sentence, without calling the official `validate_intent` or writing to `data/connection_preflight.json`. If run without the explicit `--allow-paid-probe` argument, the script will exit before reading local configuration or sending network requests; this argument was not used in this round.

### What a Single Next Call Can Answer

- If the nine-field flat probe succeeds: It indicates that this combination of model, sentence, short prompt, and request parameters can produce nine fields; the explanation that "the field count alone causes failure" becomes weaker. Joint branches, nested objects, or combinations thereof become stronger candidates for separate testing, **though it cannot be conclusively determined which one**, and it certainly does not mean the official intent card has succeeded.
- If fields are still missing or it fails: It indicates that removing joint branches and nested objects is still insufficient to resolve this phenomenon; the nine-field count, nullable enums, endpoint execution, prompts, or other factors still need to be distinguished. **It cannot be concluded from this** that Gemini does not support `anyOf` or nested objects.
- Regardless of the outcome, a single result is merely a one-off comparison; if features need to be further isolated in the next step, a new single-variable probe should be designed first and obtain another explicit authorization. The test set must not be frozen or 30 evaluations run based on this.
