# PE6201 — Music Intent Playlist

An everyday Chinese request becomes either three ordered, linked songs with traceable selection reasons or an explicit explanation that a requested condition cannot be guaranteed. The prototype tests language understanding plus deterministic recommendation; it does not stream audio or claim to improve musical taste.

## Submission map

Start with the [English submission index](docs/ENGLISH_SUBMISSION_INDEX.md): it maps each preserved Chinese or machine-readable source to an English reading copy, including all 42 request cases and 35 catalog tracks.

| Deliverable | Where to read it |
| --- | --- |
| ~1,200-word report with critique and future path | [Project report](docs/PROJECT_REPORT.md) |
| Persona, input/output, architecture, target and achieved metrics | [Product documentation](docs/PRODUCT_DOCUMENTATION.md) |
| Data provenance, field meanings, rights, and limitations | [Data explainer](docs/DATA_EXPLAINER.md), [English codebook](docs/INTENT_AND_LABEL_CODEBOOK_EN.md), and [third-party notices](data/THIRD_PARTY_NOTICES.md) |
| Evaluation protocol, baseline, scoring, and limitations | [Evaluation explainer](docs/EVALUATION_EXPLAINER.md) and [English results summary](reports/FORMAL_RESULTS_SUMMARY_EN.md) |
| Recommendation demonstration and listening check | [Classroom demo](reports/CLASSROOM_DEMO_EN.md) and [author listening review](reports/AUTHOR_LISTENING_REVIEW_EN.md) |
| Assistance and provenance disclosure | [Declaration](docs/AI_ASSISTANCE_DISCLOSURE.md) |
| Recorded face-and-screen demonstration | [Watch the video](demo/demo.mp4) (6 min 48 sec); [speaking script](docs/VIDEO_SPEECH_SCRIPT_EN.md), [recording guide](docs/VIDEO_DEMO_PLAN.md), and [submission checklist](docs/SUBMISSION_CHECKLIST.md) |

The recorded video is at [`demo/demo.mp4`](demo/demo.mp4). Historical run reports and the Chinese input/answer files remain in their evaluated form, with line- or case-linked English reading companions in the index. Do not replace the frozen Chinese inputs with English: that would change the evaluated task and invalidate the recorded hashes.

## Quick local demonstration

Requirements: Python 3.10 or newer, a terminal opened at the repository root, and internet access **only when clicking Jamendo links or choosing the optional live mode**. The fixed examples themselves make no model call and incur no API fee. Run one of:

```bash
python3 scripts/demo_recommendations.py --sample explore --lang en
python3 scripts/demo_recommendations.py --sample calm --lang en
python3 scripts/demo_recommendations.py --sample path --lang en
python3 scripts/demo_recommendations.py --sample melody --lang en
python3 scripts/demo_recommendations.py --sample unsupported --lang en
```

The first four use prewritten intent cards to demonstrate catalog selection and produce three linked tracks. `path` shows an arousal sequence of 3 → 2 → 1. `unsupported` refuses a lyric-language condition absent from the verified catalog. These examples **do not test request interpretation**. `--lang en` changes the visible labels and sample-sentence display only; the underlying cards and selections are unchanged. Without that flag the historical Chinese display remains available. [The English demo page](reports/CLASSROOM_DEMO_EN.md) also explains the output.

For an optional live text request, create a local `.env` from the blank `.env.example` and fill in your own `OPENROUTER_API_KEY` and `OPENROUTER_MODEL=google/gemini-3.5-flash-lite`. Never commit or display the key. Check local configuration without showing it:

```bash
python3 scripts/check_config.py
git check-ignore -v .env
git ls-files .env
```

The last command should print nothing. A live run requires explicit paid-call permission and makes one OpenRouter request; it may fail if credentials or network access are unavailable:

```bash
python3 scripts/demo_recommendations.py --text "想听安静的歌" --allow-paid
```

The example Chinese request means “I want quiet music.” It is included only to illustrate the optional paid live mode; the recorded formal evaluation is already complete and should not be rerun for the demonstration.

Local validation must pass before track selection. The output provides Jamendo page links, not embedded audio. Invalid cards, unguaranteed conditions, or fewer than three suitable songs are reported rather than silently filled.

## Reproduce checks without paid calls

Run from the repository root:

```bash
python3 scripts/sync_v2_answers.py check
python3 scripts/freeze_test_set.py verify
python3 scripts/export_catalog.py check
python3 scripts/audit_formal_recommendations.py --check
PYTHONPYCACHEPREFIX=/tmp/pe6201-pycache python3 -m unittest discover -s tests -v
```

The routing audit reads the released, validated cards in `reports/formal_run_02/validated_cards_for_audit.jsonl`; it works on a fresh clone without private raw replies. This release contains case IDs, valid V2 cards, and fixed error codes only, not full provider responses or secrets. The catalog check reads the checked-in `data/catalog_source_snapshot.md`, not a document outside the repository. The second formal run's recorded results are in `reports/formal_run_02/evaluation.json` and `.md`; the first, connection-failed run is retained separately in `reports/evaluation.*`. Do not rerun the 30 paid cases to inspect their already recorded score.

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
