> **历史记录：以下内容是 V2 迁移前的旧说明或展示，不代表当前答案状态。现行 V2 已获作者核对并迁移；测试集尚未冻结，也未运行 30 条正式评估。**

# 测试答案逐行核对清单

本目录的两份**测试答案草案**是 [synthetic_intents_test.csv](synthetic_intents_test.csv) 和 [unsupported_conditions_test.csv](unsupported_conditions_test.csv)。它们各有 30 行，`review_status` 当前均为 `needs_author_review`；尚未冻结，也没有正式评估成绩。[synthetic_intents_dev.csv](synthetic_intents_dev.csv) 的 12 行只用于开发。

请按 `case_id` 对照两份测试文件，逐行确认：

1. 原句和六个核心字段（五个数值字段及 `trajectory`）是否符合你的操作口径；非空值旁的 `*_evidence` 是否确实是原句中的依据。
2. `unsupported_condition_phrases` 是否只列当前曲库无法可靠保证的**原词**，正向要求也要计入；与此对应的 `expected_cannot_guarantee_constraint` 是否正确。该列为 JSON 数组文本，空列表写 `[]`。
3. 尤其核对 `test_003`（“电子乐”是正向要求）、`test_021`（意外感有依据，唤醒目标无依据）、`test_022`（“能陪着我的”是否属于无法保证的效果）、`test_024`（“别太闹”是否指音量）、`test_028`（“放松”不足以自动给出唤醒档位）。这些是**待作者裁定**的草案，不是已冻结标准答案。

确认后，请在**两份测试 CSV** 中逐行把 `review_status` 改为 `approved`；有异议时直接修正答案和依据，再运行 `python3 scripts/freeze_test_set.py check`。只有两份文件全部通过核查且你在交互终端输入确认句，冻结命令才会记录当时的新加坡时间和各自的 SHA-256。
