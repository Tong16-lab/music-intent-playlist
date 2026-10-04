> **History: The following content consists of old instructions or displays prior to the V2 migration and does not represent the current answer status. The current V2 has been verified by the author and migrated; the test set is not yet frozen, and 30 formal evaluations have not been run.**

# User Expression and Intent Annotation V2 (Pending Author Review)

This page is mechanically converted from the [V2 Annotation Table](../user_intents_v2_review.tsv); the original 42 examples (12 development, 30 test) are retained, with no newly added human data. For judgment rules and pending adjudication questions, see [V2 README](../USER_INTENT_ANNOTATION_V2_README.md). This page is not a frozen test answer.

Blank fields are displayed as "Unspecified"; each non-empty field is followed by the evidence from the original sentence. All records currently require the author's review.

## Development Examples (12 Items)

### dev_001 · P01

> Working overtime until my head is buzzing, I want to listen to something quiet to help me unwind, nothing too fancy.

- Current Valence: -1 (slightly negative); Evidence: "head is buzzing"
- Current Arousal: Unspecified
- Target Valence: Unspecified
- Target Arousal: 1 (low); Evidence: "quiet"
- Melody Novelty: 1 (low); Evidence: "nothing too fancy"
- Playlist Path: single_target (single target; Evidence: "I want to listen to something quiet to help me unwind")
- Unguaranteed Explicit Conditions: None
- Annotation Notes: "help me unwind" is an expected feeling; do not infer target valence = 0 or current arousal = 3.
- Review status: verified

### dev_002 · P01

> Squeezing onto the subway in the morning is annoying enough, give me something that's a bit more uplifting and brightens my mood, but not too loud. Don't play generic bubblegum pop for me.

- Current Valence: -1 (slightly negative); Evidence: "annoying enough"
- Current Arousal: Unspecified
- Target Valence: 1 (slightly positive); Evidence: "brightens my mood"
- Target Arousal: 2 (medium); Evidence: "a bit more uplifting"
- Melody surprise: Not specified
- Playlist path: single_target (single target; evidence: "give me something that perks me up and brightens my mood")
- Explicit conditions that cannot be guaranteed: "don't be too noisy"; "don't play bubblegum pop for me"
- Annotation note: "Noisy" is handled via volume requirements, not guaranteed by arousal.
- Review status: verified

### dev_003 · P01

> Want to zone out before bed, don't want to hear anyone singing.

- Current emotion: Not specified
- Current Arousal: Unspecified
- Target Valence: Unspecified
- Desired arousal: Not specified
- Melody surprise: Not specified
- Playlist path: none (no explicit music sequence)
- Explicit conditions that cannot be guaranteed: "don't want to hear anyone singing"
- Annotation note: "Zone out" is an expected experience, and does not automatically imply neutral emotion or low arousal.
- Review status: Pending author review

### dev_004 · P02

> Feeling a bit stuffy inside today, want to listen to something that can accompany me in feeling gloomy for a while.

- Current emotion: -1 (tendency towards negative); evidence: "feeling a bit stuffy inside"
- Current Arousal: Unspecified
- Desired emotion: -1 (tendency towards negative); evidence: "feeling gloomy for a while"
- Desired arousal: Not specified
- Melody surprise: Not specified
- Playlist path: single_target (single target; evidence: "want to listen to something that can accompany me in feeling gloomy for a while")
- Unguaranteed Explicit Conditions: None
- Annotation note: The user explicitly wants to listen to negative-leaning expressions; "accompany" is not treated as an effect guarantee.
- Review status: Pending author review

### dev_005 · P02

> I am coding, want something energetic, don't be too sentimental, otherwise I'll be even less in the mood to work.

- Current emotion: Not specified
- Current Arousal: Unspecified
- Desired emotion: 0 (neutral); Evidence: "don't be too bitter/tragic"
- Desired arousal: 2 (medium); evidence: "a bit energetic"
- Melody surprise: Not specified
- Playlist path: single_target (single target; evidence: "want something energetic")
- Unguaranteed Explicit Conditions: None
- Annotation note: "Not too sorrowful" is temporarily approximated as a neutral target, not strictly equal to valence=0.
- Pending adjudication: Yes; temporarily cannot be directly used as a complete and sole golden standard for the entire card.
- Review status: Pending author review

### dev_006 · P02

> I keep hearing those songs where you know what the next line will be right from the start. I'm sick of it; I want something unexpected.

