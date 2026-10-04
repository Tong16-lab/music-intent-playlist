# User Expression and Intent Annotation V2 (Verified by author, formal testing completed)

This page is generated from the [English V2 annotation table](user_intents_v2_review.tsv) and presents all 42 examples (12 development and 30 test). These are not quotations collected from participants. The author approved the annotations. This English rendering was not used in the recorded Chinese-input evaluation; the exact evaluated table is preserved at commit `a39e3fc`. See the [V2 README](USER_INTENT_ANNOTATION_V2_README.md) for the rules and the [completed result](../reports/formal_run_02/EVALUATION_EN.md) for the historical score.

Blank fields are displayed as "Unspecified"; each non-empty field is followed by evidence from its English rendering. Recognizable melody is separate from the six core intent fields. All 42 records were reviewed by the author.

## Development Examples (12 items)

### dev_001 · P01

> Working overtime until my head is buzzing, I want to listen to something quiet to help me unwind, nothing too fancy.

- Current valence: -1 (slightly negative); evidence: "head is buzzing"
- Current arousal: Unspecified
- Target valence: Unspecified
- Target arousal: 1 (Low); evidence: "quiet"
- Target melodic surprise: 1 (Low); evidence: "nothing too fancy"
- Explicitly requires discernible melody: Not specified
- Playlist path: single_target (single target; evidence: "listen to something quiet to help me unwind")
- Unguaranteed explicit conditions: None
- Annotation notes: "Let me slow down" is an expected feeling; do not infer target valence=0 or current arousal=3.
- Audit status: Author Verified

### dev_002 · P01

> Squeezing into the subway in the morning is annoying enough, give me something that brightens my mood and perks me up a bit, but not too loud. Don't play mainstream pop hits for me.

- Current valence: -1 (slightly negative); evidence: "annoying enough"
- Current arousal: Unspecified
- Target valence: 1 (positive); evidence: "brightens my mood"
- Target arousal: 2 (Medium); evidence: "perks me up a bit"
- Target melodic surprise: Unspecified
- Explicitly requires discernible melody: Not specified
- Playlist path: single_target (single target; evidence: "brightens my mood and perks me up a bit")
- Unguaranteed explicit conditions: "not too loud"; "mainstream pop hits"
- Annotation notes: "Noisy" follows volume requirements and is not guaranteed by arousal.
- Audit status: Author Verified

### dev_003 · P01

> Want to zone out before bed, don't want to hear vocals.

- Current valence: Unspecified
- Current arousal: Unspecified
- Target valence: Unspecified
- Target arousal: Unspecified
- Target melodic surprise: Unspecified
- Explicitly requires discernible melody: Not specified
- Playlist path: none (No explicit music order)
- Unguaranteed explicit conditions: "don't want to hear vocals."
- Annotation notes: "Mind-wandering/spacing out" is an expected experience; do not automatically infer neutral emotion or low arousal.
- Audit status: Author Verified

### dev_004 · P02

> Feeling a bit blocked up inside today, want to listen to something that can accompany me in feeling blue for a while.

- Current valence: -1 (slightly negative); evidence: "Feeling a bit blocked up inside"
- Current arousal: Unspecified
- Target valence: -1 (negative); evidence: "feeling blue"
- Target arousal: Unspecified
- Target melodic surprise: Unspecified
- Explicitly requires discernible melody: Not specified
- Playlist path: single_target (single target; evidence: "want to listen to something that can accompany me in feeling blue")
- Unguaranteed explicit conditions: None
- Annotation notes: The user explicitly wants to listen to somewhat negative expressions; "accompany" does not constitute an outcome guarantee.
- Audit status: Author Verified

### dev_005 · P02

> I'm coding and want something energetic, not too sentimental, otherwise I won't feel like working.

