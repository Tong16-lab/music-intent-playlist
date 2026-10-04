# Nine-field shorthand format: Controlled comparison of example development sets

This comparison modified two text locations: the prompt required for the output schema and the explanation shorthand format, rather than just changing a single API parameter. The model, 12 development examples, other request parameters, V2 answers, keyword baseline, and local validation remain consistent. Official test sentences were not called.

Candidate version: `compact-dev-v1`; Prompt SHA-256: `8d32673870f7798f8e46d63a13ea5d31fe5a66d813044fcfb13f526fa1412b2a`; Schema SHA-256: `c2d9e08fabefa74124fe3c22f9c74a991731a0bf67f42ca29e4ced9d2a44c344`.
Model: `google/gemini-3.5-flash-lite`; Singapore start time: `2026-10-03T18:07:39+08:00`.
Calls 12/12, early stopping: No; complete JSON 12/12, required structure complete 12/12, shorthand conversion completed 11/12, V2 local validation passed 9/12.
Failed to obtain a valid intent card 3 times (including API failures 0 times); groupings {"field_value": 2, "structure": 1}; safety error categories {"invalid_field_value": 3}.

## Comparison with Original Version and Keyword Baselines

| Metric | Original End-to-End | Candidate End-to-End | Original Valid-Only | Candidate Valid-Only | Same Keyword Baseline |
| --- | ---: | ---: | ---: | ---: | ---: |
| `current_valence` | 5/12 | 9/12 | 5/6 | 9/9 | 9/12 |
| `current_arousal` | 5/12 | 7/12 | 5/6 | 7/9 | 11/12 |
| `target_valence` | 6/12 | 7/12 | 6/6 | 7/9 | 9/12 |
| `target_arousal` | 5/12 | 4/12 | 5/6 | 4/9 | 8/12 |
| `target_melodic_surprise` | 5/12 | 8/12 | 5/6 | 8/9 | 11/12 |
| `trajectory` | 6/12 | 7/12 | 6/6 | 7/9 | 8/12 |
| Six-Field Full Card | 4/12 | 3/12 | 4/6 | 3/9 | 5/12 |
| requires_melody_present | 6/12 | 9/12 | 6/6 | 9/9 | — |
| Unsupported Condition Original Term Set All Correct | 1/12 | 3/12 | 1/6 | 3/9 | — |
| cannot_guarantee_constraint Status | 4/12 | 6/12 | 4/6 | 6/9 | — |

The end-to-end denominator includes calls without valid intent cards; the valid-output-only denominator includes only intent cards that passed conversion and V2 local validation. Invalid outputs are not counted as model false positives or false negatives for conditions. The keyword baseline still uses the project's original implementation.

## Unsupported Condition Verbatim Terms

Candidate end-to-end expected original terms: 7, unfinished: 4; among them, 0 belong to invalid intent cards.
Candidate valid-only output: hits 3, false positives 7, false negatives 4; denominator is 9 valid outputs, of which 7 are expected original terms.
Original valid-only output: hits 0, false positives 6, false negatives 4; denominator is 6 items.

## Errors and Usage

- `conversion`: 1 time
- `local_validation`: 2 times
- `dev_001`: valid; core field errors: current_arousal, target_valence, target_melodic_surprise; condition set error: yes.
- `dev_002`: valid; core field errors: current_arousal, target_arousal; condition set error: no.
- `dev_003`: valid; core field errors: target_arousal, trajectory; condition set error: no.
- `dev_004`:structure / invalid_field_value / target_valence
- `dev_005`: Valid; Core field errors: target_valence, target_arousal; Condition set error: Yes.
- `dev_006`:field_value / invalid_field_value / trajectory
- `dev_007`: Valid; Core field errors: target_arousal, trajectory; Condition set error: No.
- `dev_008`: Valid; Core field error: target_arousal; Condition set error: Yes.
- `dev_009`: Valid; Core field error: None; Condition set error: Yes.
- `dev_010`: Valid; Core field error: None; Condition set error: Yes.
- `dev_011`:field_value / invalid_field_value / trajectory.arousal
- `dev_012`: Valid; Core field error: None; Condition set error: Yes.

Candidate input/completion/total tokens: 15247/2085/17332; Available reasoning tokens: 0 (missing details 0 times).
Candidate estimated cost USD 0.009787; Calls with missing estimable data: 0. Original input/completion/total tokens: 16711/2232/18943; Original estimated cost USD 0.010593. Actual billing is subject to the service provider.

## Comparison Judgment

Format aspect: Original required structure 7/12, local valid 6/12; candidate required structure 12/12, conversion completed 11/12, local valid 9/12. This shows that the current candidate output more frequently satisfies the structural requirements, but we cannot conclude solely from a single development set comparison that the reason is the shorthand schema.
Intent aspect: Original six-field whole-card 4/12, candidate 3/12, keyword baseline 5/12. The candidate has more valid outputs, but the number of correct whole-card outputs did not increase accordingly; the valid output denominators also differ (original 6, candidate 9), so format success cannot be conflated with intent judgment success.
Constraint aspect: The candidate still has original-term false positives in 6/9 valid outputs, totaling 7; there are also 4 false negatives. The original valid outputs have 6 false positives and 4 false negatives. Since the valid sets differ between the two versions, the total count alone cannot be used to determine the change in the false positive rate.
Recommendation: Do not adopt the candidate format as the official runtime for now. It is worth keeping as a development prototype for structural improvement, but intent card clipping and constraint false positives must first be resolved on the development set before considering another round of controlled comparison; do not use these results to modify approved answers or infer official test scores.

This report only compares intent parsing on development examples. Structural or conversion success does not equal correct intent judgment; raw model predictions and conversion results reside only in local Git-ignored directories. No official pre-check tokens were generated, and no official tests were frozen or run.
