# English reading translation of approved evidence phrases

This table follows the `evidence_json` and `unsupported_condition_phrases` cells in [`user_intents_v2_review.tsv`](user_intents_v2_review.tsv), one row per case. It complements the [42 full request translations](USER_INTENTS_EN.md). The phrases below convey the meaning of the approved Chinese evidence; English translation does **not** preserve Chinese character boundaries and must not be used for the program's exact-substring validation. `CV` = current valence, `CA` = current arousal, `TV` = target song valence, `TA` = target song arousal, `MS` = target melodic surprise, `MP` = explicit melody presence, and `Tr` = trajectory classification. A blank source evidence object is shown as “None.”

| Case | Approved evidence phrases, translated by field | Unsupported-condition phrases, translated |
| --- | --- | --- |
| `dev_001` | CV: “my head is buzzing”; TA: “quiet”; MS: “nothing too flashy or elaborate”; Tr: “I want something quiet to help me recover a little” | None |
| `dev_002` | CV: “irritating enough”; TV: “brighter in mood”; TA: “more energizing”; Tr: “give me something more energizing and brighter in mood” | “not too loud”; “do not play formulaic pop” |
| `dev_003` | None | “I don't want anyone singing” |
| `dev_004` | CV: “my heart feels heavy”; TV: “down for a while”; Tr: “I want something to stay with me in that down mood for a while” | None |
| `dev_005` | TV: “not too melodramatically sad”; TA: “a bit of drive”; Tr: “want something with a bit of drive” | None |
| `dev_006` | MS: “something I won't see coming” | None |
| `dev_007` | CV and CA: “feel really panicky”; TA: “feel steadier”; Tr: “I want to gradually feel steadier” | None |
| `dev_008` | CV: “in a really good mood”; TV: “cheerful”; Tr: “I want something cheerful” | “don't play tacky party-style music” |
| `dev_009` | None | “don't play rock”; “don't play rap” |
| `dev_010` | TA: “really energetic”; MS: “unexpected moments”; Tr: “I want something really energetic” | “not formulaic pop” |
| `dev_011` | CV: “a bit annoyed”; TA: “gradually soften”; Tr: “start with something intense to let it out, then gradually soften” | None |
| `dev_012` | TV: “neither sad nor happy”; Tr: “some background music that's neither sad nor happy” | None |
| `test_001` | CV: “feel blocked up inside”; TA: “gradually settle down”; Tr: “I want music that can help me gradually settle down” | None |
| `test_002` | TV: “warm”; Tr: “I'd like something warm and easygoing” | None |
| `test_003` | None | “electronic music”; “not too loud”; “don't give me tacky party-style tracks” |
| `test_004` | CV: “under a lot of pressure”; MS: “not too complicated” | None |
| `test_005` | MS: “not something whose next bit I can guess immediately” | None |
| `test_006` | TV: “sad”; Tr: “I'd like something sad” | None |
| `test_007` | CA: “so sleepy I can barely keep my eyes open”; TA: “wake me up”; Tr: “give me something to wake me up” | “no slow songs” |
| `test_008` | TV and TA: “light and upbeat”; Tr: “I'd like something light and upbeat” | None |
| `test_009` | None | “don't play songs with sung words” |
| `test_010` | TV: “sad”; Tr: “for now I want something sad” | None |
| `test_011` | TA: “powerful”; MS: “not too convoluted”; Tr: “I want something powerful” | None |
| `test_012` | None | “don't play those slow sentimental songs”; “don't play formulaic pop” |
| `test_013` | CV: “so happy”; TV and TA: “even more exhilarating”; Tr: “I want something even more exhilarating” | None |
| `test_014` | CV: “anxious”; MS: “don't suddenly spring a big change on me” | None |
| `test_015` | MS: “freshness” | “not that tacky party-style stuff” |
| `test_016` | TV: “gentle feeling”; TA: “quiet”; Tr: “I want something quiet” | None |
| `test_017` | CV: “so fed up”; TA: “rowdy and energetic to let it out”; Tr: “I want something rowdy and energetic to let it out” | None |
| `test_018` | None | “don't play English-language songs”; “I don't want tacky party-style music” |
| `test_019` | TA: “help me relax”; Tr: “start with something tense and exciting, then gradually help me relax” | None |
| `test_020` | TV: “neither sad nor happy”; Tr: “I want something neither sad nor happy” | None |
| `test_021` | MS: “a sense of surprise” | “not too loud” |
| `test_022` | CV: “a bit lonely” | None |
| `test_023` | TV: “hope”; Tr: “I want something that feels as if dawn has broken and there is hope” | None |
| `test_024` | TV: “not too sad”; TA: “not too rowdy”; Tr: “not too sad and not too rowdy” | “formulaic pop”; “tacky party-style tracks” |
| `test_025` | CA: “can't get going”; TA: “become more energetic”; Tr: “I want music to wake me up” | None |
| `test_026` | MP: “a tune I can hum along to” | “no one singing” |
| `test_027` | MS: “little surprises” | None |
| `test_028` | CV: “feel light as air”; TV: “happy”; Tr: “I want something relaxed and happy” | None |
| `test_029` | CV: “feeling very low”; TV: “don't want anything too cheerful”; TA: “quietly”; Tr: “I just want to sit quietly for a while” | None |
| `test_030` | None | None |

The `Tr` evidence for `single_target` may be a phrase establishing a music goal without ordering. The evidence for `test_010` does **not** instruct three songs to move from sadness to happiness; the person's later improvement is separate. `test_017`'s “rowdy” was author-approved as **energy**, not a verified loudness condition. `test_024`'s “not too rowdy” means an upper arousal bound (`≤2`), not exact arousal 2. These are project-specific, reviewed judgments, not universal claims about colloquial language.
