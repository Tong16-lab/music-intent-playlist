# PE6201 V2 Development Set example Sentence Evaluation

Only uses the 12 development sentences approved by the author; this is not a formal test score, nor is it real user data. Each request contains only the original utterance, fixed runtime prompts, and schema, without answers.

Model: `google/gemini-3.5-flash-lite`; Singapore start time: `2026-10-03T17:29:58+08:00`.
Actual calls 12/12; uncalled 0; complete JSON 12/12; required structure complete 7/12; local valid intent cards 6/12.
API failures 0; format/structure failures 5; evidence failures 0; field value failures 1.
In addition, 5/6 local valid outputs do not completely match the approved answer; this is an intent judgment discrepancy and is not classified as a format or evidence failure.
Early stopping: No.

Failure groups have been corrected offline based on the saved safety structure flags; no model re-invocation or gold standard modification was performed.

## Six Core Fields

| Field | Dev Set Coverage (Correct / 12) | End-to-End Called | Valid Output Only | Keyword Baseline (Called) |
| --- | ---: | ---: | ---: | ---: |
| `current_valence` | 5/12 | 5/12 | 5/6 | 9/12 |
| `current_arousal` | 5/12 | 5/12 | 5/6 | 11/12 |
| `target_valence` | 6/12 | 6/12 | 6/6 | 9/12 |
| `target_arousal` | 5/12 | 5/12 | 5/6 | 8/12 |
| `target_melodic_surprise` | 5/12 | 5/12 | 5/6 | 11/12 |
| `trajectory` | 6/12 | 6/12 | 6/6 | 8/12 |
| All Six Fields Complete | 4/12 | 4/12 | 4/6 | 5/12 |
| requires_melody_present | 6/12 | 6/12 | 6/6 | — |
| Unsupported Condition Original Term Set All Correct | 1/12 | 1/12 | 1/6 | — |
| cannot_guarantee_constraint status | 4/12 | 4/12 | 4/6 | — |

The dev-set coverage column marks uncalled sentences as incomplete, which does not mean the model judged those sentences incorrectly. The end-to-end column counts sentences that were called but yielded no valid intent cards into the denominator; the valid-output-only column measures only intent cards that passed local validation.

## Unsupported Condition Verbatim Terms

Expected original words for called sentences: 7; end-to-end incomplete: 7, of which 3 belong to sentences with no valid intent cards.
Effective output only: 0 hits, 6 false positives, 4 false negatives (calculated within the 6 effective outputs only).

## Security Error Summary

- `invalid_field_value`: 6 times

## Sentence-by-Sentence Safety Summary

- `dev_001`: valid; core field errors: current_valence, current_arousal, target_melodic_surprise; unsupported condition set error: yes.
- `dev_002`:structure / `invalid_field_value` / `target_arousal`
- `dev_003`:structure / `invalid_field_value` / `target_arousal`
- `dev_004`: valid; core field errors: none; unsupported condition set error: no.
- `dev_005`:structure / `invalid_field_value` / `target_valence`
- `dev_006`:field_value / `invalid_field_value` / `trajectory`
- `dev_007`:structure / `invalid_field_value` / `trajectory.arousal`
- `dev_008`: valid; core field errors: target_arousal; unsupported condition set error: yes.
- `dev_009`: Valid; Core field error: None; Unsupported condition set error: Yes.
- `dev_010`: Valid; Core field error: None; Unsupported condition set error: Yes.
- `dev_011`:structure / `invalid_field_value` / `target_arousal`
- `dev_012`: Valid; Core field error: None; Unsupported condition set error: Yes.

## Usage and Scope

Input / Completion / Total tokens: 16711 / 2232 / 18943; Total obtainable reasoning tokens: 0 (missing breakdown 0 times).
Estimated cost: USD 0.010593; Calls with missing cost-estimation data: 0 times. Actual billing is subject to the service provider.
No audio was downloaded, and the actual music library recommendation effectiveness was not evaluated. The test set was not frozen, and the 30 formal tests were not run.
