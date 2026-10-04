# PE6201 — Music Intent Playlist

An everyday Chinese request becomes either three ordered, linked songs with traceable selection reasons or an explicit explanation that a requested condition cannot be guaranteed. The prototype tests language understanding plus deterministic recommendation; it does not stream audio or claim to improve musical taste.

## Submission map

Start with the [submission index](docs/ENGLISH_SUBMISSION_INDEX.md). The current tree presents the project in English, including all 42 request cases and 35 catalog tracks.

| Deliverable | Where to read it |
| --- | --- |
| ~1,200-word report with critique and future path | [Project report](docs/PROJECT_REPORT.md) |
| Persona, input/output, architecture, target and achieved metrics | [Product documentation](docs/PRODUCT_DOCUMENTATION.md) |
| Data provenance, field meanings, rights, and limitations | [Data explainer](docs/DATA_EXPLAINER.md), [English codebook](docs/INTENT_AND_LABEL_CODEBOOK_EN.md), and [third-party notices](data/THIRD_PARTY_NOTICES.md) |
| Evaluation protocol, baseline, scoring, and limitations | [Evaluation explainer](docs/EVALUATION_EXPLAINER.md) and [English results summary](reports/FORMAL_RESULTS_SUMMARY_EN.md) |
| Recommendation demonstration and listening check | [Classroom demo](reports/CLASSROOM_DEMO_EN.md) and [author listening review](reports/AUTHOR_LISTENING_REVIEW_EN.md) |
| Assistance and provenance disclosure | [Declaration](docs/AI_ASSISTANCE_DISCLOSURE.md) |
| Recorded face-and-screen demonstration | [Watch the video](demo/demo.mp4) (6 min 48 sec); [speaking script](docs/VIDEO_SPEECH_SCRIPT_EN.md), [recording guide](docs/VIDEO_DEMO_PLAN.md), and [submission checklist](docs/SUBMISSION_CHECKLIST.md) |

The recorded video is at [`demo/demo.mp4`](demo/demo.mp4). At the author's request, the recording is unchanged; its meeting-app overlay contains some Chinese text. The measured 11/30 result belongs to a Chinese-input experiment. Its exact source files and frozen hashes are preserved in [commit `a39e3fc`](https://github.com/Tong16-lab/music-intent-playlist/tree/a39e3fc), not in the translated current tree. Current English tables, prompts, and reports are reading translations, **not an English-input evaluation**. Do not compare their hashes with the historical freeze record or present the historical score as an English-input result.

## Quick local demonstration

Requirements: Python 3.10 or newer, a terminal opened at the repository root, and internet access **only when clicking Jamendo links or choosing the optional live mode**. The fixed examples themselves make no model call and incur no API fee. Run one of:

```bash
python3 scripts/demo_recommendations.py --sample explore --lang en
python3 scripts/demo_recommendations.py --sample calm --lang en
python3 scripts/demo_recommendations.py --sample path --lang en
python3 scripts/demo_recommendations.py --sample melody --lang en
python3 scripts/demo_recommendations.py --sample unsupported --lang en
```

The first four use prewritten intent cards to demonstrate catalog selection and produce three linked tracks. `path` shows an arousal sequence of 3 → 2 → 1. `unsupported` refuses a lyric-language condition absent from the verified catalog. These examples **do not test request interpretation**. `--lang en` selects the English display; the underlying cards and selections are unchanged. [The demo page](reports/CLASSROOM_DEMO_EN.md) also explains the output.

The current branch intentionally runs the fixed offline demonstration only. Its translated prompt and request examples have not been evaluated as an English-language model pipeline. To inspect or reproduce the scored live parser, check out commit `a39e3fc` and follow that commit's README with the original Chinese inputs. Never commit or display an API key.

Local validation must pass before track selection. The output provides Jamendo page links, not embedded audio. Invalid cards, unguaranteed conditions, or fewer than three suitable songs are reported rather than silently filled.

## Reproduce checks without paid calls

Run from the repository root:

```bash
python3 scripts/sync_v2_answers.py check
python3 scripts/verify_historical_freeze.py
python3 scripts/export_catalog.py check
python3 scripts/demo_recommendations.py --sample path --lang en
python3 scripts/demo_recommendations.py --sample unsupported --lang en
PYTHONPYCACHEPREFIX=/tmp/pe6201-pycache python3 -m unittest discover -s tests -p test_english_submission.py -v
```

The historical-freeze verifier reads the exact original bytes at commit `a39e3fc` without changing this checkout. The routing audit is likewise bound to those original inputs and should be run from that commit, not against translated files. The catalog check reads the checked-in `data/catalog_source_snapshot.md`. The second formal run's recorded numbers are in `reports/formal_run_02/evaluation.json` and `.md`; the first, connection-failed run is retained separately in `reports/evaluation.*`. No paid rerun is needed to inspect the recorded score. The original regression suite remains runnable at commit `a39e3fc`. English translations of those test files are retained under `tests/historical_reading_copies/` for inspection but are not run in this branch because exact Chinese source spans and prompt hashes cannot be preserved by translation. The active five-test suite checks this branch's English text, synchronized tables and display wording, catalog demonstration, and original freeze.

## Code map

| Path | Responsibility |
| --- | --- |
| `src/music_intent/config.py`, `openrouter_client.py` | Local configuration and one-call model transport; avoid logging secrets or raw replies. |
| `src/music_intent/intent.py`, `prototypes/compact_intent_format.py` | V2 schema, compact-to-V2 conversion, field and exact-source-evidence validation. |
| `src/music_intent/catalog.py`, `recommender.py`, `display.py` | Load 35 reviewed tracks, route constraints, select and explain linked results. |
| `src/music_intent/evaluation.py`, `scoring_v3.py` | Keyword baseline and predeclared field-by-field formal scoring. |
| `scripts/demo_recommendations.py`, `evaluate.py` | Offline/live demo and guarded formal evaluation entry points. |
| `scripts/export_catalog.py`, `sync_v2_answers.py`, `freeze_test_set.py`, `export_public_predictions.py` | Catalog reproducibility, answer consistency, frozen-test integrity, and redacted card release. `build_catalog_source_snapshot.py` records the one-time extraction from the original project document. |
| `tests/` | Offline behavior, format, evaluation, safety, and regression tests. |

The formal scoring specification was fixed in `data/FORMAL_SCORING_V3.md` before the completed run. The selected prompt and schema are `data/COMPACT_DEV_PROMPT_v2.txt` and `data/COMPACT_DEV_SCHEMA_v1.json`; changing them would define a different system. The 42 reviewed requests are examples, not participant data. The 35-track catalog has author-reviewed listening labels but no currently verified audio-reuse permission; this repository displays links only. Full validity limits are in the report and explainers.