- Current valence: Unspecified
- Current arousal: Unspecified
- Target valence: not lower than 0 (boundary: neutral, not an exact target); evidence: "not too sentimental"
- Target arousal: 2 (Medium); evidence: "energetic"
- Target melodic surprise: Unspecified
- Explicitly requires discernible melody: Not specified
- Playlist path: single_target (single target; evidence: "want something energetic")
- Unguaranteed explicit conditions: None
- Annotation notes: Author confirmation: "Not too melodramatic" operates with valence ≥ 0 among the three tiers of song tags in this project, allowing neutral or slightly positive songs and excluding -1; this is a coursework operational definition, and it is not claimed that the original phrasing naturally equates to this boundary. Arousal remains strictly 2.
- Audit status: Author Verified

### dev_006 · P02

> I keep hearing songs where you know what the next line will be right from the start. I'm sick of it and want something unexpected.

- Current valence: Unspecified
- Current arousal: Unspecified
- Target valence: Unspecified
- Target arousal: Unspecified
- Target melodic surprise: 3 (High); evidence: "unexpected"
- Explicitly requires discernible melody: Not specified
- Playlist path: none (No explicit music order)
- Unguaranteed explicit conditions: None
- Annotation notes: According to the project's preset definitions, map predictability expressions to melodic unexpectedness.
- Audit status: Author Verified

### dev_007 · P03

> I have an exam tomorrow and I'm extremely anxious right now. I want to calm down and feel grounded.

- Current valence: -1 (slightly negative); evidence: "extremely anxious"
- Current arousal: 3 (High); evidence: "extremely anxious"
- Target valence: Unspecified
- Target arousal: 1 (Low); evidence: "calm down"
- Target melodic surprise: Unspecified
- Explicitly requires discernible melody: Not specified
- Playlist path: single_target (single target; evidence: "want to calm down and feel grounded.")
- Unguaranteed explicit conditions: None
- Annotation notes: Personal emotions gradually easing does not equate to a strict requirement for the first track to be high and the last track to be low.
- Audit status: Author Verified

### dev_008 · P03

> I'm in a really great mood today and want to hear something upbeat, but please don't play generic club tracks.

- Current valence: 1 (slightly positive); evidence: "really great mood"
- Current arousal: Unspecified
- Target valence: 1 (positive); evidence: "upbeat"
- Target arousal: Unspecified
- Target melodic surprise: Unspecified
- Explicitly requires discernible melody: Not specified
- Playlist path: single_target (single target; evidence: "want to hear something upbeat")
- Unguaranteed explicit conditions: "don't play generic club tracks"
- Annotation notes: Tuhai (local electronic) songs have no verifiable track fields.
- Audit status: Author Verified

### dev_009 · P03

> No rock and no rap either, it gives me a headache.

- Current valence: Unspecified
- Current arousal: Unspecified
- Target valence: Unspecified
- Target arousal: Unspecified
- Target melodic surprise: Unspecified
- Explicitly requires discernible melody: Not specified
- Playlist path: none (No explicit music order)
- Unguaranteed explicit conditions: "No rock"; "no rap"
- Annotation notes: "Gives me a headache to listen to" is the rationale, not the currently experienced emotion.
- Audit status: Author Verified

### dev_010 · P04

> I'm going for a run and want something super high-energy, preferably with a few unexpected twists, and not those generic bubblegum pop songs.

- Current valence: Unspecified
- Current arousal: Unspecified
- Target valence: Unspecified
- Target arousal: 3 (High); evidence: "super high-energy"
- Target melodic surprise: 3 (High); evidence: "unexpected twists"
- Explicitly requires discernible melody: Not specified
- Playlist path: single_target (single target; evidence: "want something super high-energy")
- Unguaranteed explicit conditions: "not those generic bubblegum pop songs"
- Annotation notes: The broad term "unexpected" is interpreted according to this project's melodic exploration definition.
- Audit status: Author Verified

### dev_011 · P04

> Feeling a bit annoyed, I want something intense first to vent, and then slowly mellow out.

