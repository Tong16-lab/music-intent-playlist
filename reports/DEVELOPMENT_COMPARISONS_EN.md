# Development-set evaluations — English reading copy

This page translates and consolidates the substantive findings in [`dev_evaluation.md`](dev_evaluation.md), [`compact_dev_evaluation.md`](compact_dev_evaluation.md), and [`compact_dev_v2_evaluation.md`](compact_dev_v2_evaluation.md). These are **development**, not formal-test, results. Each version processed the same twelve approved constructed requests once per case, without retries, using `google/gemini-3.5-flash-lite`. The model was sent each request with the fixed prompt/schema, not the answer key. All results were compared with the same keyword baseline.

| End-to-end result | Original full format | Compact v1 | Compact v2 | Keyword baseline |
| --- | ---: | ---: | ---: | ---: |
| Complete JSON | 12/12 | 12/12 | 12/12 | Not applicable |
| All required fields present | 7/12 | 12/12 | 12/12 | Not applicable |
| Compact conversion completed | Not applicable | 11/12 | 11/12 | Not applicable |
| Locally valid intent card | 6/12 | 9/12 | 8/12 | Not applicable |
| `current_valence` exact | 5/12 | 9/12 | 8/12 | 9/12 |
| `current_arousal` exact | 5/12 | 7/12 | 7/12 | 11/12 |
| `target_valence` exact | 6/12 | 7/12 | 7/12 | 9/12 |
| `target_arousal` exact | 5/12 | 4/12 | 5/12 | 8/12 |
| `target_melodic_surprise` exact | 5/12 | 8/12 | 8/12 | 11/12 |
| `trajectory` exact | 6/12 | 7/12 | 7/12 | 8/12 |
| All six fields exact | 4/12 | 3/12 | 4/12 | 5/12 |
| `requires_melody_present` exact | 6/12 | 9/12 | 8/12 | Not scored |
| Unsupported-condition source-phrase set exact | 1/12 | 3/12 | 5/12 | Not scored |
| `cannot_guarantee_constraint` status correct | 4/12 | 6/12 | 7/12 | Not scored |

The original produced five structure failures and one field-value failure, with no API failures. Compact v1 produced one conversion failure and two later validation failures, with no API failures. Compact v2 produced one conversion failure and three local-validation failures, including one missing-evidence case; again, there were no API failures. Among **valid** cards, six-field exact counts were 4/6, 3/9, and 4/8 respectively. The differing denominators mean a higher format-pass rate must not be described as improved interpretation. The keyword baseline's full-card result remained 5/12.

Compact v1 changed both the output schema and the instructions explaining compact notation, so it was not a one-parameter experiment. It improved structural completeness but reduced end-to-end six-field full-card accuracy from 4/12 to 3/12. Compact v2 retained the v1 schema, converter, model, request parameters, approved answers, baseline, and validator; only the prompt instructions changed. Its full-card score returned to 4/12, while unsupported-condition status improved to 7/12 and phrase-set exactness to 5/12. This was the version chosen **before** the frozen formal run. A twelve-case development comparison cannot establish a general improvement or identify a single causal component.

| Use/cost estimate | Original | Compact v1 | Compact v2 |
| --- | ---: | ---: | ---: |
| Input tokens | 16,711 | 15,247 | 17,887 |
| Completion tokens | 2,232 | 2,085 | 2,192 |
| Price-list estimate | US$0.010593 | US$0.009787 | US$0.010846 |

These are standard-rate estimates, not verified invoices. The source reports also provide case-level **safe error categories**, without publicly exposing the provider's full replies. In compact v2, `dev_001` failed due to missing current-valence evidence, `dev_004` due to structure, `dev_006` and `dev_011` due to field/path values; other valid cases still made semantic or unsupported-condition mistakes. The twelve development cases were used for tuning; their results are not substituted for the thirty-case formal score.
