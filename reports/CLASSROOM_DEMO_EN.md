# Classroom recommendation demonstration

Run the fixed examples with `python3 scripts/demo_recommendations.py --sample NAME`, where `NAME` is one of the entries below. They use prewritten intent cards and the reviewed 35-track catalog. They demonstrate deterministic selection, not whether the model understood the displayed Chinese sentence. The terminal output is in Chinese; this page provides the English explanation. Only external Jamendo track-page links are displayed, not audio hosted by the project.

| Sample | Request meaning | Outcome and selected tracks | What it demonstrates |
| --- | --- | --- | --- |
| `explore` | “Play me some music.” | `ready`: [Give Me A Hand](https://www.jamendo.com/track/111374) → [Binz Flow](https://www.jamendo.com/track/114199) → [Robot_Star](https://www.jamendo.com/track/287980) | No stated target: a varied exploration rather than invented mind-reading. |
| `calm` | “I want quiet, soothing songs.” | `ready`: [Give Me A Hand](https://www.jamendo.com/track/111374) → [Binz Flow](https://www.jamendo.com/track/114199) → [Simplicity](https://www.jamendo.com/track/579315) | Targeting low arousal in each position. |
| `path` | “Start energetic, then gradually settle down.” | `ready`: [Robot_Star](https://www.jamendo.com/track/287980) → [How Things Change](https://www.jamendo.com/track/938333) → [Give Me A Hand](https://www.jamendo.com/track/111374) | Explicit song-order arousal targets 3 → 2 → 1. |
| `melody` | “Clear melodies with an unexpected turn.” | `ready`: [Itiro (Road and Rain)](https://www.jamendo.com/track/654634) → [Res Publica](https://www.jamendo.com/track/844698) → [Crash Of Night](https://www.jamendo.com/track/978031) | `melody_present=yes` plus high melodic-surprise tags. |
| `unsupported` | “No English-language songs.” | `cannot_guarantee_constraint`: no tracks selected. | The catalog lacks verified lyric-language labels; the system does not claim to enforce the condition. |

The catalog labels and rules make these results reproducible, but they do not prove that listeners will like the selections. The author listened to the four fixed three-song playlists (12 linked positions, all played and personally liked) in the original review table. A separate five-playlist review from the completed formal run found much more mixed request fit; see [the English listening review](AUTHOR_LISTENING_REVIEW_EN.md). Current audio rights have not been separately verified for reuse, so the demo remains link-only.
