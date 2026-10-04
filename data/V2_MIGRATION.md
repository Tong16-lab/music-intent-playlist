# V2 答案迁移记录

唯一已获作者核对的来源：`user_intents_v2_review.tsv`。旧版 CSV 原样保存在 `legacy_v1/`。

V2 TSV SHA-256: `b91615ad96ffc1af86e0fec3547e1f9221bb850e6301cf886df7ca4321c2c576`

| 文件 | 旧版 SHA-256 | V2 行数 |
| --- | --- | ---: |
| `synthetic_intents_dev.csv` | `4fab6b52e550447b4abfd9dc75835f2d32d6933210260ef9f7dae014687cdff8` | 12 |
| `synthetic_intents_test.csv` | `bdc50cc24b8f954a0d50cfc062f49c29e9cf8aed08c86d67b41f7049fea06dda` | 30 |
| `unsupported_conditions_test.csv` | `8e1e13e340f68ee5abbbfc25da614ed83d47ffe7857da814884c6bedc3a7b059` | 30 |

迁移仅改变程序使用的答案文件；未冻结，也未运行正式评估。
