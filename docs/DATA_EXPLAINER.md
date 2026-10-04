# Data explainer

## What is in the repository

The recorded experiment used 42 author-reviewed Chinese request examples: 12 development cases and 30 formal-test cases. They are **not statements collected from participants**. Persona IDs P01–P14 are grouping IDs, not recruited people. The current files present English translations of those examples. The set supports a controlled comparison of specified input types, but cannot estimate how often people use these expressions or how the system will perform on a population of listeners.

`data/user_intents_v2_review.tsv` is the English reading table for fields and evidence. Its synchronized exports are `data/synthetic_intents_dev.csv`, `data/synthetic_intents_test.csv`, and `data/unsupported_conditions_test.csv`, with 12, 30, and 30 rows. English evidence spans were aligned to the translated sentences for readability and internal consistency; they were not the spans scored in the formal run. The exact approved Chinese requests, answers, and source-phrase evidence used in that run are in [commit `a39e3fc`](https://github.com/Tong16-lab/music-intent-playlist/tree/a39e3fc). Replacing model inputs with English would create a different experiment.

The original formal-test TSV and two CSV files were frozen on 2026-10-03 at 19:14:46 Singapore time. `data/test_set_freeze.json` records SHA-256 hashes of those **original bytes in commit `a39e3fc`**. The current English translations necessarily have different hashes. `python3 scripts/sync_v2_answers.py check` checks consistency among the current translated tables; `python3 scripts/verify_historical_freeze.py` checks the original freeze directly from Git history. The first formal run stopped after three connection failures and is retained separately from the completed second run.

## Music catalog

`data/catalog.csv` has 35 distinct MTG-Jamendo track IDs, titles, artists, original track-page links, source mood/theme tags, and four project-specific listening labels. `data/catalog_source_snapshot.md` contains the two 35-row source tables needed to rebuild that CSV without any file outside the repository. The external dataset revision is `cafd8e20c265ed84f1e61f1c875327971f43a62f`; source/link checks are recorded as 2026-10-01. The author reviewed each track's listening labels and recorded them as `verified`. That status means a single-author review, not independent multi-rater agreement or a guarantee that every label is correct. One later listening review disputes the high-arousal label on “Fly So High”; the catalog has not been silently relabeled after evaluation.

MTG-Jamendo mood/theme tags are source metadata, not the project's melody or arousal judgments. The catalog has no reliable per-track loudness, genre, tempo, vocal-presence, or lyric-language values for enforcing those constraints. The app therefore refuses to guarantee such requests. The repository stores links and metadata, not audio, lyrics, covers, or clips. Historical source license records are not proof of current audio permission; `current_audio_license_status=not_checked`. See [third-party notices](../data/THIRD_PARTY_NOTICES.md).

## Privacy and limits

No participant statements were collected for this evaluation. Full provider replies stay in Git-ignored local directories. A released `reports/formal_run_02/validated_cards_for_audit.jsonl` contains only case IDs, locally valid cards, and controlled error categories, allowing the recommendation audit to be reproduced without publishing raw replies. The local `.env` must never be committed. The catalog and intent set are small and purpose-selected; neither is a representative sample of listening behavior. See [the evaluation explainer](EVALUATION_EXPLAINER.md) for how each was used.
