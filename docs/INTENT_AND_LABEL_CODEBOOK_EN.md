# English codebook for intents and song labels

The recorded experiment used Chinese operational inputs and approved evidence. Their exact bytes remain in commit `a39e3fc`; the current files explain their meanings in English without changing the recorded score.

| Request field | Values and meaning | Song-side relation |
| --- | --- | --- |
| `current_valence` | `-1` negative, `0` neutral, `1` positive, or `null` when the speaker's present emotional tone is not stated. | Context only; never automatically treated as the desired song valence. |
| `current_arousal` | `1` low, `2` medium, `3` high, or `null` when the speaker's present activation is not stated. | Context only; not automatically the song's target energy. |
| `target_valence` | An exact `-1/0/1`, a lower/upper-bound object such as `{relation: at_least, value: 0}`, or `null` when unstated. | Match/filter the song's reviewed `valence`. |
| `target_arousal` | An exact `1/2/3`, a lower/upper-bound object, or `null` when unstated. | Match/filter the song's reviewed `arousal`. Arousal does **not** guarantee loudness or tempo. |
| `target_melodic_surprise` | `1` predictable/limited melodic turning, `2` some noticeable change, `3` pronounced/unexpected melodic development, or `null`. | Match the song's reviewed `melodic_surprise`; this is not a general quality grade. |
| `trajectory` | `none` means no encodable music target or order; `single_target` means a music target without an explicit track-order path; `from_to` records an expressly requested starting and ending *song* valence/arousal. | For `from_to`, use the start, midpoint, and end over three positions. A person's hoped-for emotional recovery is not automatically a song path. |
| `requires_melody_present` | `true` only for an explicit request for an identifiable/hummable melody; otherwise `null`. | Hard-match `melody_present=yes`. This is separate from how surprising that melody is. |
| `constraints` | Exact phrases from the user's request that cannot be guaranteed by the verified catalog. `[]` means none. | A nonempty list routes to `cannot_guarantee_constraint`; never claim a proxy satisfies an unmeasured condition. |

Every nonempty interpreted value needs an exact source phrase in `evidence`; unsupported-condition phrases must also be traceable to the request. Local validation checks the structure, allowed values, trajectory consistency, and that evidence text appears in the original sentence. The catalog side has four reviewed listening fields: `valence` (-1/0/1), `arousal` (1/2/3), `melody_present` (yes/no), and `melodic_surprise` (1/2/3). The source dataset's mood/theme tags are kept separately and are not interchangeable with these fields. `verified` means author-reviewed, not objectively measured or independently annotated.

The scorer compares six core request fields exactly, with range objects compared as range objects. `requires_melody_present` and unsupported conditions receive separate metrics. See [the evaluation explainer](EVALUATION_EXPLAINER.md) for denominators and [the data explainer](DATA_EXPLAINER.md) for provenance.
