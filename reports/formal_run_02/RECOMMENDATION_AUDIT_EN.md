# Second frozen formal run — offline recommendation routing audit

This is an English reading copy of [`recommendation_audit.md`](recommendation_audit.md). The audit used the saved, locally validated intent cards, the frozen requests, and the 35-track catalog. It made **no additional model call**. It checks recommendation routing and whether catalog fields can satisfy requested conditions; it does **not** measure music quality or listener enjoyment.

| Routing status | Cases out of 30 |
| --- | ---: |
| `ready` — three linked tracks selected | 21/30 |
| `cannot_guarantee_constraint` — no selection | 7/30 |
| `insufficient_catalog` — no padding to three | 0/30 |
| `catalog_not_ready` | 0/30 |
| `invalid_intent_card` — not passed to selection | 2/30 |

The second formal run's intent accuracy is scored in [`EVALUATION_EN.md`](EVALUATION_EN.md), not inferred from these routing counts. The separate author listening assessment is in [`AUTHOR_LISTENING_REVIEW_EN.md`](../AUTHOR_LISTENING_REVIEW_EN.md).