- Current emotion: Not specified
- Current Arousal: Unspecified
- Target Valence: Unspecified
- Desired arousal: Not specified
- Melodic surprise: 3 (high); evidence: "unexpected"
- Playlist path: none (no explicit music sequence)
- Unguaranteed Explicit Conditions: None
- Annotation note: According to the project's preset definition, predictability expressions are mapped to melodic surprise.
- Review status: Pending author review

### dev_007 · P03

> I have an exam tomorrow and my heart is racing so much right now, I want to calm down and feel grounded.

- Current valence: -1 (negative-leaning); evidence: "heart is racing so much"
- Current arousal: 3 (high); evidence: "heart is racing so much"
- Target Valence: Unspecified
- Target arousal: 1 (low); evidence: "settle down"
- Melody surprise: Not specified
- Playlist path: single_target (single target; evidence: "want to slowly settle down")
- Unguaranteed Explicit Conditions: None
- Annotation note: Personal emotions gradually easing does not equate to an explicit requirement for the first song to be high and the last song to be low.
- Review status: Pending author review

### dev_008 · P03

> I'm in a really great mood today, I want to hear something upbeat, but don't play cheesy club tracks.

- Current valence: 1 (positive-leaning); evidence: "in a really great mood"
- Current Arousal: Unspecified
- Target valence: 1 (positive-leaning); evidence: "upbeat"
- Desired arousal: Not specified
- Melody surprise: Not specified
- Playlist path: single_target (single target; evidence: "want to hear something upbeat")
- Unguaranteed explicit condition: "don't play cheesy club tracks"
- Annotation note: Cheesy club tracks have no verifiable track metadata fields.
- Review status: Pending author review

### dev_009 · P03

> Don't play rock and don't play rap, listening to them gives me a headache.

- Current emotion: Not specified
- Current Arousal: Unspecified
- Target Valence: Unspecified
- Desired arousal: Not specified
- Melody surprise: Not specified
- Playlist path: none (no explicit music sequence)
- Unguaranteed explicit conditions: "no rock"; "no rap"
- Annotation note: "gives me a headache" is the reason, not the current emotion that has already occurred.
- Review status: Pending author review

### dev_010 · P04

> I'm going for a run and want to listen to something really energetic, preferably with some unexpected elements, and not that kind of bubblegum pop.

- Current emotion: Not specified
- Current Arousal: Unspecified
- Target Valence: Unspecified
- Desired arousal level: 3 (high); evidence: "really energetic"
- Melodic unexpectedness: 3 (high); evidence: "unexpected elements"
- Playlist path: single_target (single target; evidence: "want to listen to something really energetic")
- Unguaranteed explicit conditions: "not that kind of bubblegum pop"
- Annotation note: Broad "unexpected" is interpreted according to this project's melody exploration criteria.
- Review status: Pending author review

### dev_011 · P04

> Feeling a bit annoyed, want something intense to vent first, and then slowly soften down.

- Current emotion: -1 (slightly negative); evidence: "feeling a bit annoyed"
- Current Arousal: Unspecified
- Target Valence: Unspecified
- Desired arousal level: 1 (low); evidence: "slowly soften down"
- Melody surprise: Not specified
- Playlist path: from_to (clear sequential change; evidence: "first give me some intense music to vent, and then slowly soften down")
- Unguaranteed Explicit Conditions: None
- Annotation note: The first track should strongly have clear evidence, but the six core fields do not include "first track target arousal"; cannot impersonate the user's current arousal.
- Pending adjudication: Yes; temporarily cannot be directly used as a complete and sole golden standard for the entire card.
- Review status: Pending author review

### dev_012 · P04

> Just give me some background music that is neither sad nor happy.

- Current emotion: Not specified
- Current Arousal: Unspecified
- Desired emotion: 0 (neutral); evidence: "neither sad nor happy"
- Desired arousal: Not specified
- Melody surprise: Not specified
- Playlist path: single_target (single target; evidence: "some background music that is neither sad nor happy")
- Unguaranteed Explicit Conditions: None
- Annotation note: "Background music" is not interpreted as a hard condition for instrumental music.
- Review status: Pending author review

## Test Samples (30 items)

### test_001 · P05

> Just finished an argument, feeling stuffy inside, want to listen to something that can slowly calm me down.

