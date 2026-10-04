# 完整结构化输出 Schema：离线兼容性核查

> **历史核查记录。** 本文记录当时尚含五处可空数值 `enum` 的正式 Schema。后续正式运行时 Schema 只移除了这五处 `enum`；旧完整 Schema 短提示词探针与旧九字段中间探针已在各自脚本中固定当时的枚举，保留对照可复现性。本文的“当前正式 Schema”均指记录撰写时的版本。

本记录只检查本地代码和官方公开文档；没有向 OpenRouter 或 Gemini 发起推理请求。已有观察是：同一模型、同一句合成句的两字段极简探针成功，而完整九字段 Schema 配合长、短提示词都曾返回缺字段结果。它们只说明**这些组合的结果不同**，不能确定根因。历史调用没有保存完整回复，也不能重建当时实际落到的提供方端点。

## 官方文档与当前路由的边界

| 特性 | 当前正式 Schema 用法 | Google Gemini 官方文档 | OpenRouter 官方文档／当前路由 |
| --- | --- | --- | --- |
| `anyOf` | `target_valence`、`target_arousal`、`trajectory` 各一处；分支包含标量和对象 | **明确支持语法**：结构化输出示例使用 `anyOf`，GenerateContent 的 JSON Schema 支持列表也列出它。 | **未说明此关键词在当前端点如何处理**。文档说明 `strict=true` 的执行因端点而异。 |
| 可空类型 | 多处 `type:["integer","null"]`、`["boolean","null"]`、`["string","null"]`；数值枚举还包含 `null` | **明确支持**将 `"null"` 放在 `type` 数组中。整数枚举与可空类型各有说明；**未明确说明**“枚举同时包含数字和 `null`”这一组合。 | **未逐项说明**当前 OpenRouter→Gemini 端点对可空类型或混合枚举的支持。 |
| 嵌套必填对象 | `evidence` 七个必填键；`constraints[]` 三个必填键；范围对象与路径对象再嵌套 | **明确支持语法**：对象的 `properties`／`required` 已列明，官方示例也有嵌套对象及必填项。文档同时提醒很大或很深的 Schema 可能被拒绝，但没有给本模型的阈值。 | 示例明确展示**顶层** `required`；**未逐项说明**当前端点对这里的多层嵌套保证到什么程度。 |
| `additionalProperties:false` | 顶层、范围、路径、证据和约束对象均使用 | **明确支持语法**：对象属性列表包含 `additionalProperties`。 | 官方示例明确在顶层使用 `false`；**未逐项说明**当前端点的嵌套使用。 |

