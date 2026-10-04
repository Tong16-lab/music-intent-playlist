# compact-dev-v2: example development set comparison modifying prompts only

This round reuses the shorthand v1 schema, converter, model, request parameters, V2 approved answers, keyword baseline, and local validator; only general intent determination notes are added. All requests send only a single example development utterance, without sending answers. No formal test sentence design rules were used or calls executed.

Version: `compact-dev-v2`; v2 prompt SHA-256: `1177a979ad7a42aa2a3d02c04563eed950c4ef74d9f081aa44bb1044742e3eb2`; v1 prompt SHA-256: `8d32673870f7798f8e46d63a13ea5d31fe5a66d813044fcfb13f526fa1412b2a`; joint schema SHA-256 for both versions: `c2d9e08fabefa74124fe3c22f9c74a991731a0bf67f42ca29e4ced9d2a44c344`.
Model: `google/gemini-3.5-flash-lite`; Singapore start time: `2026-10-03T18:31:04+08:00`.
Pre-estimated cost USD 0.013734 (based on v1 measured data, assuming 2 input tokens per new character and a 25% increase in completion tokens).
Actual calls 12/12; early stop: no. Complete JSON 12/12; required structure complete 12/12; shorthand conversion completed 11/12; V2 local validation passed 8/12.
No valid cards 4 times, including API failures 0 times; failure grouping {"evidence": 1, "field_value": 2, "structure": 1}; safety error categories {"invalid_field_value": 3, "missing_evidence": 1}.

## Three Versions and Same-Keyword Baseline

| Metric | Original End-to-End | Abbreviated v1 End-to-End | Prompt v2 End-to-End | Same-Keyword Baseline |
| --- | ---: | ---: | ---: | ---: |
| `current_valence` | 5/12 | 9/12 | 8/12 | 9/12 |
| `current_arousal` | 5/12 | 7/12 | 7/12 | 11/12 |
| `target_valence` | 6/12 | 7/12 | 7/12 | 9/12 |
| `target_arousal` | 5/12 | 4/12 | 5/12 | 8/12 |
| `target_melodic_surprise` | 5/12 | 8/12 | 8/12 | 11/12 |
| `trajectory` | 6/12 | 7/12 | 7/12 | 8/12 |
| Six-Field Full Card | 4/12 | 3/12 | 4/12 | 5/12 |
| requires_melody_present | 6/12 | 9/12 | 8/12 | — |
| Unsupported conditional exact original word set match | 1/12 | 3/12 | 5/12 | — |
| cannot_guarantee_constraint state correct | 4/12 | 6/12 | 7/12 | — |

The denominators for valid outputs only are 6 for the original, 9 for shorthand v1, and 8 for prompt v2, respectively; the table below measures only cards that passed conversion and local validation.

| Metric | Original only valid | Abbreviation v1 only valid | Prompt v2 only valid |
| --- | ---: | ---: | ---: |
| `current_valence` | 5/6 | 9/9 | 8/8 |
| `current_arousal` | 5/6 | 7/9 | 7/8 |
| `target_valence` | 6/6 | 7/9 | 7/8 |
| `target_arousal` | 5/6 | 4/9 | 5/8 |
| `target_melodic_surprise` | 5/6 | 8/9 | 8/8 |
| `trajectory` | 6/6 | 7/9 | 7/8 |
| Six-field full card | 4/6 | 3/9 | 4/8 |
| Unsupported condition original word set all correct | 1/6 | 3/9 | 5/8 |
| cannot_guarantee_constraint state correct | 4/6 | 6/9 | 7/8 |

The end-to-end denominator includes calls without valid cards; such calls are not counted as model original-word false positives or false negatives. Complete format only indicates that the output is parsable, not that the intent judgment is correct.

## Unsupported conditions: State and original word are scored separately

Status correct (end-to-end): Original 4/12, shorthand v1 6/12, v2 7/12.
Original term set completely identical (end-to-end): Original 1/12, shorthand v1 3/12, v2 5/12.
v2 valid output only: Expected original terms 7; exact hits 5, false positives 3, false negatives 2 (8 valid cards). End-to-end incomplete original terms 2, of which 0 came from cards without valid output.

## Security Error Summary

- `conversion`: 1 time
- `local_validation`: 3 times
- `dev_001`:evidence / missing_evidence / current_valence
- `dev_002`: valid; core field error: current_arousal, target_arousal; original term set error: no.
- `dev_004`:structure / invalid_field_value / target_valence
- `dev_005`: Valid; Core field error: target_arousal; Original term set error: No.
- `dev_006`:field_value / invalid_field_value / trajectory
- `dev_007`: Valid; Core field error: target_valence, trajectory; Original term set error: No.
- `dev_008`: Valid; Core field error: None; Original term set error: Yes.
- `dev_009`: valid; core field errors: none; original term set error: yes.
- `dev_010`: valid; core field errors: target_arousal; original term set error: no.
- `dev_011`:field_value / invalid_field_value / trajectory.arousal
- `dev_012`: valid; core field errors: none; original term set error: yes.

## Usage and Boundaries

v2 input / completion / total tokens: 17887 / 2192 / 20079; obtainable reasoning tokens: 0 (missing breakdown 0 times).
v2 estimated cost USD 0.010846; missing estimable data 0 times. Original USD 0.010593; abbreviation v1 USD 0.009787. Actual billing is subject to the service provider.
Raw model predictions and conversion cards exist only locally in private directories ignored by Git; public reports do not include complete raw responses, request headers, or keys. Not connected to formal runtime, frozen, or evaluating the formal test set.