- Current emotion: -1 (slightly negative); Evidence: "feeling stuffy inside"
- Current Arousal: Unspecified
- Target Valence: Unspecified
- Desired energy level: 1 (low); Evidence: "slowly calm down"
- Melody surprise: Not specified
- Playlist path: single_target (single target; Evidence: "want to listen to something that can slowly calm me down")
- Unguaranteed Explicit Conditions: None
- Annotation note: Do not rigidly label "stuffy" as high arousal, nor "calm down" as neutral emotion.
- Review status: Pending author review

### test_002 · P05

> Lazy weekend afternoon, want to listen to something warm and relaxing.

- Current emotion: Not specified
- Current Arousal: Unspecified
- Desired emotion: 1 (slightly positive); Evidence: "warm"
- Desired arousal: Not specified
- Melody surprise: Not specified
- Playlist path: single_target (single target; Evidence: "want to listen to something warm and relaxing")
- Unguaranteed Explicit Conditions: None
- Annotation note: "Relaxing" does not automatically equal low arousal; "lazy" is not necessarily a current negative emotion.
- Review status: Pending author review

### test_003 · P05

> No overly noisy electronic music, and don't play cheesy club tracks for me.

- Current emotion: Not specified
- Current Arousal: Unspecified
- Target Valence: Unspecified
- Desired arousal: Not specified
- Melody surprise: Not specified
- Playlist path: none (no explicit music sequence)
- Unguaranteed explicit conditions: "electronic music"; "not too noisy"; "don't play cheesy club tracks for me"
- Annotation note: Electronic music is a positive style requirement; none of the three items have reliable song metadata guarantees.
- Review status: Pending author review

### test_004 · P06

> Under a lot of pressure lately, want to listen to something healing, just keep it simple, don't make it too complicated.

- Current emotion: -1 (slightly negative); Evidence: "under a lot of pressure"
- Current Arousal: Unspecified
- Target Valence: Unspecified
- Desired arousal: Not specified
- Melody surprise: 1 (low); Evidence: "don't make it too complicated"
- Playlist path: none (no explicit music sequence)
- Unguaranteed Explicit Conditions: None
- Annotation note: "Healing" is a soft experience goal; "complicated" maps to low melody surprise according to project-confirmed criteria.
- Review status: Pending author review

### test_005 · P06

> Want to listen to something that makes me go "huh?", don't let me guess the rest the moment I hear it.

- Current emotion: Not specified
- Current Arousal: Unspecified
- Target Valence: Unspecified
- Desired arousal: Not specified
- Melody surprise: 3 (high); Evidence: "don't let me guess the rest the moment I hear it"
- Playlist path: none (no explicit music sequence)
- Unguaranteed Explicit Conditions: None
- Annotation note: Map high melodic surprise according to project criteria.
- Review status: Pending author review

### test_006 · P06

> It's raining, and I feel all damp and humid. I want to listen to something sad.

- Current emotion: Not specified
- Current Arousal: Unspecified
- Desired valence: -1 (negative bias); Evidence: "sad"
- Desired arousal: Not specified
- Melody surprise: Not specified
- Playlist path: single_target (single target; Evidence: "want to listen to something sad")
- Unguaranteed Explicit Conditions: None
- Annotation note: Weather and "dampness" do not independently determine the user's current emotion.
- Review status: Pending author review

### test_007 · P07

> I'm so sleepy I can't keep my eyes open, give me something energizing, don't play slow songs.

- Current emotion: Not specified
- Current arousal: 1 (low); Evidence: "so sleepy I can't keep my eyes open"
- Target Valence: Unspecified
- Desired activity: 3 (high); Evidence: "energizing"
- Melody surprise: Not specified
- Playlist path: single_target (single target; Evidence: "give me something energizing")
- Explicit condition that cannot be guaranteed: "don't play slow songs"
- Annotation note: Slow songs pertain to tempo requirements and cannot be guaranteed solely based on arousal.
- Review status: Pending author review

### test_008 · P07

> I want to play something upbeat while cooking.

- Current emotion: Not specified
- Current Arousal: Unspecified
- Desired valence: 1 (positive bias); Evidence: "upbeat"
- Desired activity: 2 (medium); Evidence: "upbeat"
- Melody surprise: Not specified
- Playlist path: single_target (single target; Evidence: "want to play something upbeat")
- Unguaranteed Explicit Conditions: None
- Annotation note: "Upbeat" simultaneously expresses relatively positive valence and moderate activity.
- Review status: Pending author review

### test_009 · P07

> I'm going to read a book, don't play anything with vocals, it will distract me.

