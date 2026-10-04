# Face-and-screen demo plan and recording guide

The [recorded demonstration](../demo/demo.mp4) is **6 min 48 sec**, below the instructor's eight-minute viewing cap. The file is present locally and has video and audio tracks; the author still needs to watch the complete file to confirm visible face and screen, clear speech and text, and no accidental disclosure before hand-in.

Use the [complete English speaking script](VIDEO_SPEECH_SCRIPT_EN.md) while rehearsing. Show English-facing pages and English terminal output so the instructor can follow each claim. The visible English request in each fixed demo is a display translation; the underlying prewritten Chinese intent card and selector are unchanged.

| Time | What to show | What to say, briefly |
| --- | --- | --- |
| 0:00–0:40 | Face plus project title/README | “This prototype translates a casual Chinese music request into three explained track links, or a transparent refusal.” State the everyday-listener persona and the problem. |
| 0:40–1:25 | Product architecture diagram | Point to request → model intent card → local validation → catalog filtering/ranking → three links. Explain that the model interprets words and the local selector chooses songs. |
| 1:25–2:35 | Terminal: run `python3 scripts/demo_recommendations.py --sample path --lang en`; optionally open one displayed Jamendo page | Show the 3 → 2 → 1 arousal ordering and the labels used. Say this fixed sample starts from a prepared intent card and demonstrates recommendation logic only. |
| 2:35–3:10 | Terminal: run `python3 scripts/demo_recommendations.py --sample unsupported --lang en` | Show the refusal and why no lyric-language guarantee can be made. |
| 3:10–4:20 | English formal results summary | Explain the completed 30-case run: 28 valid cards, full-card 11/30 versus keyword 12/30; stronger trajectory, weaker target arousal. State clearly that the first run failed due to connection errors and was kept separate. |
| 4:20–5:15 | Listening review plus one concrete failure | Discuss `test_010` (person feeling better versus song sequence) or `test_017` (disputed arousal label). Distinguish personal liking from actual request fit. |
| 5:15–5:50 | Face plus report conclusion | Say what the prototype establishes, what it does not establish, and one realistic next step. |

The recorded file is at [`demo/demo.mp4`](../demo/demo.mp4). Before submission, verify playback and instructor access to the repository or upload the file separately if the course requires it. During review, check that the recording does not show `.env`, API keys, private predictions, or unrelated personal windows; the fixed offline samples should not be presented as live model calls.

## Practical macOS setup with OBS Studio

OBS's [official quick-start guide](https://obsproject.com/kb/quick-start-guide) documents adding capture sources, checking audio, and recording. Its [macOS permissions guide](https://obsproject.com/kb/macos-permissions-guide) covers screen, camera, and microphone access.

1. Open the English README, product documentation, results summary, and listening review before recording. Increase text zoom so the numbers are legible. Close notifications and unrelated windows; keep `.env` and private directories closed.
2. In OBS, create one scene. Add **macOS Screen Capture** for the display, then **Video Capture Device** for your webcam. Resize the camera into a corner where it does not obscure text. Select your microphone and confirm the audio meter moves when you speak. Grant Screen Recording, Camera, and Microphone permissions if requested.
3. Set the recording destination. Make a 20–30-second trial: say one sentence, switch from a document to the terminal, then replay the saved file. Verify that face and screen remain visible, the voice is audible, no secret appears, and displayed text is readable.
4. Record the full sequence. Keep the key table visible long enough for `11/30` versus `12/30` and `16/30` versus `23/30` to be seen. Do not describe the fixed offline examples as model-interpreted live inputs. Show track links rather than recording third-party audio, whose current reuse permission has not been verified.
5. Replay the entire 6-minute-48-second file. If you edit or replace it, recheck the duration; the instructor said only the first eight minutes of a longer video would be viewed. Confirm that the final file and repository/video link are accessible to the instructor.
