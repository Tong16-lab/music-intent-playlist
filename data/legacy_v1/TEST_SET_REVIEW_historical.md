> **History: The following content consists of old instructions or displays prior to the V2 migration and does not represent the current answer status. The current V2 has been verified by the author and migrated; the test set is not yet frozen, and 30 formal evaluations have not been run.**

# Test Answer Line-by-Line Verification Checklist

The two **draft test answer files** in this directory are [synthetic_intents_test.csv](synthetic_intents_test.csv) and [unsupported_conditions_test.csv](unsupported_conditions_test.csv). Each contains 30 rows, and their `review_status` is currently `needs_author_review`; they are not yet frozen, nor do they have formal evaluation scores. The 12 rows in [synthetic_intents_dev.csv](synthetic_intents_dev.csv) are for development use only.

Please compare the two test files by `case_id` and confirm line by line:

1. Whether the original sentence and the six core fields (five numerical fields and `trajectory`) conform to your operational criteria; whether the `*_evidence` next to non-empty values is indeed the basis from the original sentence.
2. Whether `unsupported_condition_phrases` lists only the **original terms** that the current music library cannot reliably guarantee, with positive requirements also counted; whether the corresponding `expected_cannot_guarantee_constraint` is correct. This column is JSON array text, write `[]` for an empty list.
3. Specially check `test_003` ("electronic music" is a positive requirement), `test_021` (sense of surprise has basis, arousal target has no basis), `test_022` (whether "can accompany me" belongs to un-guaranteed effects), `test_024` (whether "not too noisy" refers to volume), `test_028` ("relaxation" is insufficient to automatically output the arousal tier). These are drafts **pending the author's adjudication**, not frozen standard answers.

After confirmation, please change `review_status` to `approved` row by row in **the two test CSVs**; if there are objections, directly correct the answers and evidence, then run `python3 scripts/freeze_test_set.py check`. Only when both files pass verification completely and you input the confirmation sentence in the interactive terminal will the freeze command record the Singapore time and respective SHA-256 hashes at that moment.