- Current valence: -1 (slightly negative); evidence: "a bit annoyed"
- Current arousal: Unspecified
- Target valence: Unspecified
- Target arousal: 1 (Low); evidence: "slowly mellow out"
- Target melodic surprise: Unspecified
- Explicitly requires discernible melody: Not specified
- Playlist path: from_to (Song activity gradually changes from 3 to 1; evidence: "first to vent, and then slowly mellow out")
- Unguaranteed explicit conditions: None
- Annotation notes: Author confirmation: "Hard-hitting" corresponds to song arousal 3, subsequently decreasing gradually to 1; target_arousal=1 represents the end point, and the song's starting point should not be mistakenly recorded as the user's current arousal level.
- Audit status: Author Verified

### dev_012 · P04

> Just give me some background music that is neither sad nor happy.

- Current valence: Unspecified
- Current arousal: Unspecified
- Target valence: 0 (neutral); evidence: "neither sad nor happy"
- Target arousal: Unspecified
- Target melodic surprise: Unspecified
- Explicitly requires discernible melody: Not specified
- Playlist path: single_target (single target; evidence: "Just give me some background music that is neither sad nor happy.")
- Unguaranteed explicit conditions: None
- Annotation notes: "Background music" is not interpreted as a strict instrumental-only condition.
- Audit status: Author Verified

## Test Examples (30 items)

### test_001 · P05

> Just finished an argument, feeling blocked up inside, want to listen to something that can slowly help me calm down.

- Current valence: -1 (slightly negative); evidence: "blocked up inside"
- Current arousal: Unspecified
- Target valence: Unspecified
- Target arousal: 1 (Low); evidence: "slowly help me calm down."
- Target melodic surprise: Unspecified
- Explicitly requires discernible melody: Not specified
- Playlist path: single_target (single target; evidence: "want to listen to something that can slowly help me calm down.")
- Unguaranteed explicit conditions: None
- Annotation notes: Do not rigidly label "feeling stuffy/distressed" as high arousal, nor rigidly label "calming down" as neutral emotion.
- Audit status: Author Verified

### test_002 · P05

> Lazy Sunday afternoon, I want to listen to something warm and relaxing.

- Current valence: Unspecified
- Current arousal: Unspecified
- Target valence: 1 (positive); evidence: "warm"
- Target arousal: Unspecified
- Target melodic surprise: Unspecified
- Explicitly requires discernible melody: Not specified
- Playlist path: single_target (single target; evidence: "I want to listen to something warm and relaxing.")
- Unguaranteed explicit conditions: None
- Annotation notes: "Relaxed" does not automatically equal low arousal; "lazy/languid" is not necessarily the current negative emotion.
- Audit status: Author Verified

### test_003 · P05

> No overly loud electronic music, and don't play cheesy club tracks for me either.

- Current valence: Unspecified
- Current arousal: Unspecified
- Target valence: Unspecified
- Target arousal: Unspecified
- Target melodic surprise: Unspecified
- Explicitly requires discernible melody: Not specified
- Playlist path: none (No explicit music order)
- Unguaranteed explicit conditions: "electronic music"; "overly loud"; "don't play cheesy club tracks"
- Annotation notes: Electronic music is a positive style requirement; none of the three items have reliable song field guarantees.
- Audit status: Author Verified

### test_004 · P06

> I've been under a lot of pressure lately, I want to listen to something healing, keeping it simple is fine, don't make it too complicated.

- Current valence: -1 (slightly negative); evidence: "under a lot of pressure"
- Current arousal: Unspecified
- Target valence: Unspecified
- Target arousal: Unspecified
- Target melodic surprise: 1 (Low); evidence: "keeping it simple"
- Explicitly requires discernible melody: Not specified
- Playlist path: none (No explicit music order)
- Unguaranteed explicit conditions: None
- Annotation notes: "Healing" is a soft experience goal; "complex" maps to low melodic surprise according to the project's confirmed definition.
- Audit status: Author Verified

### test_005 · P06

> I want to hear something that makes me go "Huh?", something where you can't guess what's coming next right away.

- Current valence: Unspecified
- Current arousal: Unspecified
- Target valence: Unspecified
- Target arousal: Unspecified
- Target melodic surprise: 3 (High); evidence: "you can't guess what's coming next right away"
- Explicitly requires discernible melody: Not specified
- Playlist path: none (No explicit music order)
- Unguaranteed explicit conditions: None
- Annotation notes: Maps to high melodic surprise according to the project definition.
- Audit status: Author Verified

