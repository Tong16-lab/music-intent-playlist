# 冻结后第二次正式运行：推荐层离线审计

仅使用已保存的本机私有预测、冻结的原句和 35 首正式曲库；没有 API 调用。这是推荐流程与条件可满足性检查，不是预先完成的推荐质量或用户喜好评估。

| 状态 | 数量 |
| --- | ---: |
| `ready` | 21/30 |
| `cannot_guarantee_constraint` | 7/30 |
| `insufficient_catalog` | 0/30 |
| `catalog_not_ready` | 0/30 |
| `invalid_intent_card` | 2/30 |

无效意图卡不参与推荐；`cannot_guarantee_constraint` 不选歌；曲库不足时不补足。模型意图判断成绩仍以本运行原始评估报告为准。
