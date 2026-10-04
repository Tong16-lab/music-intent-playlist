# Formal scoring specification v3 — English rendering

This translates the scoring logic preserved in `FORMAL_SCORING_V3.md`. That source was written before the completed formal run. Its historical “not yet frozen/not yet evaluated” wording reflects the time it was prepared; the set was subsequently frozen and evaluated. This file clarifies the same rules without changing the code, gold answers, or recorded results.

## Denominators and stages

- `N` is the number of evaluation requests, **30** in the formal set. Each request is called at most once in a run. An API failure or invalid card still occupies its end-to-end denominator; its field, full-card, and constraint results are marked **unfinished**, not correct. It is not automatically a model-level false positive or false negative for a phrase.
- `V` is the number of cards that pass compact conversion plus the existing V2 value, path, constraint, and exact-source-evidence checks. Valid-only accuracy is `correct/V`. If `V=0`, report “not evaluable,” not an apparent `0/0` accuracy. Run 2 had `V=28`.
- Count processable API responses, complete JSON, required-field structure, compact conversion, and local validation separately. Passing a stage never proves the next one or semantic correctness.
- The keyword baseline processes the **same requests** against the **same approved answers**. It has no API, JSON, schema, or local-card stage and must not be assigned invented structural pass rates.

## Six core intent fields

Report both end-to-end `correct/N` and valid-only `correct/V` for each of `current_valence`, `current_arousal`, `target_valence`, `target_arousal`, `target_melodic_surprise`, and `trajectory`. A match must be **exact**: `{"relation":"at_least","value":0}` does not equal exactly `0`; `at_most` does not equal its endpoint; a `from_to` object does not equal `single_target`. A six-field card counts as correct only if all six match and the card is valid. This is a strict supplementary measure, not the sole measure of understanding.

For each of the first five nullable fields, split cases by the approved answer. The **stated subset** has a non-null value, including a range object; report its size, model end-to-end correct count, model valid-only correct count over valid cases in that subset, and baseline correct count. The **unstated subset** has an approved `null`; report the same exact-match counts. In the valid unstated subset only, a predicted non-null is a **false fill**. Invalid cards are counted separately as unfinished rather than false fills.

Trajectory requires its own distinction. A stated **song-order** requirement exists only where the approved answer is `{"type":"from_to",...}`. `single_target` expresses a music goal without requested song order; `none` expresses no encodable music goal or order. Both belong to the **no-explicit-order** subset, but are still distinct values for exact matching. In that subset, an invented `from_to` is a false song-order path. A confusion between `single_target` and `none` is an exact-match error reported separately, not mislabeled as a `from_to` false positive. The keyword baseline receives the same subgroup treatment and, because it always returns a value, no valid-only denominator.

## Auxiliary fields and conditions

- Report `requires_melody_present` separately, end-to-end and valid-only; it is not one of the six core fields.
- Score unsupported `constraints` in two distinct ways: (1) whether the presence or absence of any unguaranteed condition agrees with the approved `expected_cannot_guarantee_constraint`; and (2) whether the **set of exact source phrases** equals the approved set. Report both as end-to-end `correct/N` and valid-only `correct/V`. Neither enters the six-field card score.
- Phrase hits, false positives, and misses are calculated only from valid cards. Expected phrases attached to invalid or failed calls are “unfinished” for end-to-end coverage, not model misses. The V2 answers did not approve each item's `polarity`; phrase-set scoring must not imply they did.

The public report retains case IDs, predefined safe error categories, known field names, counts, token usage, and estimated cost. It excludes credentials, request headers, full provider replies, and unknown generated field/value text.