### test_006 · P06

> It's rainy, I feel all damp inside, I want to hear something melancholic.

- Current valence: Unspecified
- Current arousal: Unspecified
- Target valence: -1 (negative); evidence: "melancholic"
- Target arousal: Unspecified
- Target melodic surprise: Unspecified
- Explicitly requires discernible melody: Not specified
- Playlist path: single_target (single target; evidence: "I want to hear something melancholic")
- Unguaranteed explicit conditions: None
- Annotation notes: Weather and "damp/humid" do not singly deduce the user's current emotion.
- Audit status: Author Verified

### test_007 · P07

> I am so sleepy I can barely keep my eyes open, give me something energizing, don't play slow songs.

- Current valence: Unspecified
- Current arousal: 1 (Low); evidence: "so sleepy I can barely keep my eyes open"
- Target valence: Unspecified
- Target arousal: 3 (High); evidence: "energizing"
- Target melodic surprise: Unspecified
- Explicitly requires discernible melody: Not specified
- Playlist path: single_target (single target; evidence: "give me something energizing")
- Unguaranteed explicit conditions: "don't play slow songs."
- Annotation notes: Slow songs belong to tempo requirements and cannot be guaranteed by arousal alone.
- Audit status: Author Verified

### test_008 · P07

> I want to play something upbeat while cooking.

- Current valence: Unspecified
- Current arousal: Unspecified
- Target valence: 1 (positive); evidence: "upbeat"
- Target arousal: 2 (Medium); evidence: "upbeat"
- Target melodic surprise: Unspecified
- Explicitly requires discernible melody: Not specified
- Playlist path: single_target (single target; evidence: "upbeat")
- Unguaranteed explicit conditions: None
- Annotation notes: "Brisk/cheerful" simultaneously expresses relatively positive and moderately active states.
- Audit status: Author Verified

### test_009 · P07

> I am going to read, don't play anything with vocals, it will distract me.

- Current valence: Unspecified
- Current arousal: Unspecified
- Target valence: Unspecified
- Target arousal: Unspecified
- Target melodic surprise: Unspecified
- Explicitly requires discernible melody: Not specified
- Playlist path: none (No explicit music order)
- Unguaranteed explicit conditions: "don't play anything with vocals"
- Annotation notes: The requirement involves vocals/lyrics, which existing song tags cannot guarantee.
- Audit status: Author Verified

### test_010 · P08

> Just went through a breakup, want to listen to something sad first to cry it out, and then slowly get better.

- Current valence: Unspecified
- Current arousal: Unspecified
- Target valence: -1 (negative); evidence: "sad"
- Target arousal: Unspecified
- Target melodic surprise: Unspecified
- Explicitly requires discernible melody: Not specified
- Playlist path: single_target (single target; evidence: "listen to something sad first")
- Unguaranteed explicit conditions: None
- Annotation notes: Author verification: "First" means wanting to listen to sad songs at this moment, while "then slowly get better" describes the person's state, without dictating the sequence of the three songs, a exclusive target for the first track, or the emotional trajectory of subsequent songs. target_valence=-1 is the currently executable musical target.
- Audit status: Author Verified

### test_011 · P08

> I want to hear something punchy, but not too convoluted; I don't understand those complex ones.

- Current valence: Unspecified
- Current arousal: Unspecified
- Target valence: Unspecified
- Target arousal: 3 (High); evidence: "punchy"
- Target melodic surprise: 1 (Low); evidence: "not too convoluted"
- Explicitly requires discernible melody: Not specified
- Playlist path: single_target (single target; evidence: "I want to hear something punchy")
- Unguaranteed explicit conditions: None
- Annotation notes: "Twisted / complex" maps to low melodic surprise according to the project's confirmed criteria.
- Audit status: Author Verified

### test_012 · P08

> Don't play those slow ballads, and don't play bubblegum pop either; they feel underwhelming.

