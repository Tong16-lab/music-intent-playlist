# Evaluation explainer

## Questions and comparison

1. Can the language-model pipeline return a locally valid intent card with exact phrases drawn from the request?
2. On the same reviewed 30 Chinese requests, how often does each of six core fields match its frozen answer exactly, compared with the keyword baseline?
3. Does the resulting card let the deterministic selector produce three linked tracks without claiming to satisfy a condition that is not in the catalog?
4. Do a small number of author-listened playlists feel coherent? This is a separate qualitative check, not a formal user-experience score.

The six core fields are current valence, current arousal, target valence, target arousal, target melodic surprise, and trajectory. `requires_melody_present` and unsupported constraints are reported separately. “Not stated” is a legitimate answer; a plausible guess is still wrong when the request does not specify that field. Exact card correctness means all six fields match, so it is stricter than any one field's score.

## Protocol and files

Twelve development requests supported choosing the `compact-dev-v2` prompt and compact response format. The frozen 30-case test set was then run once per request in the completed second formal run with `google/gemini-3.5-flash-lite`. The first formal run attempted three requests and stopped after network errors; it is archived separately and does not contribute accuracy numbers. Do not merge the two runs or treat the failed run's zero valid cards as a measure of model comprehension.

The scoring specification is `data/FORMAL_SCORING_V3.md`; the implementation is `src/music_intent/scoring_v3.py`; the keyword comparator is in `src/music_intent/evaluation.py`; the runner is `scripts/evaluate.py`. `reports/formal_run_02/evaluation.json` and `.md` contain the recorded formal results. The English summary is `reports/FORMAL_RESULTS_SUMMARY_EN.md`. The prompt and schema actually used are `data/COMPACT_DEV_PROMPT_v2.txt` and `data/COMPACT_DEV_SCHEMA_v1.json`. They remain in their operational language to preserve the evaluated setup.

Every attempted request counts in the end-to-end denominator of 30, including invalid cards. Valid-only scores use 28 as their denominator. For a field not specified in the approved answer, a model-invented value is a false fill. For trajectory, only `from_to` is an explicit song-order request; `single_target` does not imply song order. Unsupported conditions are checked both as an existence decision and as an exact set of phrases. A failed or invalid card is unfinished, not a phrase-level false negative. The baseline uses the same 30 inputs and frozen answers, but has no API or JSON-validation stage.

`scripts/audit_formal_recommendations.py --check` audits routing over the released, validated case cards in `reports/formal_run_02/validated_cards_for_audit.jsonl` and the 35-track catalog without calling the model. The release omits raw provider text, headers, and secrets. Its 21/7/2 routing counts do **not** score musical fit. Four fixed offline demos exercise exploration, calm, three-step arousal, and melodic variation; they start with prewritten intent cards, so they do not test language comprehension. The author also listened to five deterministic picks from the 21 ready formal playlists and reviewed two refusals. The listening judgments are subjective, from one person, post-run, and not population estimates.

## Main threats to validity

The requests are constructed and author-reviewed rather than observed participant statements. Some test cases informed earlier rule discussions, so this is not a pristine unseen-design benchmark even though its answers were frozen before the completed run. The 30-case sample is too small for a general superiority claim, especially with an 11-versus-12 exact-card difference. Exact-match grading can penalize close but defensible interpretations, while the keyword baseline can score highly by leaving unstated fields empty. The listener review lacks an independent panel, random assignment, and a recommendation-quality baseline. Catalog labels may be disputed, and external links may change. The study demonstrates a reproducible end-to-end prototype and exposes its weaknesses; it does not demonstrate improved musical taste or real-world listener satisfaction.
