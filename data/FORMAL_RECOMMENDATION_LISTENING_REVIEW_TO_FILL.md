# Official Run Playlist: Author Listening Review Table

This table is taken from the predictions saved in the second official run after freezing and the 35 official song libraries, **without re-calling the model**. Among the 21 cases that can provide three songs, take the 1st, 6th, 11th, 16th, and 21st in ascending order of `case_id`; among the 7 rejection cases, take the 2 with the smallest IDs. The selected cases are not random samples and cannot represent public satisfaction. Review tables for the original four fixed demo playlists remain independent.

Please fill in only judgments after actual listening or personal verification. Whether a song meets tag rules, whether you personally like it, and whether the AI correctly understood the original sentence are three different things; do not guess the listening experience when playback fails. If the same song appears repeatedly, you only need to listen to it once, but you should judge separately whether it is suitable in different requests. This table is not used to modify frozen intent ground truths or official scores. The "System Song Selection Understanding" below is only a brief summary of this saved output, **not the correct answer**.

## 1. Original Utterance and System Song Selection Understanding

| Case | User Original Utterance | System Understanding Actually Used for Song Selection |
| --- | --- | --- |
| `test_001` | Just finished arguing, my heart feels stuffed, want to listen to something that can slowly calm me down. | Wants to listen to songs leaning positive with low arousal |
| `test_010` | Just broke up, want to listen to something sad first, have a cry, and then slowly get better. | Arranges three songs in order of emotion from negative to positive |
| `test_017` | So annoying, so annoying, want to listen to something noisy to vent. | Wants to listen to high-arousal songs |
| `test_023` | Want to listen to something that makes people feel dawn has broken and there is hope. | Wants to listen to songs leaning positive |
| `test_030` | Play anything. | No clear goal, adopts exploratory recommendation |

| `test_2. Per-Song Listening` |

"Meets original utterance" can be filled with "Yes/Partially/No", and "Personally like" can be filled with "Like/Neutral/Dislike". Please fill in the actual listening date; if unable to play, record "No" and leave the listening experience judgment blank. Remarks can record specific discrepancies or timestamps when melody changes are heard; there is no need to write long reviews for every song.

| Case | Sequence | Actual Recommended Song | Listening Date | Playback Successful? | Meets Original Utterance? | Personally Like? | Remarks / Specific Changes Heard |
| --- | ---: | --- | --- | --- | --- | --- | --- |
| `test_001` | 1 | [Binz Flow](https://www.jamendo.com/track/114199) · `track_0114199` |  |  |  |  |  |
| `test_001` | 2 | [Simplicity](https://www.jamendo.com/track/579315) · `track_0579315` |  |  |  |  |  |
| `test_001` | 3 | [How Things Change](https://www.jamendo.com/track/938333) · `track_0938333` |  |  |  |  |  |
| `test_010` | 1 | [Give Me A Hand](https://www.jamendo.com/track/111374) · `track_0111374` |  |  |  |  |  |
| `test_010` | 2 | [Binz Flow](https://www.jamendo.com/track/114199) · `track_0114199` |  |  |  |  |  |
| `test_010` | 3 | [Fly So High](https://www.jamendo.com/track/824134) · `track_0824134` |  |  |  |  |  |
| `test_017` | 1 | [Robot_Star](https://www.jamendo.com/track/287980) · `track_0287980` |  |  |  |  |  |
| `test_017` | 2 | [Fly So High](https://www.jamendo.com/track/824134) · `track_0824134` |  |  |  |  |  |
| `test_017` | 3 | [Res Publica](https://www.jamendo.com/track/844698) · `track_0844698` |  |  |  |  |  |
| `test_023` | 1 | [Fly So High](https://www.jamendo.com/track/824134) · `track_0824134` |  |  |  |  |  |
| `test_023` | 2 | [How Things Change](https://www.jamendo.com/track/938333) · `track_0938333` |  |  |  |  |  |
| `test_023` | 3 | [Crash Of Night](https://www.jamendo.com/track/978031) · `track_0978031` |  |  |  |  |  |
| `test_030` | 1 | [Give Me A Hand](https://www.jamendo.com/track/111374) · `track_0111374` |  |  |  |  |  |
| `test_030` | 2 | [Binz Flow](https://www.jamendo.com/track/114199) · `track_0114199` |  |  |  |  |  |
| `test_030` | 3 | [Robot_Star](https://www.jamendo.com/track/287980) · `track_0287980` |  |  |  |  |  |

## 3. Evaluation of the Entire Playlist

Please evaluate whether the AI's understanding of the original prompt, the transitions among the three consecutive tracks, and the overall playlist meet the request, respectively; write at least one specific reason for each case. Even if the songs sound good, the AI may still misunderstand the original prompt.

| Case | Is the AI's understanding of the original prompt reasonable? | Are the three consecutive tracks natural? | Does the overall playlist meet the original prompt? | One specific reason |
| --- | --- | --- | --- | --- |
| `test_001` |  |  |  |  |
| `test_010` |  |  |  |  |
| `test_017` |  |  |  |  |
| `test_023` |  |  |  |  |
| `test_030` |  |  |  |  |

## 4. Review of Rejected Recommendations: No Listening Required

What is reviewed here is whether "the refusal is reasonable" and "the reason provided by the system is complete", rather than the song experience. The refusal criteria currently identified by the system are listed in the table; please check against the original prompt yourself for any omissions or misjudgments.

| Case | User's Original Prompt | System-Provided Refusal Basis | Is the Refusal Reasonable? | Is the Reason Complete? | Notes |
| --- | --- | --- | --- | --- | --- |
| `test_003` | Not too noisy electronic music, and don't play cheesy club tracks for me. | The music library cannot guarantee "electronic music" or "cheesy club tracks", so no songs are selected |  |  |  |
| `test_007` | I am so sleepy I can barely keep my eyes open, give me something invigorating, don't play slow songs. | The music library cannot guarantee "do not play slow songs", so no songs are selected |  |  |  |