- Current valence: Unspecified
- Current arousal: Unspecified
- Target valence: Unspecified
- Target arousal: Unspecified
- Target melodic surprise: Unspecified
- Explicitly requires discernible melody: Not specified
- Playlist path: none (No explicit music order)
- Unguaranteed explicit conditions: "slow ballads"; "bubblegum pop"
- Annotation notes: "Slow / lyrical style / bubblegum pop" are none of them existing reliable fields.
- Audit status: Author Verified

### test_013 · P09

> I'm so happy today, I want to hear something even more hype!

- Current valence: 1 (slightly positive); evidence: "so happy"
- Current arousal: Unspecified
- Target valence: 1 (positive); evidence: "even more hype"
- Target arousal: 3 (High); evidence: "even more hype"
- Target melodic surprise: Unspecified
- Explicitly requires discernible melody: Not specified
- Playlist path: single_target (single target; evidence: "I want to hear something even more hype")
- Unguaranteed explicit conditions: None
- Annotation notes: "High / energetic" is treated here according to positive and high-arousal musical expressions.
- Audit status: Author Verified

### test_014 · P09

> I'm a bit anxious, I want to hear something steady without any sudden big changes to startle me.

- Current valence: -1 (slightly negative); evidence: "a bit anxious"
- Current arousal: Unspecified
- Target valence: Unspecified
- Target arousal: Unspecified
- Target melodic surprise: 1 (Low); evidence: "sudden big changes"
- Explicitly requires discernible melody: Not specified
- Playlist path: none (No explicit music order)
- Unguaranteed explicit conditions: None
- Annotation notes: "Steady" does not specify an exact arousal tier; "change" maps to melodic surprise according to the project's confirmed criteria.
- Audit status: Author Verified

### test_015 · P09

> Give me something that sounds fresh, but not cheesy EDM.

- Current valence: Unspecified
- Current arousal: Unspecified
- Target valence: Unspecified
- Target arousal: Unspecified
- Target melodic surprise: 2 (Medium); evidence: "fresh"
- Explicitly requires discernible melody: Not specified
- Playlist path: none (No explicit music order)
- Unguaranteed explicit conditions: "not cheesy EDM"
- Annotation notes: Mapping novelty to medium-tier melodic surprise is the project criterion confirmed by the author.
- Audit status: Author Verified

### test_016 · P10

> Walking home at night, want to listen to something quiet with a gentle vibe.

- Current valence: Unspecified
- Current arousal: Unspecified
- Target valence: 1 (positive); evidence: "gentle vibe"
- Target arousal: 1 (Low); evidence: "quiet"
- Target melodic surprise: Unspecified
- Explicitly requires discernible melody: Not specified
- Playlist path: single_target (single target; evidence: "want to listen to something quiet")
- Unguaranteed explicit conditions: None
- Annotation notes: "Quiet" means low arousal; "gentle" is temporarily treated as a positive musical expression.
- Audit status: Author Verified

### test_017 · P10

> Annoying, annoying, I want to listen to something noisy to vent.

- Current valence: -1 (slightly negative); evidence: "Annoying, annoying,"
- Current arousal: Unspecified
- Target valence: Unspecified
- Target arousal: 3 (High); evidence: "noisy"
- Target melodic surprise: Unspecified
- Explicitly requires discernible melody: Not specified
- Playlist path: single_target (single target; evidence: "want to listen to something noisy to vent.")
- Unguaranteed explicit conditions: None
- Annotation notes: Author verification: "Noisy" refers to high-energy music, not high volume.
- Audit status: Author Verified

### test_018 · P10

> Don't play English songs, and I don't want to hear cheesy club music either.

- Current valence: Unspecified
- Current arousal: Unspecified
- Target valence: Unspecified
- Target arousal: Unspecified
- Target melodic surprise: Unspecified
- Explicitly requires discernible melody: Not specified
- Playlist path: none (No explicit music order)
- Unguaranteed explicit conditions: "Don't play English songs"; "cheesy club music"
- Annotation notes: There are no reliable fields for English lyrics language or cheesy/EDM-pop song categories.
- Audit status: Author Verified

