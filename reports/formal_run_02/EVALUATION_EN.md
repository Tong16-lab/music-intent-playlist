# Completed formal run 2: detailed English result

This is an English rendering of the preserved Chinese `evaluation.md` and `evaluation.json`, not a new run or a recalculation with translated inputs. The first run called three cases and stopped after three network failures; it is separate and must not be pooled with this one. The 30 approved Chinese requests are constructed examples, not statements collected from participants. This run does not by itself measure recommendation quality.

Run configuration: candidate `compact-dev-v2`; model `google/gemini-3.5-flash-lite`; scoring `formal-scoring-v3`; started 2026-10-03 19:38:01 Singapore time. Prompt SHA-256 `1177a979ad7a42aa2a3d02c04563eed950c4ef74d9f081aa44bb1044742e3eb2`; schema SHA-256 `c2d9e08fabefa74124fe3c22f9c74a991731a0bf67f42ca29e4ced9d2a44c344`; frozen answers recorded in `data/test_set_freeze.json`.

## Call and validation stages

Calls attempted **30/30**; processable responses **30/30**; complete JSON **30/30**; required structure complete **30/30**; compact conversion complete **30/30**; local V2 validation passed **28/30**. Two cards were invalid; there was no early stop. Passing a structural stage does not establish correct intent interpretation.

## Six core fields

End-to-end scores include invalid cards in the denominator of 30. “Valid-only” scores use 28 valid cards. The keyword baseline directly produces six fields from the same 30 Chinese requests and is compared with the same approved answers; it has no API or JSON stage.

| Field | Model end-to-end | Model valid-only | Keyword baseline |
| --- | ---: | ---: | ---: |
| `current_valence` | 26/30 | 26/28 | 27/30 |
| `current_arousal` | 26/30 | 26/28 | 29/30 |
| `target_valence` | 22/30 | 22/28 | 20/30 |
| `target_arousal` | 16/30 | 16/28 | 23/30 |
| `target_melodic_surprise` | 27/30 | 27/28 | 26/30 |
| `trajectory` | 23/30 | 23/28 | 18/30 |

## Stated versus unstated approved values

For the five nullable fields, “stated” means the approved value is not null, including a range object. For `trajectory`, only approved `from_to` is a stated **song-order** request; `single_target` and `none` are in the no-explicit-order group. A prediction is exact only if it equals the approved value; a range is not interchangeable with an exact point.

| Field | Stated cases | Model end-to-end | Model valid-only | Baseline |
| --- | ---: | ---: | ---: | ---: |
| `current_valence` | 8 | 7/8 | 7/8 | 6/8 |
| `current_arousal` | 2 | 2/2 | 2/2 | 1/2 |
| `target_valence` | 11 | 7/11 | 7/11 | 1/11 |
| `target_arousal` | 11 | 5/11 | 5/11 | 4/11 |
| `target_melodic_surprise` | 7 | 4/7 | 4/5 | 3/7 |
| `trajectory` | 1 | 1/1 | 1/1 | 0/1 |

For an unstated field, a model-supplied value is a false fill only when the card is valid. Invalid cards are unfinished, not model false fills. For trajectory, only an invented `from_to` is a false song-order path; confusing `single_target` and `none` is reported separately.

| Field | Unstated cases | Model end-to-end exact | Model valid-only exact | Model false fills on valid cards | Invalid/unfinished | Baseline exact | Baseline false fills |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `current_valence` | 22 | 19/22 | 19/20 | 1/20 | 2 | 21/22 | 1/22 |
| `current_arousal` | 28 | 24/28 | 24/26 | 2/26 | 2 | 28/28 | 0/28 |
| `target_valence` | 19 | 15/19 | 15/17 | 2/17 | 2 | 19/19 | 0/19 |
| `target_arousal` | 19 | 11/19 | 11/17 | 6/17 | 2 | 19/19 | 0/19 |
| `target_melodic_surprise` | 23 | 23/23 | 23/23 | 0/23 | 0 | 23/23 | 0/23 |
| `trajectory` | 29 | 22/29 | 22/27 | 2/27 | 2 | 18/29 | 0/29 |

Among valid cards without explicit song order, the model additionally confused `single_target` and `none` in **3/27** cases; the baseline did so in **11/29**.

## Strict supplementary measures and unsupported conditions

All six core fields exact on one card: model **11/30** end-to-end and **11/28** valid-only; baseline **12/30**. This strict card score is supplementary and does not alone represent the quality of all interpretation. `requires_melody_present` was exact **28/30** end-to-end and **28/28** valid-only.

| Unsupported-condition measure | Model end-to-end | Model valid-only |
| --- | ---: | ---: |
| Correct existence/non-existence decision | 27/30 | 27/28 |
| Exact set of quoted source phrases | 24/30 | 24/28 |

On valid cards, phrase-level counts were **6 exact hits, 5 false positives, 7 misses**. Fourteen phrases were expected across the full 30 cases; **8** were unfinished end-to-end, with **1** of those arising from an invalid card rather than a model phrase-level miss.

## Failures, usage, and interpretation

Only `test_005` and `test_015` had invalid cards; both were categorized `invalid_field_value`. The detailed preserved report lists the other case IDs and which fields or constraint phrases disagreed with approved answers. Notable examples include `test_010` (current/target valence and trajectory) and `test_017` (target arousal). These are observed disagreements under the predeclared rubric, not evidence that every alternative reading is impossible.

Input/completion/total tokens: **44,616 / 4,887 / 49,503**. Returned reasoning tokens totaled 0, with no missing usage breakdown. Estimated cost at the recorded list price: **USD 0.025602**; the actual bill is not established by this estimate. All attempted-call failures were local field-value failures, not API or structure failures in this run. Raw provider replies and credentials are not in the public report; `validated_cards_for_audit.jsonl` releases only approved-structure cards and fixed error categories for reproducing the recommendation routing audit. Do not edit frozen answers and present the old run as if it had used new answers.