- Current emotion: Not specified
- Current Arousal: Unspecified
- Target Valence: Unspecified
- Desired arousal: Not specified
- Melody surprise: Not specified
- Playlist path: none (no explicit music sequence)
- Explicit condition that cannot be guaranteed: "don't play anything with vocals"
- Annotation note: Requirements involve vocals/lyrics, which current song tags cannot guarantee.
- Review status: Pending author review

### test_010 · P08

> Just broke up, I want to listen to something sad first, have a good cry, and then slowly start to feel better.

- Current emotion: Not specified
- Current Arousal: Unspecified
- Desired valence: -1 (tends negative); Evidence: "sad"
- Desired arousal: Not specified
- Melody surprise: Not specified
- Playlist path: single_target (single target; Evidence: "want to listen to something sad first")
- Unguaranteed Explicit Conditions: None
- Annotation note: Only specifies listening to negative music first; "getting better gradually" is the expected effect, and subsequent song changes are not specified, so a complete music path cannot be rigidly annotated.
- Pending adjudication: Yes; temporarily cannot be directly used as a complete and sole golden standard for the entire card.
- Review status: Pending author review

### test_011 · P08

> I want to hear something high-energy, but not too convoluted; I don't understand those complex things.

- Current emotion: Not specified
- Current Arousal: Unspecified
- Target Valence: Unspecified
- Desired energy/arousal: 3 (high); Evidence: "high-energy"
- Melody surprise/unpredictability: 1 (low); Evidence: "not too convoluted"
- Playlist path: single_target (single target; Evidence: "want to hear something high-energy")
- Unguaranteed Explicit Conditions: None
- Annotation note: "Convoluted / complex" maps to low melody surprise according to the project's confirmed guidelines.
- Review status: Pending author review

### test_012 · P08

> Don't play those slow ballads, and don't play bubblegum pop either; listening to them feels like nothing.

- Current emotion: Not specified
- Current Arousal: Unspecified
- Target Valence: Unspecified
- Desired arousal: Not specified
- Melody surprise: Not specified
- Playlist path: none (no explicit music sequence)
- Explicit conditions that cannot be guaranteed: "Don't play those slow ballads"; "Don't play bubblegum pop"
- Annotation note: Slow tempo / ballad style / bubblegum pop are none of them reliable existing fields.
- Review status: Pending author review

### test_013 · P09

> Today is way too happy, I want to listen to something even more hyped!

- Current valence: 1 (tends positive); Evidence: "too happy"
- Current Arousal: Unspecified
- Desired valence: 1 (tends positive); Evidence: "even more hyped"
- Desired energy/arousal: 3 (high); Evidence: "even more hyped"
- Melody surprise: Not specified
- Playlist path: single_target (single target; Evidence: "want to listen to something even more hyped")
- Unguaranteed Explicit Conditions: None
- Annotation note: "hai" is treated here as a positive and high-arousal musical expression.
- Review status: Pending author review

### test_014 · P09

> Feeling a bit anxious, I want to listen to something steady, without any sudden changes to startle me.

- Current emotion: -1 (slightly negative); evidence: "feeling a bit anxious"
- Current Arousal: Unspecified
- Target Valence: Unspecified
- Desired arousal: Not specified
- Melody surprise: 1 (low); evidence: "without any sudden changes"
- Playlist path: none (no explicit music sequence)
- Unguaranteed Explicit Conditions: None
- Annotation note: "steady" does not specify an exact arousal tier; "changes" maps to melody surprise according to the project's confirmed criteria.
- Review status: Pending author review

### test_015 · P09

> Give me something that sounds fresh, but not like cheesy high-energy club tracks.

- Current emotion: Not specified
- Current Arousal: Unspecified
- Target Valence: Unspecified
- Desired arousal: Not specified
- Melody surprise: 2 (medium); evidence: "fresh"
- Playlist path: none (no explicit music sequence)
- Unguaranteed explicit condition: "not like cheesy high-energy club tracks"
- Annotation note: Mapping freshness to medium melody surprise is a project standard confirmed by the authors.
- Review status: Pending author review

### test_016 · P10

> Walking home at night, I want to listen to something quiet with a tender feeling.

- Current emotion: Not specified
- Current Arousal: Unspecified
- Desired emotion: 1 (slightly positive); evidence: "tender feeling"
- Target Arousal: 1 (low); Evidence: "quiet"
- Melody surprise: Not specified
- Playlist path: single_target (single target; evidence: "want to listen to something quiet")
- Unguaranteed Explicit Conditions: None
- Annotation note: "quiet" implies low arousal; "tender" is temporarily treated as positive musical expression.
- Review status: Pending author review