### test_019 · P11

> Start with something tense and thrilling, and gradually help me relax later.

- Current valence: Unspecified
- Current arousal: Unspecified
- Target valence: Unspecified
- Target arousal: 1 (Low); evidence: "relax"
- Target melodic surprise: Unspecified
- Explicitly requires discernible melody: Not specified
- Playlist path: from_to (Song activity gradually changes from 3 to 1; evidence: "Start with something tense and thrilling, and gradually help me relax")
- Unguaranteed explicit conditions: None
- Annotation notes: Author verification: Song arousal gradually decreases from 3 to 1; target_arousal=1 is the endpoint. The starting point is recorded within the playlist path, without adding a new first-track field or mixing in the user's current state.
- Audit status: Author Verified

### test_020 · P11

> I want to listen to something neither sad nor happy, the plain and ordinary kind.

- Current valence: Unspecified
- Current arousal: Unspecified
- Target valence: 0 (neutral); evidence: "neither sad nor happy"
- Target arousal: Unspecified
- Target melodic surprise: Unspecified
- Explicitly requires discernible melody: Not specified
- Playlist path: single_target (single target; evidence: "I want to listen to something neither sad nor happy")
- Unguaranteed explicit conditions: None
- Annotation notes: Neutral emotion is clear; "plain and dull" does not automatically set a precise arousal level.
- Audit status: Author Verified

### test_021 · P11

> I want something unexpected, but not too noisy.

- Current valence: Unspecified
- Current arousal: Unspecified
- Target valence: Unspecified
- Target arousal: Unspecified
- Target melodic surprise: 3 (High); evidence: "unexpected"
- Explicitly requires discernible melody: Not specified
- Playlist path: none (No explicit music order)
- Unguaranteed explicit conditions: "not too noisy"
- Annotation notes: Only melody preference, not an emotional path; loud is a volume requirement that cannot be guaranteed.
- Audit status: Author Verified

### test_022 · P12

> Feeling a bit lonely, I want something to keep me company.

- Current valence: -1 (slightly negative); evidence: "a bit lonely"
- Current arousal: Unspecified
- Target valence: Unspecified
- Target arousal: Unspecified
- Target melodic surprise: Unspecified
- Explicitly requires discernible melody: Not specified
- Playlist path: none (No explicit music order)
- Unguaranteed explicit conditions: None
- Annotation notes: "Companionship" is a soft wish, cannot be used as a hard condition that must be guaranteed, nor does it automatically infer the target music emotion.
- Audit status: Author Verified

### test_023 · P12

> I want to hear something that makes it feel like dawn is breaking and brings hope.

- Current valence: Unspecified
- Current arousal: Unspecified
- Target valence: 1 (positive); evidence: "brings hope."
- Target arousal: Unspecified
- Target melodic surprise: Unspecified
- Explicitly requires discernible melody: Not specified
- Playlist path: single_target (single target; evidence: "want to hear something that makes it feel like dawn is breaking and brings hope.")
- Unguaranteed explicit conditions: None
- Annotation notes: "Something to look forward to" is treated as positive musical expression; listener's actual mood change is not guaranteed.
- Audit status: Author Verified

### test_024 · P12

> Don't be too sad, and don't be too rowdy either; no cheesy pop songs or tacky EDM.

- Current valence: Unspecified
- Current arousal: Unspecified
- Target valence: 0 (neutral); evidence: "too sad"
- Target arousal: not higher than 2 (boundary: Medium, not an exact target); evidence: "too rowdy"
- Target melodic surprise: Unspecified
- Explicitly requires discernible melody: Not specified
- Playlist path: single_target (single target; evidence: "Don't be too sad, and don't be too rowdy")
- Unguaranteed explicit conditions: "cheesy pop songs"; "tacky EDM"
- Annotation notes: Author verification: "Not too sad" is approximated as a neutral target; "Not too noisy" means music arousal ≤ 2, not a volume requirement, nor can it be forcibly filled as exactly 1 or 2. When the library arousal is unknown, it cannot be claimed that the upper limit is met; bubblegum pop / cheesy EDM still cannot be guaranteed.
- Audit status: Author Verified

