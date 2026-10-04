# PE6201 V2 正式合成测试评估

**运行状态说明（报告生成后补充，未改评分或答案）：**前三次调用均在网络阶段失败，未取得可处理的 API 响应；程序依预设规则停止，余下 27 句未调用。表中 AI 的 `0/30` 表示端到端未完成，**不能解释为模型在意图判断上 30 句全错，也不能与关键词基线作能力比较**。仅有效输出的分母为 0，因此语义准确率未评估。服务商未返回 token 或账单用量；下文 USD 0.000000 只是可取得用量的计算小计，实际是否收费**无法确认**。

此报告只有在作者核对答案、冻结测试集并授权正式调用后才可生成。评估对象是合成表达，不是真人用户数据；不衡量尚未接入的正式歌曲曲库推荐效果。

候选：`compact-dev-v2`；模型：`google/gemini-3.5-flash-lite`；评分：`formal-scoring-v3`。
提示词 SHA-256：`1177a979ad7a42aa2a3d02c04563eed950c4ef74d9f081aa44bb1044742e3eb2`；Schema SHA-256：`c2d9e08fabefa74124fe3c22f9c74a991731a0bf67f42ca29e4ced9d2a44c344`；新加坡运行时间：`2026-10-03T19:15:07+08:00`。
冻结记录：`data/test_set_freeze.json`。

## 调用与校验阶段

实际调用 3/30；API 返回可处理响应 0/30；完整 JSON 0/30；必填结构完整 0/30；简写转换完成 0/30；V2 本地校验通过 0/30。
无有效意图卡 30/30；提前停止：是。阶段通过只说明数据可处理，不代表意图判断正确。

## 六个核心字段：主指标

端到端分母包含无效调用；仅有效输出分母只包含通过转换及本地校验的意图卡。关键词基线对同一批原话直接输出六字段，没有 API、JSON 或结构通过率。

| 字段 | AI 端到端 | AI 仅有效 | 关键词基线 |
| --- | ---: | ---: | ---: |
| `current_valence` | 0/30 | 未评估（分母 0） | 27/30 |
| `current_arousal` | 0/30 | 未评估（分母 0） | 29/30 |
| `target_valence` | 0/30 | 未评估（分母 0） | 20/30 |
| `target_arousal` | 0/30 | 未评估（分母 0） | 23/30 |
| `target_melodic_surprise` | 0/30 | 未评估（分母 0） | 26/30 |
| `trajectory` | 0/30 | 未评估（分母 0） | 18/30 |

## 按批准答案是否明确表达划分

五个可空字段的非空批准答案属于明确表达子集，范围对象也算非空。`trajectory` 只有批准答案为 `from_to` 才算明确要求**歌曲顺序**；`single_target` 与 `none` 均属于未明确要求顺序。所有正确数都要求预测值与批准答案完全相等。

| 字段 | 明确子集句数 | AI 端到端 | AI 仅有效 | 关键词基线 |
| --- | ---: | ---: | ---: | ---: |
| `current_valence` | 8 | 0/8 | 未评估（分母 0） | 6/8 |
| `current_arousal` | 2 | 0/2 | 未评估（分母 0） | 1/2 |
| `target_valence` | 11 | 0/11 | 未评估（分母 0） | 1/11 |
| `target_arousal` | 11 | 0/11 | 未评估（分母 0） | 4/11 |
| `target_melodic_surprise` | 7 | 0/7 | 未评估（分母 0） | 3/7 |
| `trajectory` | 1 | 0/1 | 未评估（分母 0） | 0/1 |

未说明子集：五个可空字段的批准答案为 `null`；轨迹则指**未明确要求歌曲顺序**（包括 `single_target`、`none`）。AI 误填只在有效卡片内计算；失败调用另列未完成。轨迹的误填专指擅自输出 `from_to`，把 `single_target` 与 `none` 混淆另列。