### test_017 · P10

> So annoying, so annoying, I want to listen to something noisy to vent.

- Current emotion: -1 (slightly negative); evidence: "so annoying, so annoying"
- Current Arousal: Unspecified
- Target Valence: Unspecified
- Desired arousal: 3 (high); evidence: "noisy to vent"
- Melody surprise: Not specified
- Playlist path: single_target (single target; evidence: "want to listen to something noisy to vent")
- Unguaranteed Explicit Conditions: None
- Annotation note: "Noisy" is expressed here as high-energy music, not treated as a guaranteed volume threshold.
- Pending adjudication: Yes; temporarily cannot be directly used as a complete and sole golden standard for the entire card.
- Review status: Pending author review

### test_018 · P10

> Do not play English songs, and I don't want to listen to cheesy dance/EDM tracks.

- Current emotion: Not specified
- Current Arousal: Unspecified
- Target Valence: Unspecified
- Desired arousal: Not specified
- Melody surprise: Not specified
- Playlist path: none (no explicit music sequence)
- Unguaranteed explicit conditions: "Do not play English songs"; "I don't want to listen to cheesy dance/EDM tracks"
- Annotation notes: Neither English lyric language nor cheesy dance/EDM categories have reliable fields.
- Review status: Pending author review

### test_019 · P11

> Start with something tense and exciting, and slowly let me relax later.

- Current emotion: Not specified
- Current Arousal: Unspecified
- Target Valence: Unspecified
- Desired arousal: 1 (low); evidence: "relax later"
- Melody surprise: Not specified
- Playlist path: from_to (clear sequential change; evidence: "first give me something intense and thrilling, and then slowly let me relax afterwards")
- Unguaranteed Explicit Conditions: None
- Annotation note: The first high-activity music is clear, but cannot be written into "user's current arousal"; a separate first-track target field is needed.
- Pending adjudication: Yes; temporarily cannot be directly used as a complete and sole golden standard for the entire card.
- Review status: Pending author review

### test_020 · P11

> I want to listen to something neither sad nor happy, just plain and ordinary.

- Current emotion: Not specified
- Current Arousal: Unspecified
- Desired emotion: 0 (neutral); evidence: "neither sad nor happy"
- Desired arousal: Not specified
- Melody surprise: Not specified
- Playlist path: single_target (single target; evidence: "want to listen to something neither sad nor happy")
- Unguaranteed Explicit Conditions: None
- Annotation notes: Neutral emotion is clear; "plain and ordinary" does not automatically set a precise arousal level.
- Review status: Pending author review

### test_021 · P11

> I want something unexpected, but not too noisy.

- Current emotion: Not specified
- Current Arousal: Unspecified
- Target Valence: Unspecified
- Desired arousal: Not specified
- Melody unexpectedness: 3 (high); evidence: "unexpected feel"
- Playlist path: none (no explicit music sequence)
- Unguaranteed explicit conditions: "not too noisy"
- Annotation notes: Only melody preference, not an emotional path; noisy is an volume requirement that cannot be guaranteed.
- Review status: Pending author review

### test_022 · P12

> Feeling a bit lonely, I want to listen to something that can accompany me.

- Current emotion: -1 (slightly negative); evidence: "feeling a bit lonely"
- Current Arousal: Unspecified
- Target Valence: Unspecified
- Desired arousal: Not specified
- Melody surprise: Not specified
- Playlist path: none (no explicit music sequence)
- Unguaranteed Explicit Conditions: None
- Annotation notes: "Companionship" is a soft wish and cannot be used as a mandatory hard condition, nor does it automatically infer the target music emotion.
- Review status: Pending author review

### test_023 · P12

> I want to listen to something that makes people feel like dawn has broken and there is hope.

- Current emotion: Not specified
- Current Arousal: Unspecified
- Desired emotion: 1 (positive); Evidence: "something to look forward to"
- Desired arousal: Not specified
- Melody surprise: Not specified
- Playlist path: single_target (single target; Evidence: "wanting to hear something that makes it feel like dawn is breaking, with something to look forward to")
- Unguaranteed Explicit Conditions: None
- Annotation note: "something to look forward to" is treated as a positive musical expression; listener's actual mood change is not guaranteed.
- Review status: Pending author review

### test_024 · P12

> Not too sad, not too rowdy, and no bubblegum pop or cheesy club tracks.

