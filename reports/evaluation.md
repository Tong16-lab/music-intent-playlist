# PE6201 V2 Formal Synthesis Test Evaluation

**Execution Status Notes (added after report generation, scores or answers unchanged):** The first three calls all failed during the network stage, and no processable API response was obtained; the program stopped according to preset rules, and the remaining 27 sentences were not called. The AI's `0/30` in the table indicates that the end-to-end process was not completed, **and cannot be interpreted as the model being completely wrong on all 30 sentences in intent recognition, nor can it be compared in capability against the keyword baseline**. The denominator for valid outputs is 0, so semantic accuracy was not evaluated. The service provider did not return token or billing usage; the USD 0.000000 below is merely a calculation subtotal for obtainable usage, and whether actual charges apply **cannot be confirmed**.

This report can only be generated after the author verifies the answers, freezes the test set, and authorizes formal execution. The evaluation subject is examples, not real user data; it does not measure the recommendation effectiveness of the official song library that has not yet been integrated.

Candidate: `compact-dev-v2`; Model: `google/gemini-3.5-flash-lite`; Scoring: `formal-scoring-v3`.
Prompt SHA-256: `1177a979ad7a42aa2a3d02c04563eed950c4ef74d9f081aa44bb1044742e3eb2`; Schema SHA-256: `c2d9e08fabefa74124fe3c22f9c74a991731a0bf67f42ca29e4ced9d2a44c344`; Singapore runtime: `2026-10-03T19:15:07+08:00`.
Freeze record: `data/test_set_freeze.json`.

## Invocation and Validation Phase

Actual calls 3/30; API returned processable responses 0/30; Complete JSON 0/30; Required structure complete 0/30; Abbreviation conversion complete 0/30; V2 local validation passed 0/30.
No valid intent cards 30/30; early stopping: yes. Phase pass only indicates data is processable, not that intent judgment is correct.

## Six core fields: Primary metrics

End-to-end denominator includes invalid calls; valid-only-output denominator contains only intent cards that passed conversion and local validation. Keyword baseline directly outputs the six fields for the same batch of raw utterances, without API, JSON, or structural pass rates.

| Field | AI End-to-End | AI Valid Only | Keyword Baseline |
| --- | ---: | ---: | ---: |
| `current_valence` | 0/30 | Not evaluated (denominator 0) | 27/30 |
| `current_arousal` | 0/30 | Not evaluated (denominator 0) | 29/30 |
| `target_valence` | 0/30 | Unevaluated (Denominator 0) | 20/30 |
| `target_arousal` | 0/30 | Unevaluated (Denominator 0) | 23/30 |
| `target_melodic_surprise` | 0/30 | Unevaluated (Denominator 0) | 26/30 |
| `trajectory` | 0/30 | Unevaluated (denominator 0) | 18/30 |

## Categorized by whether approved answers explicitly express

Non-empty approved answers for the five nullable fields belong to the explicitly expressed subset, and scope objects are also considered non-empty. For `trajectory`, only approved answers of `from_to` count as an explicit requirement for **song order**; both `single_target` and `none` count as not explicitly requiring order. All correct counts require the predicted value to be an exact match with the approved answer.

| Field | Explicit subset sentence count | AI End-to-End | AI Valid Only | Keyword Baseline |
| --- | ---: | ---: | ---: | ---: |
| `current_valence` | 8 | 0/8 | Not evaluated (denominator 0) | 6/8 |
| `current_arousal` | 2 | 0/2 | Not evaluated (denominator 0) | 1/2 |
| `target_valence` | 11 | 0/11 | Unevaluated (denominator 0) | 1/11 |
| `target_arousal` | 11 | 0/11 | Unevaluated (denominator 0) | 4/11 |
| `target_melodic_surprise` | 7 | 0/7 | Unevaluated (denominator 0) | 3/7 |
| `trajectory` | 1 | 0/1 | Unevaluated (denominator 0) | 0/1 |

Unspecified subset: approved answers for five nullable fields are `null`; trajectory refers to **song order not explicitly required** (including `single_target`, `none`). AI incorrect entries are counted only within valid cards; failed calls are listed separately as incomplete. Incorrect trajectory entries specifically refer to unauthorized output of `from_to`, while confusing `single_target` with `none` is listed separately.

