# Official Evaluation Scoring Criteria v3 (Fixed in advance, no official scores yet)

This document fixes the scoring method for `formal-scoring-v3`, which applies to the same batch of approved example-sentence AI intent cards and existing keyword baselines. The official test set has not been frozen or called by the model yet; this criterion cannot be modified based on future results while retaining the original scores. Old development reports retain their criteria and original appearance at that time.

## Denominator and Stages

- The total dataset denominator `N` is the number of sentences in the current evaluation set; the official evaluation expects `N=30`. Each sentence requests the AI at most once; failures or missing valid intent cards still count towards the end-to-end denominator, and their fields, entire cards, and constraint results are recorded as **incomplete**, not automatically judged as correct, nor recorded as model misfilling or omission of a certain term.
- The valid output denominator `V` is the number of intent cards that pass shorthand conversion, existing V2 value, trajectory, constraint, and verbatim evidence verification. The valid-output accuracy alone is `number of correct/V`; if `V=0`, write "Not evaluated", and do not write `0/0` to represent accuracy.
- Count separately whether the API returns a processable response, complete JSON, complete Schema required structure, completed shorthand conversion, and passed local validation. Success in a previous stage does not imply success in a subsequent stage, let alone correct field semantics.
- The keyword baseline runs the existing `keyword_baseline` directly from **the same batch of original prompts**, compared against the same set of approved answers. It has no API, JSON, Schema, or local intent card stages, and is not assigned a fictitious structural pass rate.

## Six Core Fields

- Each field reports both `end-to-end correct count/N` and `valid-only correct count/V`; correctness requires the predicted value to be **completely identical** to the approved answer. `{"relation":"at_least","value":0}` is not equal to exact `0`; `at_most` is not equal to the exact upper limit either; a `from_to` object is not equal to `single_target`. An entire six-field card is correct only when all six items are completely identical and the intent card is valid, serving as a strict supplementary metric and not independently representing the full comprehension capability.

For `current_valence`, `current_arousal`, `target_valence`, `target_arousal`, and `target_melodic_surprise`:

- **Explicitly expressed subset**: Approved answers are not `null` (range objects are also considered non-empty). Report the number of subset sentences `E`, the AI end-to-end correct count `C_E/E`, the correct count within valid cards `C_EV/E_V`, and the keyword baseline `C_B/E`.
- **Unspecified subset**: Approved answers are `null`. Report the number of subset sentences `U`, the AI end-to-end correct count `C_U/U`, the correct count within valid cards `C_UV/U_V`, and the keyword baseline `C_BU/U`. False positives `F/U_V` are counted **only for valid cards**: approved answer is `null` but the prediction is not `null`; invalid outputs are listed separately as `U-U_V` incomplete items and are not counted as false positives.

The V2 definition of `trajectory` is handled separately:

- **Explicitly requested song order** strictly means the approved answer is `{"type":"from_to",...}`; it must be explicit start and end points for song sequencing. Report the exact match count for the aforementioned explicit subset. `single_target` indicates there is a music mood/energy target but **no song order is requested**; `none` indicates there is no encodable music sequence or target. Neither counts as an explicit order.
- **Unspecified song order** subset contains the approved answers `single_target` and `none`. Report the exact match counts for each of these two respective values; false positive orders in valid cards `F/U_V` refer strictly to predictions of `from_to`. Misclassifying `single_target` as `none` (or vice versa) is still considered an error for this field, but is listed separately as a "no-order classification error" rather than being mixed into `from_to` false alarms. Invalid outputs are still only counted as incomplete.

The keyword baseline also evaluates field value exact equality and false positive conditions in the same explicit/unspecified subsets; all `N` sentences in the baseline have outputs without a "valid cards only" denominator.

## Constraints and Auxiliary Fields

- `requires_melody_present` is reported separately for end-to-end and valid-only accuracy counts, and is not included in the six-field full-card evaluation.
- `constraints` are scored separately: ① whether the presence of unguaranteed conditions is correctly judged, i.e., whether `constraints` being non-empty matches the approved answer's `expected_cannot_guarantee_constraint`; ② whether the extracted original-word **set** matches the approved answer exactly. Both report end-to-end `correct_count/N` and valid-only `correct_count/V`, and are not merged into the six-field full-card evaluation.
- Original-word item-by-item hits, false positives, and false negatives are calculated only within valid cards; expected original words corresponding to invalid calls are listed as "end-to-end incomplete" rather than masquerading as model false negatives. V2 does not verify `polarity` item-by-item, and the original-word set scoring does not use `polarity` as an approved standard answer.

Reports retain case IDs, predefined safety error categories, known field names, counts, tokens, and estimated costs; full model replies, API keys, request headers, or model-generated unknown fields and values must not be made public.
