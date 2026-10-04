# PE6201: Local recommendation demonstration for 35 official tracks

The following are all **fixed examples and preset intent cards**, without calling models, and they are not the 30 frozen official test sentences. Songs and their order are calculated by the current deterministic song selector on the 35 official tracks; title links point only to the original Jamendo pages.

Rules use the author-verified `valence`, `arousal`, `melody_present`, and `melodic_surprise`; original MTG mood/theme are used only for candidate sources and not as listening review evidence.

## Example `explore`

example input: Play some random music

### Actual recommendations

Status: `ready`.
No executable song target specified; exploring according to verified tag combinations.

| Order | Song (Jamendo Original Page) | Artist | Verified Tags | Basis |
| ---: | --- | --- | --- | --- |
| 1 | [Give Me A Hand](https://www.jamendo.com/track/111374) | Traffic In My Head | valence=-1; arousal=1; melody_present=yes; melodic_surprise=1 | Verified tags; Exploration choice |
| 2 | [Binz Flow](https://www.jamendo.com/track/114199) | Pedro Collares | valence=0; arousal=1; melody_present=yes; melodic_surprise=2 | Verified tags; Exploration choice |
| 3 | [Robot_Star](https://www.jamendo.com/track/287980) | Nationale2 | valence=0; arousal=3; melody_present=yes; melodic_surprise=2 | Verified tags; Exploration choice |

Tag matching and rule passing do not mean human users like these songs; audio licensing has not been verified, and this page only provides external links.


## Sample `calm`

example input: I want to listen to quiet and soothing songs

### Actual recommendations

Status: `ready`.
The following is based on verified song tags matched with clear musical goals.

| Order | Song (Jamendo Original Page) | Artist | Verified Tags | Basis |
| ---: | --- | --- | --- | --- |
| 1 | [Give Me A Hand](https://www.jamendo.com/track/111374) | Traffic In My Head | valence=-1;arousal=1;melody_present=yes;melodic_surprise=1 | arousal=1 |
| 2 | [Binz Flow](https://www.jamendo.com/track/114199) | Pedro Collares | valence=0;arousal=1;melody_present=yes;melodic_surprise=2 | arousal=1 |
| 3 | [Simplicity](https://www.jamendo.com/track/579315) | Macroform | valence=0;arousal=1;melody_present=yes;melodic_surprise=1 | arousal=1 |

Tag matching and rule passing do not mean human users like these songs; audio licensing has not been verified, and this page only provides external links.


## Sample `path`

example input: Start with energetic songs, then gradually quiet down

### Actual recommendations

Status: `ready`.
The following is based on verified song tags matched with clear musical goals.

| Order | Song (Jamendo Original Page) | Artist | Verified Tags | Basis |
| ---: | --- | --- | --- | --- |
| 1 | [Robot_Star](https://www.jamendo.com/track/287980) | Nationale2 | valence=0;arousal=3;melody_present=yes;melodic_surprise=2 | arousal=3;track sequence path 1st track |
| 2 | [How Things Change](https://www.jamendo.com/track/938333) | Jonathan Dimmel | valence=1;arousal=2;melody_present=yes;melodic_surprise=2 | arousal=2;track sequence path 2nd track |
| 3 | [Give Me A Hand](https://www.jamendo.com/track/111374) | Traffic In My Head | valence=-1;arousal=1;melody_present=yes;melodic_surprise=1 | arousal=1;track sequence path 3rd track |

Tag matching and rule passing do not mean human users like these songs; audio licensing has not been verified, and this page only provides external links.


## Example `melody`

Synthesis input: I want to hear songs with clear melodies and surprising progressions

### Actual recommendations

Status: `ready`.
The following is based on verified song tags matched with clear musical goals.

| Order | Song (Jamendo Original Page) | Artist | Verified Tags | Basis |
| ---: | --- | --- | --- | --- |
| 1 | [Itiro (Road and Rain)](https://www.jamendo.com/track/654634) | Alexandr Ossipov production music | valence=-1;arousal=1;melody_present=yes;melodic_surprise=3 | melodic_surprise=3;recognizable_melody=yes |
| 2 | [Res Publica](https://www.jamendo.com/track/844698) | Sevenless | valence=0;arousal=3;melody_present=yes;melodic_surprise=3 | melodic_surprise=3;recognizable_melody=yes |
| 3 | [Crash Of Night](https://www.jamendo.com/track/978031) | StatueOfDiveo | valence=1;arousal=3;melody_present=yes;melodic_surprise=3 | melodic_surprise=3;recognizable_melody=yes |

Listening tip (author's original notes):

- Track 1 (track_0654634): Around 1:36 and 2:16, both the melodic register and phrasal rhythm undergo noticeable changes, making the later section less predictable than the earlier part.
- Track 2 (track_0844698): Around 3:12 and 3:56, the thematic pitch center and harmonic progression undergo two distinct transitions, making the later section difficult to predict directly from the preceding part.
- Track 3 (track_0978031): Around 1:50 and 3:56, the dominant pitch center and rhythmic patterns shift multiple times with a relatively large magnitude of change.

Tag matching and rule passing do not mean human users like these songs; audio licensing has not been verified, and this page only provides external links.


## Example `unsupported`

example input: No English songs

### Actual recommendations

Status: `cannot_guarantee_constraint`.
The current music library tags cannot reliably guarantee hard conditions in the original sentence; no song selected.

Tag matching and rule passing do not mean human users like these songs; audio licensing has not been verified, and this page only provides external links.


## Evaluation Boundary

These results only prove that the current rules and verified labels can produce reproducible matches, but do not prove higher song quality, nor do they prove that real listeners like them. Please fill in subsequent author audition feedback in [`data/RECOMMENDATION_LISTENING_REVIEW_TO_FILL.md`](../data/RECOMMENDATION_LISTENING_REVIEW_TO_FILL.md). The current audio license is `not_checked`, and the demo only opens external pages.

Post-freezing, the official intent evaluation is based on [`formal_run_02/evaluation.md`](formal_run_02/evaluation.md); this report did not rerun the intent model.
