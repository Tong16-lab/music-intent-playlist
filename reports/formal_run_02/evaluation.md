# PE6201 V2 Formal Synthesis Test Evaluation

Run ID: **Second official run after freezing**.
The first run only attempted 3/30 items and stopped due to three consecutive `network` failures, yielding 0 valid results; this report counts only the second run and does not merge the two invocations.

This report can only be generated after the author verifies the answers, freezes the test set, and authorizes formal execution. The evaluation subject is examples, not real user data; it does not measure the recommendation effectiveness of the official song library that has not yet been integrated.

Candidate: `compact-dev-v2`; Model: `google/gemini-3.5-flash-lite`; Scoring: `formal-scoring-v3`.
Prompt SHA-256: `1177a979ad7a42aa2a3d02c04563eed950c4ef74d9f081aa44bb1044742e3eb2`; Schema SHA-256: `c2d9e08fabefa74124fe3c22f9c74a991731a0bf67f42ca29e4ced9d2a44c344`; Singapore run time: `2026-10-03T19:38:01+08:00`.
Freeze record: `data/test_set_freeze.json`.

## Invocation and Validation Phase

Actual calls 30/30; API returned processable responses 30/30; Complete JSON 30/30; Required structure complete 30/30; Shorthand conversion completed 30/30; V2 local validation passed 28/30.
No valid intent cards 2/30; Early stop: No. Stage passing only indicates data is processable, not that the intent judgment is correct.

## Six core fields: Primary metrics

End-to-end denominator includes invalid calls; valid-only-output denominator contains only intent cards that passed conversion and local validation. Keyword baseline directly outputs the six fields for the same batch of raw utterances, without API, JSON, or structural pass rates.

| Field | AI End-to-End | AI Valid Only | Keyword Baseline |
| --- | ---: | ---: | ---: |
| `current_valence` | 26/30 | 26/28 | 27/30 |
| `current_arousal` | 26/30 | 26/28 | 29/30 |
| `target_valence` | 22/30 | 22/28 | 20/30 |
| `target_arousal` | 16/30 | 16/28 | 23/30 |
| `target_melodic_surprise` | 27/30 | 27/28 | 26/30 |
| `trajectory` | 23/30 | 23/28 | 18/30 |

## Categorized by whether approved answers explicitly express

Non-empty approved answers for the five nullable fields belong to the explicitly expressed subset, and scope objects are also considered non-empty. For `trajectory`, only approved answers of `from_to` count as an explicit requirement for **song order**; both `single_target` and `none` count as not explicitly requiring order. All correct counts require the predicted value to be an exact match with the approved answer.

| Field | Explicit subset sentence count | AI End-to-End | AI Valid Only | Keyword Baseline |
| --- | ---: | ---: | ---: | ---: |
| `current_valence` | 8 | 7/8 | 7/8 | 6/8 |
| `current_arousal` | 2 | 2/2 | 2/2 | 1/2 |
| `target_valence` | 11 | 7/11 | 7/11 | 1/11 |
| `target_arousal` | 11 | 5/11 | 5/11 | 4/11 |
| `target_melodic_surprise` | 7 | 4/7 | 4/5 | 3/7 |
| `trajectory` | 1 | 1/1 | 1/1 | 0/1 |

Unspecified subset: approved answers for five nullable fields are `null`; trajectory refers to **song order not explicitly required** (including `single_target`, `none`). AI incorrect entries are counted only within valid cards; failed calls are listed separately as incomplete. Incorrect trajectory entries specifically refer to unauthorized output of `from_to`, while confusing `single_target` with `none` is listed separately.

| Field | Unspecified Subset Utterances | AI End-to-End Exact | AI Valid-Only Exact | AI Valid Incorrect | Invalid Incomplete | Keyword Baseline Exact | Baseline Incorrect |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `current_valence` | 22 | 19/22 | 19/20 | 1/20 | 2 | 21/22 | 1/22 |
| `current_arousal` | 28 | 24/28 | 24/26 | 2/26 | 2 | 28/28 | 0/28 |
| `target_valence` | 19 | 15/19 | 15/17 | 2/17 | 2 | 19/19 | 0/19 |
| `target_arousal` | 19 | 11/19 | 11/17 | 6/17 | 2 | 19/19 | 0/19 |
| `target_melodic_surprise` | 23 | 23/23 | 23/23 | 0/23 | 0 | 23/23 | 0/23 |
| `trajectory` | 29 | 22/29 | 22/27 | 2/27 | 2 | 18/29 | 0/29 |
No sequential classification errors: AI 3/27 valid cards; Keyword baseline 11/29.

