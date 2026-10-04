# English results summary — completed second formal run

This is a readable summary of the preserved result artifacts in `reports/formal_run_02/`. The first formal attempt stopped after three network failures and is stored in `reports/evaluation.md`; it is not pooled with this completed run. The 30 Chinese test requests and answers were frozen before the completed run. The requests are author-reviewed examples, not participant statements.

| Measure | Language-model pipeline | Keyword baseline |
| --- | ---: | ---: |
| Requests attempted | 30/30 | 30/30 |
| Structurally complete outputs | 30/30 | Not applicable |
| Cards passing local validation | 28/30 | Not applicable |
| Current valence exact | 26/30 | 27/30 |
| Current arousal exact | 26/30 | 29/30 |
| Target valence exact | 22/30 | 20/30 |
| Target arousal exact | 16/30 | 23/30 |
| Target melodic surprise exact | 27/30 | 26/30 |
| Trajectory exact | 23/30 | 18/30 |
| All six fields exact | 11/30 | 12/30 |

The 11/30 versus 12/30 full-card result is a narrow observed difference, not a general winner. On explicitly stated target valence, the model scored 7/11 versus 1/11; on unstated target valence, the baseline scored 19/19 versus the model's 15/19 end-to-end. Target arousal is the clearest weakness of the model pipeline. Scores for valid model cards alone use 28 as the denominator and are listed in the preserved detailed report. The two invalid cards count as unfinished in the 30-case end-to-end figures.

Unsupported-condition existence was correct in 27/30 cases, and the exact set of source phrases in 24/30. The saved-card routing audit gave 21 three-track recommendations, 7 `cannot_guarantee_constraint` refusals, and 2 invalid cards; no catalog-shortage case occurred. Routing is not listening quality. The separate author listening review found 10/15 fully fitting track positions and only 1/5 fully fitting complete playlists.

The run used 44,616 input and 4,887 completion tokens. Its price-list estimate was US$0.025602, not a verified invoice. Raw provider replies stay in a locally ignored directory; the released, validated cards used in the routing audit are checked in as `reports/formal_run_02/validated_cards_for_audit.jsonl`. Public artifacts also retain counts, approved data, fixed prompt/schema, and safe error categories. See [the evaluation explainer](../docs/EVALUATION_EXPLAINER.md) for the protocol and its validity limits.
