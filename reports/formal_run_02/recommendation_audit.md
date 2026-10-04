# Second formal run after freezing: Recommendation layer offline audit

Only saved local private predictions, frozen original sentences, and 35 formal music tracks are used; no API calls. This is a recommendation workflow and conditional satisfiability check, not a pre-completed recommendation quality or user preference evaluation.

| Status | Count |
| --- | ---: |
| `ready` | 21/30 |
| `cannot_guarantee_constraint` | 7/30 |
| `insufficient_catalog` | 0/30 |
| `catalog_not_ready` | 0/30 |
| `invalid_intent_card` | 2/30 |

Invalid intent cards do not participate in recommendation; `cannot_guarantee_constraint` selects no songs; deficiencies are not backfilled when the music library is insufficient. Model intent judgment scores are still subject to the original evaluation report of this run.
