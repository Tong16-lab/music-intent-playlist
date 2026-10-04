# compact-dev-v2：只改提示词的合成开发集比较

本轮沿用简写 v1 的 Schema、转换器、模型、请求参数、V2 已批准答案、关键词基线和本地校验器；只增加通用意图判定说明。所有请求只发送单条合成开发原话，不发送答案。没有使用正式测试句设计规则或进行调用。

版本：`compact-dev-v2`；v2 提示词 SHA-256：`1177a979ad7a42aa2a3d02c04563eed950c4ef74d9f081aa44bb1044742e3eb2`；v1 提示词 SHA-256：`8d32673870f7798f8e46d63a13ea5d31fe5a66d813044fcfb13f526fa1412b2a`；两版共同 Schema SHA-256：`c2d9e08fabefa74124fe3c22f9c74a991731a0bf67f42ca29e4ced9d2a44c344`。
模型：`google/gemini-3.5-flash-lite`；新加坡开始时间：`2026-10-03T18:31:04+08:00`。
预先估算费用 USD 0.013734（依据 v1 实测，用新增字符每字 2 个输入 token、完成 token 增加 25% 的假设）。
实际调用 12/12；提前停止：否。完整 JSON 12/12；必填结构完整 12/12；简写转换完成 11/12；V2 本地校验通过 8/12。
无有效卡片 4 次，其中 API 失败 0 次；失败分组 {"evidence": 1, "field_value": 2, "structure": 1}；安全错误类别 {"invalid_field_value": 3, "missing_evidence": 1}。

## 三版与同一关键词基线

| 指标 | 原版端到端 | 简写 v1 端到端 | 提示词 v2 端到端 | 同一关键词基线 |
| --- | ---: | ---: | ---: | ---: |
| `current_valence` | 5/12 | 9/12 | 8/12 | 9/12 |
| `current_arousal` | 5/12 | 7/12 | 7/12 | 11/12 |
| `target_valence` | 6/12 | 7/12 | 7/12 | 9/12 |
| `target_arousal` | 5/12 | 4/12 | 5/12 | 8/12 |
| `target_melodic_surprise` | 5/12 | 8/12 | 8/12 | 11/12 |
| `trajectory` | 6/12 | 7/12 | 7/12 | 8/12 |
| 六字段整卡 | 4/12 | 3/12 | 4/12 | 5/12 |
| requires_melody_present | 6/12 | 9/12 | 8/12 | — |
| 不支持条件原词集合全对 | 1/12 | 3/12 | 5/12 | — |
| cannot_guarantee_constraint 状态正确 | 4/12 | 6/12 | 7/12 | — |

仅有效输出的分母分别为原版 6、简写 v1 9、提示词 v2 8；下表只衡量通过转换及本地校验的卡片。

| 指标 | 原版仅有效 | 简写 v1 仅有效 | 提示词 v2 仅有效 |
| --- | ---: | ---: | ---: |
| `current_valence` | 5/6 | 9/9 | 8/8 |
| `current_arousal` | 5/6 | 7/9 | 7/8 |
| `target_valence` | 6/6 | 7/9 | 7/8 |
| `target_arousal` | 5/6 | 4/9 | 5/8 |
| `target_melodic_surprise` | 5/6 | 8/9 | 8/8 |
| `trajectory` | 6/6 | 7/9 | 7/8 |
| 六字段整卡 | 4/6 | 3/9 | 4/8 |
| 不支持条件原词集合全对 | 1/6 | 3/9 | 5/8 |
| cannot_guarantee_constraint 状态正确 | 4/6 | 6/9 | 7/8 |

端到端分母包含无有效卡片的调用；这种调用不记作模型原词误报或漏报。格式完整只表示输出可解析，不表示意图判断正确。

## 不支持条件：状态与原词分别计分

状态正确（端到端）：原版 4/12、简写 v1 6/12、v2 7/12。
原词集合完全一致（端到端）：原版 1/12、简写 v1 3/12、v2 5/12。
v2 仅有效输出：预期原词 7 个；精确命中 5、误报 3、漏报 2（8 条有效卡片）。端到端未完成原词 2 个，其中 0 个来自无有效卡片。

## 安全错误摘要

- `conversion`：1 次
- `local_validation`：3 次
- `dev_001`：evidence / missing_evidence / current_valence
- `dev_002`：有效；核心字段错误：current_arousal, target_arousal；原词集合错误：否。
- `dev_004`：structure / invalid_field_value / target_valence
- `dev_005`：有效；核心字段错误：target_arousal；原词集合错误：否。
- `dev_006`：field_value / invalid_field_value / trajectory
- `dev_007`：有效；核心字段错误：target_valence, trajectory；原词集合错误：否。
- `dev_008`：有效；核心字段错误：无；原词集合错误：是。
- `dev_009`：有效；核心字段错误：无；原词集合错误：是。
- `dev_010`：有效；核心字段错误：target_arousal；原词集合错误：否。
- `dev_011`：field_value / invalid_field_value / trajectory.arousal
- `dev_012`：有效；核心字段错误：无；原词集合错误：是。

## 用量和边界

v2 输入／完成／总 token：17887／2192／20079；可取得的推理 token：0（缺明细 0 次）。
v2 估算费用 USD 0.010846；缺可估数据 0 次。原版 USD 0.010593；简写 v1 USD 0.009787。实际账单以服务商为准。
原始模型预测和转换卡只存在本机被 Git 忽略的私有目录；公开报告不包含完整原始回复、请求头或密钥。未接入正式运行时、冻结或评估正式测试集。
