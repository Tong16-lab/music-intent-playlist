# Submission audit against the instructor's added constraints

| Requirement | Current evidence | Status before hand-in |
| --- | --- | --- |
| Well-structured report, 1,200 words ± approximately 10–15%, with reasoned outcome critique and optional future path | `docs/PROJECT_REPORT.md` (about 1,160 words by `wc -w`; includes trade-offs, per-field results, evaluation limits, debugging, and future work) | Draft ready; author should proofread the final text. |
| Face-and-screen video, about five minutes and no more than eight minutes of material expected to be viewed | [Recorded demonstration](../demo/demo.mp4), 6 min 48 sec; video and audio tracks are present. The [script](VIDEO_SPEECH_SCRIPT_EN.md) and [guide](VIDEO_DEMO_PLAN.md) remain available. | Video is tracked in the repository; the author should review complete playback, face/screen visibility, sound, legibility, and absence of secrets. Confirm access through the published GitHub link. |
| Transparent data and evaluation files, each with an explainer | `docs/ENGLISH_SUBMISSION_INDEX.md` links the 42 translated cases, 35 translated catalog entries, scoring/prompt copies, development comparisons, both formal-run accounts, evaluation explainers, translated V2 files, JSON, and validated cards | Prepared; the exact evaluated Chinese files and original freeze hashes are at commit `a39e3fc`, not in the current English tree. |
| Reproducible code instructions and legible file/module documentation | English root `README.md`, module-level docstrings, offline tests, fixed examples with `--lang en`, and public-card routing audit | Prepared; verify from a fresh clone on another machine. |
| Product persona, input, output, architecture, target/reached metrics | `docs/PRODUCT_DOCUMENTATION.md` | Prepared; no unregistered numerical superiority target has been invented. |
| Honest baseline, limitations, and end-to-end demonstration from the original watchouts | Report, English formal summary, classroom demo, and listening review | Prepared; author should rehearse a concise explanation. |
| Single assistance/provenance declaration | `docs/AI_ASSISTANCE_DISCLOSURE.md` | Prepared; author must confirm names, model versions, dates, prompts, and scope before submission. |
| Public repository and teacher access | Existing Git remote; local tests, data checks, and tracked-file secret scan completed | Confirm the published repository and video can be opened without owner access, then submit the exact links requested by the instructor. |

## Final author checks

1. Confirm the course's complete rubric, submission deadline, repository visibility, video hand-in location, and whether any separate upload is required; the added message and proposal watchouts do not specify every portal setting.
2. Proofread the English report against `reports/formal_run_02/evaluation.json` and your completed listening review. Verify the historical freeze against commit `a39e3fc`, not the current translated files; do not present the old score as an English-input result.
3. Run the offline commands in `README.md`. Keep `.env` and private predictions out of Git; inspect `git status --short` and the pending diff before committing.
4. Review the entire [recorded video](../demo/demo.mp4) for playback quality, face/screen visibility, readable text, audible speech, and accidental disclosure. Confirm that the course accepts a video checked into GitHub or upload it separately if required.
5. Open the published README and video links, and submit the precise repository/video locations requested by the instructor. Until the course portal receives those links, the package is **prepared but not submitted**.
