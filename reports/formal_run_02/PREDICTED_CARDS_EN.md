# English reading copy of the thirty recorded formal predictions

This table follows the case IDs and valid V2 field values in [`validated_cards_for_audit.jsonl`](validated_cards_for_audit.jsonl). It presents **model predictions**, not approved answers; compare with the [English answer table](../../data/USER_INTENTS_EN.md). `—` means a null/unset field. `CV/CA/TV/TA/MS/MP/Tr` have the meanings in the [codebook](../../docs/INTENT_AND_LABEL_CODEBOOK_EN.md). `≥` and `≤` are bounded predictions, not exact levels. `single` abbreviates `single_target`; `none` remains `none`. Invalid cases have no usable card and no fabricated field values. The Chinese provider-evidence phrases are retained in the machine artifact; the English constraint phrases below are for reading, not a new exact-phrase score.

| Case | Valid? | CV / CA | TV / TA / MS / MP / Tr | Predicted unsupported conditions, rendered in English |
| --- | --- | --- | --- | --- |
| `test_001` | Yes | -1 / 2 | 1 / 1 / — / — / single | None |
| `test_002` | Yes | — / — | 1 / 1 / — / — / single | None |
| `test_003` | Yes | — / — | — / ≤1 / — / — / single | Require electronic style; exclude tacky party-style music |
| `test_004` | Yes | -1 / 3 | — / — / — / — / none | None |
| `test_005` | No — invalid field value | — | No validated card | Not scored |
| `test_006` | Yes | — / — | -1 / — / — / — / single | None |
| `test_007` | Yes | — / 1 | — / ≥3 / — / — / single | No slow songs |
| `test_008` | Yes | — / — | 1 / ≥2 / — / — / single | None |
| `test_009` | Yes | — / — | — / — / — / — / none | No sung lyrics |
| `test_010` | Yes | -1 / — | 1 / — / — / — / valence -1→1 | None |
| `test_011` | Yes | — / — | — / ≥3 / 1 / — / single | None |
| `test_012` | Yes | — / — | — / — / — / — / none | Exclude slow sentimental songs; exclude formulaic pop |
| `test_013` | Yes | 1 / — | — / ≥3 / — / — / single | None |
| `test_014` | Yes | -1 / — | 1 / 1 / 1 / — / single | None |
| `test_015` | No — invalid field value | — | No validated card | Not scored |
| `test_016` | Yes | — / — | 1 / 1 / — / — / single | None |
| `test_017` | Yes | -1 / — | — / ≥3 / — / — / single | None |
| `test_018` | Yes | — / — | — / — / — / — / none | No English-language songs; no tacky party-style music |
| `test_019` | Yes | — / — | — / 1 / — / — / arousal 3→1 | None |
| `test_020` | Yes | — / — | 0 / 2 / — / — / single | None |
| `test_021` | Yes | — / — | — / ≤1 / 3 / — / single | None |
| `test_022` | Yes | -1 / — | — / — / — / — / none | None |
| `test_023` | Yes | — / — | 1 / — / — / — / single | None |
| `test_024` | Yes | — / — | ≥0 / ≤2 / — / — / single | Exclude formulaic pop; exclude tacky party-style music |
| `test_025` | Yes | — / 1 | — / 3 / — / — / arousal 1→3 | None |
| `test_026` | Yes | — / — | — / — / — / true / none | No singing |
| `test_027` | Yes | — / — | — / — / 3 / — / none | None |
| `test_028` | Yes | — / — | 1 / ≤2 / — / — / single | None |
| `test_029` | Yes | -1 / — | — / ≤1 / — / — / single | None |
| `test_030` | Yes | — / — | — / — / — / — / none | None |

Examples of the difference between prediction and approved answer: `test_010`'s predicted sadness-to-happiness **song** path conflicts with the approved reading that the *person* hopes to feel better; `test_017`'s `≥3` is a different representation from the approved exact target `3`; `test_024` predicts `TV≥0` whereas the approved operational approximation is exact neutral `TV=0`. The [detailed English score](EVALUATION_EN.md) counts these under the frozen rules. The table does not change those scores or endorse the predictions as correct.

## Predicted evidence phrases, translated for reading

These are the phrases attached to the *predicted* non-null fields. They are not the approved evidence in [`INTENT_EVIDENCE_EN.md`](../../data/INTENT_EVIDENCE_EN.md). A missing field in a row means the provider card supplied no phrase for it. The original Chinese spans in the JSONL remain authoritative for exact-substring validation.

| Case | Predicted evidence phrases by field |
| --- | --- |
| `test_001` | CV: “feel blocked up”; CA: “just had an argument”; TV and TA: “settle down” |
| `test_002` | TV: “warm”; TA: “easygoing” |
| `test_003` | TA: “not too loud” |
| `test_004` | CV and CA: “under a lot of pressure” |
| `test_005` | No validated card |
| `test_006` | TV: “sad” |
| `test_007` | CA: “so sleepy I can barely keep my eyes open”; TA: “energizing” |
| `test_008` | TV and TA: “light and upbeat” |
| `test_009` | No non-null field evidence |
| `test_010` | CV: “breakup”; TV: “feel better”; Tr: “sad, cry, then gradually feel better” |
| `test_011` | TA: “powerful”; MS: “not too convoluted; I cannot follow such complicated music” |
| `test_012` | No non-null field evidence |
| `test_013` | CV: “so happy”; TA: “even more exhilarating” |
| `test_014` | CV: “anxious”; TV and TA: “steady”; MS: “don't suddenly spring a big change on me” |
| `test_015` | No validated card |
| `test_016` | TV: “gentle”; TA: “quiet” |
| `test_017` | CV: “so fed up”; TA: “rowdy” |
| `test_018` | No non-null field evidence |
| `test_019` | TA: “gradually help me relax”; Tr: “start tense and exciting, then gradually help me relax” |
| `test_020` | TV: “neither sad nor happy”; TA: “plain and even” |
| `test_021` | TA: “not too loud”; MS: “surprising” |
| `test_022` | CV: “a bit lonely” |
| `test_023` | TV: “as if dawn has broken and there is hope” |
| `test_024` | TV: “not too sad”; TA: “not too rowdy” |
| `test_025` | CA: “can't get going”; TA: “energetic”; Tr: “from soft/sluggish to more energetic” |
| `test_026` | MP: “a tune I can hum along to” |
| `test_027` | MS: “ideally each song has its own little surprise; not the same from start to finish” |
| `test_028` | TV: “happy”; TA: “relaxed” |
| `test_029` | CV: “feeling very low”; TA: “don't want anything too cheerful” |
| `test_030` | No non-null field evidence |

Some translations reveal why a prediction was marked wrong: `test_001` uses “just had an argument” to infer current arousal, `test_003` treats loudness as an arousal target, and `test_010` uses personal recovery language as a song path. These remain observations of recorded output, not revisions to the answer key.
