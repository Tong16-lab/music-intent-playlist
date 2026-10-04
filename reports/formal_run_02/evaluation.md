# PE6201 V2 正式合成测试评估

运行标识：**冻结后第二次正式运行**。
第一次运行仅尝试 3/30 条，因连续三次 `network` 失败停止，有效结果 0；本报告只统计第二次运行，不合并两次调用。

此报告只有在作者核对答案、冻结测试集并授权正式调用后才可生成。评估对象是合成表达，不是真人用户数据；不衡量尚未接入的正式歌曲曲库推荐效果。

候选：`compact-dev-v2`；模型：`google/gemini-3.5-flash-lite`；评分：`formal-scoring-v3`。
提示词 SHA-256：`1177a979ad7a42aa2a3d02c04563eed950c4ef74d9f081aa44bb1044742e3eb2`；Schema SHA-256：`c2d9e08fabefa74124fe3c22f9c74a991731a0bf67f42ca29e4ced9d2a44c344`；新加坡运行时间：`2026-10-03T19:38:01+08:00`。
冻结记录：`data/test_set_freeze.json`。

## 调用与校验阶段

实际调用 30/30；API 返回可处理响应 30/30；完整 JSON 30/30；必填结构完整 30/30；简写转换完成 30/30；V2 本地校验通过 28/30。
无有效意图卡 2/30；提前停止：否。阶段通过只说明数据可处理，不代表意图判断正确。

## 六个核心字段：主指标

端到端分母包含无效调用；仅有效输出分母只包含通过转换及本地校验的意图卡。关键词基线对同一批原话直接输出六字段，没有 API、JSON 或结构通过率。

| 字段 | AI 端到端 | AI 仅有效 | 关键词基线 |
| --- | ---: | ---: | ---: |
| `current_valence` | 26/30 | 26/28 | 27/30 |
| `current_arousal` | 26/30 | 26/28 | 29/30 |
| `target_valence` | 22/30 | 22/28 | 20/30 |
| `target_arousal` | 16/30 | 16/28 | 23/30 |
| `target_melodic_surprise` | 27/30 | 27/28 | 26/30 |
| `trajectory` | 23/30 | 23/28 | 18/30 |

## 按批准答案是否明确表达划分

五个可空字段的非空批准答案属于明确表达子集，范围对象也算非空。`trajectory` 只有批准答案为 `from_to` 才算明确要求**歌曲顺序**；`single_target` 与 `none` 均属于未明确要求顺序。所有正确数都要求预测值与批准答案完全相等。

| 字段 | 明确子集句数 | AI 端到端 | AI 仅有效 | 关键词基线 |
| --- | ---: | ---: | ---: | ---: |
| `current_valence` | 8 | 7/8 | 7/8 | 6/8 |
| `current_arousal` | 2 | 2/2 | 2/2 | 1/2 |
| `target_valence` | 11 | 7/11 | 7/11 | 1/11 |
| `target_arousal` | 11 | 5/11 | 5/11 | 4/11 |
| `target_melodic_surprise` | 7 | 4/7 | 4/5 | 3/7 |
| `trajectory` | 1 | 1/1 | 1/1 | 0/1 |

未说明子集：五个可空字段的批准答案为 `null`；轨迹则指**未明确要求歌曲顺序**（包括 `single_target`、`none`）。AI 误填只在有效卡片内计算；失败调用另列未完成。轨迹的误填专指擅自输出 `from_to`，把 `single_target` 与 `none` 混淆另列。

| 字段 | 未说明子集句数 | AI 端到端精确 | AI 仅有效精确 | AI 有效误填 | 无效未完成 | 关键词基线精确 | 基线误填 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `current_valence` | 22 | 19/22 | 19/20 | 1/20 | 2 | 21/22 | 1/22 |
| `current_arousal` | 28 | 24/28 | 24/26 | 2/26 | 2 | 28/28 | 0/28 |
| `target_valence` | 19 | 15/19 | 15/17 | 2/17 | 2 | 19/19 | 0/19 |
| `target_arousal` | 19 | 11/19 | 11/17 | 6/17 | 2 | 19/19 | 0/19 |
| `target_melodic_surprise` | 23 | 23/23 | 23/23 | 0/23 | 0 | 23/23 | 0/23 |
| `trajectory` | 29 | 22/29 | 22/27 | 2/27 | 2 | 18/29 | 0/29 |
无顺序分类错误：AI 3/27 条有效卡片；关键词基线 11/29。