| 字段 | 未说明子集句数 | AI 端到端精确 | AI 仅有效精确 | AI 有效误填 | 无效未完成 | 关键词基线精确 | 基线误填 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `current_valence` | 22 | 0/22 | 未评估（分母 0） | 未评估（分母 0） | 22 | 21/22 | 1/22 |
| `current_arousal` | 28 | 0/28 | 未评估（分母 0） | 未评估（分母 0） | 28 | 28/28 | 0/28 |
| `target_valence` | 19 | 0/19 | 未评估（分母 0） | 未评估（分母 0） | 19 | 19/19 | 0/19 |
| `target_arousal` | 19 | 0/19 | 未评估（分母 0） | 未评估（分母 0） | 19 | 19/19 | 0/19 |
| `target_melodic_surprise` | 23 | 0/23 | 未评估（分母 0） | 未评估（分母 0） | 23 | 23/23 | 0/23 |
| `trajectory` | 29 | 0/29 | 未评估（分母 0） | 未评估（分母 0） | 29 | 18/29 | 0/29 |
无顺序分类错误：AI 0/0 条有效卡片；关键词基线 11/29。

## 严格补充指标与不支持条件

六字段整卡全对：AI 端到端 0/30；仅有效 未评估（分母 0）；关键词基线 12/30。整卡是严格补充指标，不单独代表理解能力。
`requires_melody_present`：AI 端到端 0/30；仅有效 未评估（分母 0）。

| 不支持条件指标 | AI 端到端 | AI 仅有效 |
| --- | ---: | ---: |
| 是否正确判断存在无法保证条件 | 0/30 | 未评估（分母 0） |
| 截取原词集合完全一致 | 0/30 | 未评估（分母 0） |
没有有效卡片，原词命中／误报／漏报未评估。
端到端预期原词 14 个、未完成 14 个；其中 14 个来自无效调用，不算模型原词漏报。

## 用量、失败和限制

输入／完成／总 token：0／0／0；可取得推理 token：0（缺明细 3 次）。
按标准费率估算 USD 0.000000；缺少可估数据 3 次。实际账单以服务商为准。
实际调用中的失败分组：{"api": 3}；安全错误类别：{"network": 3}。

- `test_001`：无有效卡片 / `network`
- `test_002`：无有效卡片 / `network`
- `test_003`：无有效卡片 / `network`
- `test_004`：无有效卡片 / `not_attempted_after_stop`
- `test_005`：无有效卡片 / `not_attempted_after_stop`
- `test_006`：无有效卡片 / `not_attempted_after_stop`
- `test_007`：无有效卡片 / `not_attempted_after_stop`
- `test_008`：无有效卡片 / `not_attempted_after_stop`
- `test_009`：无有效卡片 / `not_attempted_after_stop`
- `test_010`：无有效卡片 / `not_attempted_after_stop`
- `test_011`：无有效卡片 / `not_attempted_after_stop`
- `test_012`：无有效卡片 / `not_attempted_after_stop`
- `test_013`：无有效卡片 / `not_attempted_after_stop`
- `test_014`：无有效卡片 / `not_attempted_after_stop`
- `test_015`：无有效卡片 / `not_attempted_after_stop`
- `test_016`：无有效卡片 / `not_attempted_after_stop`
- `test_017`：无有效卡片 / `not_attempted_after_stop`
- `test_018`：无有效卡片 / `not_attempted_after_stop`
- `test_019`：无有效卡片 / `not_attempted_after_stop`
- `test_020`：无有效卡片 / `not_attempted_after_stop`
- `test_021`：无有效卡片 / `not_attempted_after_stop`
- `test_022`：无有效卡片 / `not_attempted_after_stop`
- `test_023`：无有效卡片 / `not_attempted_after_stop`
- `test_024`：无有效卡片 / `not_attempted_after_stop`
- `test_025`：无有效卡片 / `not_attempted_after_stop`
- `test_026`：无有效卡片 / `not_attempted_after_stop`
- `test_027`：无有效卡片 / `not_attempted_after_stop`
- `test_028`：无有效卡片 / `not_attempted_after_stop`
- `test_029`：无有效卡片 / `not_attempted_after_stop`
- `test_030`：无有效卡片 / `not_attempted_after_stop`

关键词基线无需 JSON；结构通过率不是理解准确率。完整模型预测仅存于本机 Git 忽略目录，公开报告不含密钥、请求头或完整回复。冻结后不得暗改批准答案沿用本成绩。