## Strict Supplementary Metrics and Unsupported Conditions

Six-field whole-card all correct: AI end-to-end 11/30; valid only 11/28; keyword baseline 12/30. Whole card is a strict supplementary metric and does not independently represent comprehension capability.
`requires_melody_present`: AI end-to-end 28/30; valid only 28/28.

| Unsupported conditional metrics | AI end-to-end | AI valid only |
| --- | ---: | ---: |
| Correctly judge whether unguaranteed conditions exist | 27/30 | 27/28 |
| Intercepted original term set completely identical | 24/30 | 24/28 |
Original terms of valid cards only: exact hits 6, false positives 5, false negatives 7.
End-to-end expected original terms 14, uncompleted 8; of which 1 came from an invalid call, not counted as a model original term false negative.

## Usage, Failures, and Limits

Input/Completed/Total tokens: 44616/4887/49503; Reasoner tokens available: 0 (missing details 0 times).
Estimated at standard rates USD 0.025602; times lacking estimable data: 0. Actual billing is subject to the service provider.
Failed groups in actual calls: {"field_value": 2}; Safety error categories: {"invalid_field_value": 2}.

- `test_001`: valid; error core fields: current_arousal, target_valence; unsupported conditional state error: False; original term set error: False.
- `test_002`: valid; error core fields: target_arousal; unsupported conditional state error: False; original term set error: False.
- `test_003`: valid; error core fields: target_arousal, trajectory; unsupported conditional state error: False; original term set error: True.
- `test_004`: Valid; erroneous core fields: current_arousal, target_melodic_surprise; unsupported conditional state error: False; original term set error: False.
- `test_005`: No valid card / `invalid_field_value`
- `test_007`: Valid; erroneous core field: target_arousal; unsupported conditional state error: False; original term set error: False.
- `test_008`: valid; error core field: target_arousal; unsupported conditional state error: False; original term set error: False.
- `test_010`: valid; error core fields: current_valence, target_valence, trajectory; unsupported conditional state error: False; original term set error: False.
- `test_011`: valid; error core field: target_arousal; unsupported conditional state error: False; original term set error: False.
- `test_012`: valid; error core field: none; unsupported conditional state error: False; original term set error: True.
- `test_013`: valid; error core field: target_valence, target_arousal; unsupported conditional state error: False; original term set error: False.
- `test_014`: valid; error core field: target_valence, target_arousal, trajectory; unsupported conditional state error: False; original term set error: False.
- `test_015`: No valid cards / `invalid_field_value`
- `test_017`: Valid; incorrect core field: target_arousal; unsupported conditional state error: False; original term set error: False.
- `test_018`: Valid; incorrect core field: None; unsupported conditional state error: False; original term set error: True.
- `test_020`: Valid; Error core field: target_arousal; Unsupported conditional state error: False; Original term set error: False.
- `test_021`: Valid; Error core fields: target_arousal, trajectory; Unsupported conditional state error: True; Original term set error: True.
- `test_024`: Valid; Error core field: target_valence; Unsupported conditional state error: False; Original term set error: False.
- `test_025`: Valid; Error core field: trajectory; Unsupported conditional state error: False; Original term set error: False.
- `test_028`: Valid; Error core field: current_valence, target_arousal; Unsupported conditional state error: False; Original term set error: False.
- `test_029`: Valid; Error core field: target_valence, target_arousal; Unsupported conditional state error: False; Original term set error: False.

Keyword baseline does not require JSON; structural pass rate is not comprehension accuracy. Complete model predictions reside only in the local Git-ignored directory, and public reports do not contain keys, request headers, or complete responses. After freezing, approved answers must not be stealthily modified to carry over this score.
