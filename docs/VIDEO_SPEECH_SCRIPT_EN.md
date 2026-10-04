# Five-to-six-minute face-and-screen presentation script

The bracketed cues are for the presenter, not spoken. Keep your face visible in a small corner throughout. The offline examples use prewritten intent cards; the measured request-understanding results come from the separately recorded formal run.

## 0:00–0:40 — Problem and product

[Show `README.md` and the product title.]

Hello, I am presenting Music Intent Playlist. Imagine getting home after a difficult day and saying, “I want music that understands how I feel, but I do not know what to play next.” Ordinary recommendation feeds often use listening history. My project examines a different starting point: can an everyday Chinese sentence be interpreted as a music request, and can that interpretation drive an explainable, three-song recommendation? The intended user is an everyday listener who does not know specialist music vocabulary. This is a course prototype, not a streaming service or a claim that musical taste has improved.

## 0:40–1:25 — Architecture and roles

[Open `docs/PRODUCT_DOCUMENTATION.md`; point to the architecture diagram.]

The user provides one free-text sentence. A language model converts it into a structured intent card: the speaker's current mood and energy, the music they want, any melodic preference, an explicitly requested song sequence, and conditions the catalog cannot guarantee. Local code checks both allowed values and whether quoted evidence actually occurs in the user's sentence. A separate, deterministic selector then matches the card to thirty-five author-reviewed tracks. The output is three ordered Jamendo links, or a clear refusal if a hard condition cannot be checked. This separation lets me evaluate language understanding and music selection independently.

## 1:25–2:35 — Demonstrate selection

[Run `python3 scripts/demo_recommendations.py --sample path --lang en` in the repository terminal. Enlarge the text.]

Here the display translates a fixed example: “Start with energetic songs, then gradually calm down.” The selector uses an arousal path from level three to level one. Notice the three positions: three, two, one. Each recommendation shows its reviewed labels and the selection reason, and the title links to the original track page. This is deliberately an offline example with a prewritten intent card. It demonstrates the selection logic; it is not evidence that the model correctly interpreted this particular sentence. The system does not upload or play the audio inside the repository.

[Run `python3 scripts/demo_recommendations.py --sample unsupported --lang en`.]

This second example requests no English-language songs. Our catalog has no verified lyric-language field, so the system refuses instead of pretending it can guarantee the condition. That is a product limitation, but a transparent one.

## 2:35–4:05 — Evaluation

[Open `reports/FORMAL_RESULTS_SUMMARY_EN.md`; zoom to the results table.]

For request interpretation, I compared the selected model pipeline with a keyword-rule baseline on the same thirty frozen, author-reviewed requests. All thirty model calls completed; twenty-eight produced cards that passed local checks. The exact six-field card was correct in eleven of thirty cases, compared with twelve of thirty for the baseline. That one-case difference is not evidence of a general winner. Per-field results are more informative: the model did better on requested song trajectory, twenty-three versus eighteen, and target emotional tone, twenty-two versus twenty. It was weaker on desired energy, sixteen versus twenty-three. Two invalid cards remain in the end-to-end denominator. The first attempted run stopped because of connection failures; it is preserved separately and not mixed into these scores. These requests are examples of plausible listening situations, not statements collected from participants; this is a controlled course evaluation, not a measurement of live users.

## 4:05–5:10 — Recommendation audit and critique

[Open `reports/AUTHOR_LISTENING_REVIEW_EN.md`; show the five-playlist summary and one specific mismatch.]

I also checked what happened after interpretation. Of the thirty recorded cases, twenty-one yielded three links, seven were refused because a requested condition could not be guaranteed, and two had invalid intent cards. That proves the pipeline can route cases; it does not prove the songs feel right. In my listening review of five complete playlists, ten of fifteen individual track positions fully fit, but only one of five full three-song sequences fully fit. This gap matters: a plausible single track does not automatically make a satisfying journey. One recurring weakness is that a phrase about a person gradually feeling better can be mistaken for an instruction to change the music across three songs. Another is the project's coarse, subjective song labels. I kept such mismatches visible instead of relabeling the frozen answers after seeing the scores.

## 5:10–5:45 — Conclusion

[Return to your face and the report conclusion.]

This project shows a working, inspectable path from informal language to linked recommendations, with explicit refusals and separate checks for interpretation and listening fit. It does not show superiority over the keyword baseline, a change in users' musical appreciation, or reliable performance beyond these thirty examples. A sensible next step would be a small, consent-based listener study and more independent song labeling. For this course, the most important outcome is understanding where the model helps, where simple rules remain stronger, and where recommendation quality still needs evidence. Thank you.
