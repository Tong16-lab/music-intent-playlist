# Product documentation — music-intent playlist

## Problem, user, and scope

The primary persona is a listener looking for new music during a commute or another everyday moment. They can describe a feeling in ordinary Chinese but may not know terms such as *valence* or *melodic surprise*. The prototype turns one such request into three ordered track links with a short, traceable reason for each choice. It explores musical variety without presenting itself as a teacher. It does not claim to improve anyone's taste or mood.

The input is one Chinese text request. The output is either three distinct Jamendo track-page links in order, with the labels used for selection, or an explicit status explaining why a safe match cannot be guaranteed. It does not play, download, or redistribute audio. Fixed offline examples use prewritten intent cards and therefore demonstrate the selection layer only; live text calls the configured language model once and passes its card through local validation.

## High-level architecture

```text
Chinese request
      |
      v
OpenRouter / Gemini language model
(intent fields + exact source phrases)
      |
      v
Compact-format converter -> V2 value and evidence validator
      |                         |
      | valid                   +-- invalid -> no recommendation
      v
Constraint router -------- unsupported -> explain refusal
      |
      v
Verified 35-track catalog -> hard filters -> weighted match / path order
      |
      v
Three linked tracks + selection reasons, or honest shortage status

Parallel evaluation: same 30 frozen requests -> model and keyword baseline
                     -> same approved answers -> field-level comparison
```

The model interprets the request; it does not invent track labels or rank songs. The catalog stores author-reviewed `valence` (-1 to 1), `arousal` (1 to 3), `melody_present` (yes/no), and `melodic_surprise` (1 to 3). For a request that specifies a three-step path, the selector targets its start, midpoint, and end. It enforces stated ranges and a request for a discernible melody, then scores relevant dimensions with weights 0.35/0.35/0.30 for valence/arousal/melodic surprise, renormalized to the dimensions actually requested. Ties favor artist and label diversity, then track ID. A hard condition that the catalog cannot verify produces `cannot_guarantee_constraint`; the system does not silently substitute an unrelated label. These weights are design choices, not learned or user-validated optimums.

## Targeted versus reached metrics

| Measure | Target defined before this report | Reached or observed |
| --- | --- | --- |
| Recommendation routing | For each valid card, give three distinct tracks or explicitly refuse/flag a shortage rather than claim to satisfy unmeasured conditions. | 21/30 three-track outcomes, 7/30 explicit refusals, 2/30 invalid cards, 0 catalog shortages in the completed-run routing audit. |
| Intent comparison | Use the same frozen 30 answers for the model and keyword baseline; report each field, invalid responses, and the exact six-field card. **No numerical superiority threshold was registered.** | 28/30 valid cards; exact six-field card 11/30 for the model, 12/30 for the baseline; trajectory 23/30 versus 18/30; target arousal 16/30 versus 23/30. |
| Listening check | Review fixed demonstrations and a small predetermined set of completed-run playlists, keeping personal liking separate from request fit. No population-satisfaction target was defined. | In five selected completed-run playlists, 10/15 track positions fully fit, 4/15 partly fit, 1/15 did not; 1/5 whole playlists fully fit. |

Routing counts are not recommendation-quality scores. The single-author listening results are not representative of listener satisfaction.

See [the evaluation explainer](EVALUATION_EXPLAINER.md), [the English results summary](../reports/FORMAL_RESULTS_SUMMARY_EN.md), and [the listening review](../reports/AUTHOR_LISTENING_REVIEW_EN.md) for denominators and limitations.
