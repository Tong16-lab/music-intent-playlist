# V2 正式测试答案状态

**当前状态：作者已核对并迁移；测试集已冻结，第二次正式评估已完成。** 获作者核对的意图答案来源为 [user_intents_v2_review.tsv](user_intents_v2_review.tsv)（12 条开发、30 条测试，均为 `approved`）。冻结时间及文件哈希见 [test_set_freeze.json](test_set_freeze.json)；正式结果见 [第二次评估报告](../reports/formal_run_02/EVALUATION_EN.md)。判定依据见 [USER_INTENT_ANNOTATION_V2_README.md](USER_INTENT_ANNOTATION_V2_README.md)。

现行 [synthetic_intents_dev.csv](synthetic_intents_dev.csv)、[synthetic_intents_test.csv](synthetic_intents_test.csv) 与 [unsupported_conditions_test.csv](unsupported_conditions_test.csv) 均已从 V2 转换，分别为 12、30、30 行，不能把历史旧版答案的状态直接改成 `approved` 代替这次迁移。旧版原件及本文件过去的“待作者核对”清单保存在 [`legacy_v1/`](legacy_v1/)；那份清单是**历史记录，不代表当前需要重新核对 V2**。迁移说明见 [V2_MIGRATION.md](V2_MIGRATION.md)。

运行 `python3 scripts/sync_v2_answers.py check` 与 `python3 scripts/review_test_answers.py` 可核查原句、case ID、角色编号、字段值、逐字证据和不支持条件是否仍与 V2 一致。`test_022` 的不支持条件是空数组；`test_024` 仅列“口水歌”“土嗨歌”。

冻结记录载明新加坡时间 **2026-10-03 19:14:46**，以及 V2 TSV、30 条正式测试答案 CSV、30 条不支持条件答案 CSV 各自的 SHA-256。首次正式运行因网络问题提前停止，保留为独立记录；完成 30 条调用的是第二次正式运行，不应合并两次成绩。