- Current emotion: Not specified
- Current Arousal: Unspecified
- Desired emotion: 0 (neutral); Evidence: "not too sad"
- Desired arousal: Not specified
- Melody surprise: Not specified
- Playlist path: single_target (single target; evidence: "not too sad")
- Explicit conditions that cannot be guaranteed: "bubblegum pop"; "cheesy club tracks"
- Annotation note: "Not too sad -> neutral" is an approximation; "not too noisy" can refer to activity level or volume, and the target arousal is temporarily not forcibly filled in nor counted as an unsupported condition.
- Pending adjudication: Yes; temporarily cannot be directly used as a complete and sole golden standard for the entire card.
- Review status: Pending author review

### test_025 · P13

> Can't get out of bed in the morning, want to use songs to wake myself up, preferably starting soft and slowly becoming energetic.

- Current emotion: Not specified
- Current arousal level: 1 (low); Evidence: "can't get out of bed"
- Target Valence: Unspecified
- Desired energy level: 3 (high); Evidence: "becoming energetic"
- Melody surprise: Not specified
- Playlist path: from_to (clear sequential change; evidence: "from soft and slow to gradually energetic")
- Unguaranteed Explicit Conditions: None
- Annotation note: The user's current low activity and the first track being "soft" are two different facts; the first track goal is not listed as a single column in the six fields.
- Pending adjudication: Yes; temporarily cannot be directly used as a complete and sole golden standard for the entire card.
- Review status: Pending author review

### test_026 · P13

> Want to hear something without vocals, but it needs to have a tune you can hum along to.

- Current emotion: Not specified
- Current Arousal: Unspecified
- Target Valence: Unspecified
- Desired arousal: Not specified
- Melody surprise: Not specified
- Playlist path: none (no explicit music sequence)
- Explicit condition that cannot be guaranteed: "without vocals"
- Annotation note: "A tune you can hum along to" is a clear requirement that can be supported by melody_present=yes, but the current six fields lack this request field; it cannot be ignored.
- Pending adjudication: Yes; temporarily cannot be directly used as a complete and sole golden standard for the entire card.
- Review status: Pending author review

### test_027 · P13

> It's best if each song has a bit of a different small surprise, instead of being the same from start to finish.

- Current emotion: Not specified
- Current Arousal: Unspecified
- Target Valence: Unspecified
- Desired arousal: Not specified
- Melody surprise: 3 (high); Evidence: "small surprise"
- Playlist path: none (no explicit music sequence)
- Unguaranteed Explicit Conditions: None
- Annotation note: "small surprise" is mapped to high melody surprise per the author's confirmed standard.
- Review status: Pending author review

### test_028 · P14

> Finally finished exams, I feel totally light and carefree, want to listen to something relaxing and happy.

- Current mood: 1 (positive); Evidence: "feel totally light and carefree"
- Current Arousal: Unspecified
- Target mood: 1 (positive); Evidence: "happy"
- Desired arousal: Not specified
- Melody surprise: Not specified
- Playlist path: single_target (single target; Evidence: "want to listen to something relaxing and happy")
- Unguaranteed Explicit Conditions: None
- Annotation note: "Relaxing" does not automatically equal low arousal; kept as a soft description.
- Review status: Pending author review

### test_029 · P14

> Feeling very down, don't want to hear anything too upbeat, just want to sit quietly for a while.

- Current mood: -1 (negative); Evidence: "feeling very down"
- Current Arousal: Unspecified
- Target mood: 0 (neutral); Evidence: "don't want to hear anything too upbeat"
- Target energy: 1 (low); Evidence: "quietly"
- Melody surprise: Not specified
- Playlist path: single_target (single target; Evidence: "just want to sit quietly for a while")
- Unguaranteed Explicit Conditions: None
- Annotation note: "Not too cheerful -> neutral" is an approximation and does not indicate the user explicitly requests positive music.
- Pending adjudication: Yes; temporarily cannot be directly used as a complete and sole golden standard for the entire card.
- Review status: Pending author review

### test_030 · P14

> Play whatever.

- Current emotion: Not specified
- Current Arousal: Unspecified
- Target Valence: Unspecified
- Desired arousal: Not specified
- Melody surprise: Not specified
- Playlist path: none (no explicit music sequence)
- Unguaranteed Explicit Conditions: None
- Annotation note: No mood or melody conditions can be inferred, should be treated as exploratory recommendation.
- Review status: Pending author review