来源：[OpenRouter Structured Outputs](https://openrouter.ai/docs/guides/features/structured-outputs)、[OpenRouter Gemini 3.5 Flash Lite 模型页](https://openrouter.ai/google/gemini-3.5-flash-lite)、[Google Gemini Structured Outputs](https://ai.google.dev/gemini-api/docs/structured-output)、[Google GenerateContent API](https://ai.google.dev/api/generate-content)。Google 文档描述 Gemini 自身接口的能力，**不能直接推定** OpenRouter 所选端点完整保留每个 Schema 约束。OpenRouter 明确指出支持按提供方端点决定；`require_parameters=true` 有助于选择宣称支持参数的端点，`strict=true` 在不同端点也未必都能保证完全遵从。

**本地代码推断：**当前正式 Schema 使用的都是文档中列出的基本关键词，没有看到明显拼写错误或无效 JSON；不过其多个可空枚举、联合分支、嵌套必填对象的**组合**是否在实际路由上稳定执行，文档没有证明。既往“HTTP 成功但缺字段”意味着该次回复没有满足本地必填检查，不能据此反推哪一层忽略了 Schema，也不能断言是模型、路由还是提示词造成。

## 正式 Schema 与本地校验

以下差异只提出后续版本的修正方向；本轮没有修改正式 Schema、提示词、校验器或 V2 答案。

1. `requires_melody_present` 的 Schema 允许 `false`，本地 `validate_intent` 只接受 `true`／`null`。后续可考虑让 Schema 只接受这两个值，但须先确认当前端点能否执行相应布尔／空值枚举；本地硬校验应继续保留。
2. `trajectory` 的对象分支只要求 `type`，因此 Schema 可接受没有路径的 `{"type":"from_to"}`。本地要求至少有 `valence` 或 `arousal` 路径、起终点不同，且终点与目标值相同。后续可把“至少一条路径”表达进**新版本** Schema，跨字段一致性仍需本地校验。
3. Schema 允许空 `evidence` 字符串，也不表达“活跃字段必须有证据、无效字段证据必须为 `null`、证据须逐字出现原句”的跨字段规则。本地已经严格检查。后续可在新版本增加可执行的非空约束；逐字核查继续留给本地程序。
4. `constraints[]` 的 `evidence` 在 Schema 中可为空串或任意字符串，本地要求非空且逐字存在于原句。后续可收紧非空条件；逐字核查仍由本地完成。
5. 顶层及各对象的 `additionalProperties:false` 与本地拒绝额外键**一致**。`target_*` 的精确值／范围值域也与本地检查基本一致；不要把全部失败归因于 Schema 与校验器不一致。

即使未来 Schema 与本地规则更贴近，Schema 通过只代表结构合法，不能证明意图理解准确、歌曲可保证约束，或通过逐字证据检查。

## 独立中间探针的精确差异

脚本：`scripts/probe_intermediate_schema.py`。它沿用前一次**完整 Schema＋短提示词探针**的模型 `google/gemini-3.5-flash-lite`、同一条未进入开发／测试集的合成句、同一个 `data/FULL_SCHEMA_SHORT_PROMPT.txt`、同一 OpenRouter 端点和全部请求参数：`strict=true`、`require_parameters=true`、`reasoning.effort=minimal`、`max_tokens=2048`、默认 temperature。JSON Schema 的名称也保持 `music_intent`。**请求中只有 Schema 内容改变。**

保持不变：顶层对象的**九个属性名、九个 `required` 项及其顺序、`additionalProperties:false`**；`current_valence`、`current_arousal`、`target_melodic_surprise`、`requires_melody_present` 的属性 Schema 原样保留。

只改以下五个属性：

| 属性 | 正式 Schema | 中间探针 Schema |
| --- | --- | --- |
| `target_valence`、`target_arousal` | `anyOf`：可空精确整数或必填 `{relation,value}` 的范围对象 | 只取原 `anyOf` 的第一个分支：可空精确整数；**不能表示 V2 范围** |
| `trajectory` | `anyOf`：`none`／`single_target` 或含嵌套路径的 `from_to` 对象 | 只取字符串分支：`none`／`single_target`；**不能表示顺序路径** |
| `evidence` | 含七个必填可空子字段的对象 | 一个可空字符串，表示一段逐字证据；不再有嵌套键 |
| `constraints` | 数组，每项是含三个必填字段的对象 | 字符串数组；无条件时仍为 `[]` |

中间探针不含 `anyOf` 或嵌套对象，仍保留九个顶层必填字段及四个原样的可空标量字段。它是**诊断协议**，不能表达已批准的完整 V2 答案，也不能进入正式预检或正式评估。它只检查自己的简化结构以及标量证据是否逐字取自合成句，不调用正式 `validate_intent`，不写 `data/connection_preflight.json`。运行脚本若没有明确的 `--allow-paid-probe` 参数，会在读取本机配置或发网络请求前退出；本轮未使用该参数。

### 下一次仅一条调用能回答什么

- 若九字段扁平探针成功：说明这组模型、句子、短提示词和请求参数可以产出九个字段；“字段数量单独导致失败”的解释会变弱。联合分支、嵌套对象或它们的组合成为更值得单独测试的候选，**但不能断定是哪一个**，更不能认为正式意图卡已成功。
- 若仍缺字段或失败：说明删除联合分支和嵌套对象仍不足以解决这一现象；九字段数量、可空枚举、端点执行、提示词或其他因素仍待区分。**不能据此断定** Gemini 不支持 `anyOf` 或嵌套对象。
- 不论结果如何，一次结果只是单次对照；下一步若需再隔离特性，应先设计新的单变量探针并取得另一次明确授权。不得据此冻结测试集或运行 30 条评估。