### test_025 · P13

> I can't get up in the morning and want to use songs to wake myself up, preferably starting soft and slowly becoming energetic.

- Current valence: Unspecified
- Current arousal: 1 (Low); evidence: "can't get up in the morning"
- Target valence: Unspecified
- Target arousal: 3 (High); evidence: "energetic"
- Target melodic surprise: Unspecified
- Explicitly requires discernible melody: Not specified
- Playlist path: single_target (single target; evidence: "starting soft and slowly becoming energetic")
- Unguaranteed explicit conditions: None
- Annotation notes: Author verification: "Soft" describes the user's current state, not a track title; do not use this to map a clear low-to-high musical progression.
- Audit status: Author Verified

### test_026 · P13

> I want to hear something with no vocals, but it needs a tune I can hum along to.

- Current valence: Unspecified
- Current arousal: Unspecified
- Target valence: Unspecified
- Target arousal: Unspecified
- Target melodic surprise: Unspecified
- Explicitly requires discernible melody: Yes; Evidence: "tune I can hum along to"
- Playlist path: none (No explicit music order)
- Unguaranteed explicit conditions: "no vocals"
- Annotation notes: The author confirmed adding requires_melody_present=true, evidenced by "a tune you can hum along to", which only matches songs with melody_present=yes; this does not guarantee everyone can hum it. "No one singing" remains a vocal condition that the current music library cannot guarantee.
- Audit status: Author Verified

### test_027 · P13

> Ideally, each song should have a little unexpected surprise, rather than sounding the same all the way through.

- Current valence: Unspecified
- Current arousal: Unspecified
- Target valence: Unspecified
- Target arousal: Unspecified
- Target melodic surprise: 3 (High); evidence: "unexpected surprise"
- Explicitly requires discernible melody: Not specified
- Playlist path: none (No explicit music order)
- Unguaranteed explicit conditions: None
- Annotation notes: "Little surprise" maps to high melodic unexpectedness according to the author's confirmed standard.
- Audit status: Author Verified

### test_028 · P14

> Exams are finally over, I feel weightless all over, and I want to hear something relaxing and happy.

- Current valence: 1 (slightly positive); evidence: "weightless"
- Current arousal: Unspecified
- Target valence: 1 (positive); evidence: "happy"
- Target arousal: Unspecified
- Target melodic surprise: Unspecified
- Explicitly requires discernible melody: Not specified
- Playlist path: single_target (single target; evidence: "want to hear something relaxing and happy.")
- Unguaranteed explicit conditions: None
- Annotation notes: "Relaxed" does not automatically equal low arousal; retained as a soft description.
- Audit status: Author Verified

### test_029 · P14

> I am feeling very low, don't want to hear anything too upbeat, just want to sit quietly for a while.

- Current valence: -1 (slightly negative); evidence: "feeling very low"
- Current arousal: Unspecified
- Target valence: 0 (neutral); evidence: "don't want to hear anything too upbeat"
- Target arousal: 1 (Low); evidence: "sit quietly"
- Target melodic surprise: Unspecified
- Explicitly requires discernible melody: Not specified
- Playlist path: single_target (single target; evidence: "just want to sit quietly for a while")
- Unguaranteed explicit conditions: None
- Annotation notes: Author verification: Combined with "wanting to stay quiet for a while", this project approximates the target as neutral and low activity; it does not claim that "not too upbeat" strictly equals neutral on its own.
- Audit status: Author Verified

### test_030 · P14

> Just play anything.

- Current valence: Unspecified
- Current arousal: Unspecified
- Target valence: Unspecified
- Target arousal: Unspecified
- Target melodic surprise: Unspecified
- Explicitly requires discernible melody: Not specified
- Playlist path: none (No explicit music order)
- Unguaranteed explicit conditions: None
- Annotation notes: There are no emotional or melodic conditions that can be inferred from this, so it should be treated as exploratory recommendation.
- Audit status: Author Verified