| Field | Unspecified Subset Utterances | AI End-to-End Exact | AI Valid-Only Exact | AI Valid Incorrect | Invalid Incomplete | Keyword Baseline Exact | Baseline Incorrect |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `current_valence` | 22 | 0/22 | Unevaluated (denominator 0) | Unevaluated (denominator 0) | 22 | 21/22 | 1/22 |
| `current_arousal` | 28 | 0/28 | Unevaluated (denominator 0) | Unevaluated (denominator 0) | 28 | 28/28 | 0/28 |
| `target_valence` | 19 | 0/19 | Unevaluated (denominator 0) | Unevaluated (denominator 0) | 19 | 19/19 | 0/19 |
| `target_arousal` | 19 | 0/19 | Not evaluated (denominator 0) | Not evaluated (denominator 0) | 19 | 19/19 | 0/19 |
| `target_melodic_surprise` | 23 | 0/23 | Not evaluated (denominator 0) | Not evaluated (denominator 0) | 23 | 23/23 | 0/23 |
| `trajectory` | 29 | 0/29 | Not evaluated (denominator 0) | Not evaluated (denominator 0) | 29 | 18/29 | 0/29 |
Unordered classification error: AI 0/0 valid cards; keyword baseline 11/29.

## Strict Supplementary Metrics and Unsupported Conditions

Six-field whole-card completely correct: AI end-to-end 0/30; valid only unevaluated (denominator 0); keyword baseline 12/30. The whole card is a strict supplementary metric and does not independently represent comprehension ability.
`requires_melody_present`: AI end-to-end 0/30; valid only unassessed (denominator 0).

| Unsupported conditional metrics | AI end-to-end | AI valid only |
| --- | ---: | ---: |
| Whether inability to guarantee conditions is correctly judged | 0/30 | Unassessed (denominator 0) |
| Extracted original term set completely matches | 0/30 | Not evaluated (denominator 0) |
No valid cards; original term hit/false positive/false negative not evaluated.
End-to-end expected original terms: 14, uncompleted: 14; among them, 14 come from invalid calls and are not counted as model original term false negatives.

## Usage, Failures, and Limits

Input/Completion/Total tokens: 0/0/0; Reasonability tokens available: 0 (missing breakdown 3 times).
Estimated at standard rates USD 0.000000; missing estimable data 3 times. Actual billing is subject to the service provider.
Failed groups in actual calls: {"api": 3}; Security error categories: {"network": 3}.

- `test_001`: No valid card / `network`
- `test_002`: No valid card / `network`
- `test_003`:No valid cards / `network`
- `test_004`:No valid cards / `not_attempted_after_stop`
- `test_005`:No valid cards / `not_attempted_after_stop`
- `test_006`: No valid card / `not_attempted_after_stop`
- `test_007`: No valid card / `not_attempted_after_stop`
- `test_008`: No valid card / `not_attempted_after_stop`
- `test_009`:No valid cards / `not_attempted_after_stop`
- `test_010`:No valid cards / `not_attempted_after_stop`
- `test_011`:No valid cards / `not_attempted_after_stop`
- `test_012`: No valid card / `not_attempted_after_stop`
- `test_013`: No valid card / `not_attempted_after_stop`
- `test_014`: No valid card / `not_attempted_after_stop`
- `test_015`: No valid cards / `not_attempted_after_stop`
- `test_016`: No valid cards / `not_attempted_after_stop`
- `test_017`: No valid cards / `not_attempted_after_stop`
- `test_018`: No valid cards / `not_attempted_after_stop`
- `test_019`: No valid cards / `not_attempted_after_stop`
- `test_020`: No valid cards / `not_attempted_after_stop`
- `test_021`:No valid cards / `not_attempted_after_stop`
- `test_022`:No valid cards / `not_attempted_after_stop`
- `test_023`:No valid cards / `not_attempted_after_stop`
- `test_024`:No valid card / `not_attempted_after_stop`
- `test_025`:No valid card / `not_attempted_after_stop`
- `test_026`:No valid card / `not_attempted_after_stop`
- `test_027`:No valid cards / `not_attempted_after_stop`
- `test_028`:No valid cards / `not_attempted_after_stop`
- `test_029`:No valid cards / `not_attempted_after_stop`
- `test_030`: No valid card / `not_attempted_after_stop`

Keyword baseline does not require JSON; structural pass rate is not comprehension accuracy. Complete model predictions reside only in the local Git-ignored directory, and public reports do not contain keys, request headers, or complete responses. After freezing, approved answers must not be stealthily modified to carry over this score.
