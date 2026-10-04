# PE6201 V2 开发集合成句评估

仅使用作者已批准的 12 条开发句；这不是正式测试成绩，也不是真人用户数据。每次请求只含原话、固定运行时提示词和 Schema，不含答案。

模型：`google/gemini-3.5-flash-lite`；新加坡开始时间：`2026-10-03T17:29:58+08:00`。
实际调用 12/12；未调用 0；完整 JSON 12/12；必填结构完整 7/12；本地有效意图卡 6/12。
API 失败 0；格式／结构失败 5；证据失败 0；字段值失败 1。
另有 5/6 条本地有效输出与已批准答案不完全一致；这是意图判断差异，未归为格式或证据失败。
提前停止：否。

失败分组已依据保存的安全结构标志离线校正；没有重新调用模型或改动标准答案。

## 六个核心字段

| 字段 | 开发集覆盖（正确／12） | 已调用端到端 | 仅有效输出 | 关键词基线（已调用） |
| --- | ---: | ---: | ---: | ---: |
| `current_valence` | 5/12 | 5/12 | 5/6 | 9/12 |
| `current_arousal` | 5/12 | 5/12 | 5/6 | 11/12 |
| `target_valence` | 6/12 | 6/12 | 6/6 | 9/12 |
| `target_arousal` | 5/12 | 5/12 | 5/6 | 8/12 |
| `target_melodic_surprise` | 5/12 | 5/12 | 5/6 | 11/12 |
| `trajectory` | 6/12 | 6/12 | 6/6 | 8/12 |
| 六字段整卡 | 4/12 | 4/12 | 4/6 | 5/12 |
| requires_melody_present | 6/12 | 6/12 | 6/6 | — |
| 不支持条件原词集合全对 | 1/12 | 1/12 | 1/6 | — |
| cannot_guarantee_constraint 状态 | 4/12 | 4/12 | 4/6 | — |

开发集覆盖列把未调用句记为未完成，不代表模型对这些句子判断错误。端到端列把已调用但无有效意图卡的句子计入分母；仅有效输出列只衡量通过本地校验的意图卡。

## 不支持条件原词

已调用句预期原词 7 个；端到端未完成 7 个，其中 3 个属于无有效意图卡。
仅有效输出：命中 0、误报 6、漏报 4（仅在 6 条有效输出内计算）。

## 安全错误摘要

- `invalid_field_value`：6 次

## 逐句安全摘要

- `dev_001`：有效；核心字段错误：current_valence, current_arousal, target_melodic_surprise；不支持条件集合错误：是。
- `dev_002`：structure / `invalid_field_value` / `target_arousal`
- `dev_003`：structure / `invalid_field_value` / `target_arousal`
- `dev_004`：有效；核心字段错误：无；不支持条件集合错误：否。
- `dev_005`：structure / `invalid_field_value` / `target_valence`
- `dev_006`：field_value / `invalid_field_value` / `trajectory`
- `dev_007`：structure / `invalid_field_value` / `trajectory.arousal`
- `dev_008`：有效；核心字段错误：target_arousal；不支持条件集合错误：是。
- `dev_009`：有效；核心字段错误：无；不支持条件集合错误：是。
- `dev_010`：有效；核心字段错误：无；不支持条件集合错误：是。
- `dev_011`：structure / `invalid_field_value` / `target_arousal`
- `dev_012`：有效；核心字段错误：无；不支持条件集合错误：是。

## 用量与范围

输入／完成／总 token：16711／2232／18943；可取得的推理 token 合计：0（缺明细 0 次）。
估算费用：USD 0.010593；缺少可估费用数据的调用 0 次。实际账单以服务商为准。
没有下载音频或评估真实曲库推荐效果。测试集未冻结，30 条正式测试未运行。