## 严格补充指标与不支持条件

六字段整卡全对：AI 端到端 11/30；仅有效 11/28；关键词基线 12/30。整卡是严格补充指标，不单独代表理解能力。
`requires_melody_present`：AI 端到端 28/30；仅有效 28/28。

| 不支持条件指标 | AI 端到端 | AI 仅有效 |
| --- | ---: | ---: |
| 是否正确判断存在无法保证条件 | 27/30 | 27/28 |
| 截取原词集合完全一致 | 24/30 | 24/28 |
仅有效卡片的原词：精确命中 6、误报 5、漏报 7。
端到端预期原词 14 个、未完成 8 个；其中 1 个来自无效调用，不算模型原词漏报。

## 用量、失败和限制

输入／完成／总 token：44616／4887／49503；可取得推理 token：0（缺明细 0 次）。
按标准费率估算 USD 0.025602；缺少可估数据 0 次。实际账单以服务商为准。
实际调用中的失败分组：{"field_value": 2}；安全错误类别：{"invalid_field_value": 2}。

- `test_001`：有效；错误核心字段：current_arousal, target_valence；不支持条件状态错误：False；原词集合错误：False。
- `test_002`：有效；错误核心字段：target_arousal；不支持条件状态错误：False；原词集合错误：False。
- `test_003`：有效；错误核心字段：target_arousal, trajectory；不支持条件状态错误：False；原词集合错误：True。
- `test_004`：有效；错误核心字段：current_arousal, target_melodic_surprise；不支持条件状态错误：False；原词集合错误：False。
- `test_005`：无有效卡片 / `invalid_field_value`
- `test_007`：有效；错误核心字段：target_arousal；不支持条件状态错误：False；原词集合错误：False。
- `test_008`：有效；错误核心字段：target_arousal；不支持条件状态错误：False；原词集合错误：False。
- `test_010`：有效；错误核心字段：current_valence, target_valence, trajectory；不支持条件状态错误：False；原词集合错误：False。
- `test_011`：有效；错误核心字段：target_arousal；不支持条件状态错误：False；原词集合错误：False。
- `test_012`：有效；错误核心字段：无；不支持条件状态错误：False；原词集合错误：True。
- `test_013`：有效；错误核心字段：target_valence, target_arousal；不支持条件状态错误：False；原词集合错误：False。
- `test_014`：有效；错误核心字段：target_valence, target_arousal, trajectory；不支持条件状态错误：False；原词集合错误：False。
- `test_015`：无有效卡片 / `invalid_field_value`
- `test_017`：有效；错误核心字段：target_arousal；不支持条件状态错误：False；原词集合错误：False。
- `test_018`：有效；错误核心字段：无；不支持条件状态错误：False；原词集合错误：True。
- `test_020`：有效；错误核心字段：target_arousal；不支持条件状态错误：False；原词集合错误：False。
- `test_021`：有效；错误核心字段：target_arousal, trajectory；不支持条件状态错误：True；原词集合错误：True。
- `test_024`：有效；错误核心字段：target_valence；不支持条件状态错误：False；原词集合错误：False。
- `test_025`：有效；错误核心字段：trajectory；不支持条件状态错误：False；原词集合错误：False。
- `test_028`：有效；错误核心字段：current_valence, target_arousal；不支持条件状态错误：False；原词集合错误：False。
- `test_029`：有效；错误核心字段：target_valence, target_arousal；不支持条件状态错误：False；原词集合错误：False。

关键词基线无需 JSON；结构通过率不是理解准确率。完整模型预测仅存于本机 Git 忽略目录，公开报告不含密钥、请求头或完整回复。冻结后不得暗改批准答案沿用本成绩。
