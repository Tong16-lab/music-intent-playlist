# 极短结构化输出：离线 Schema 核查

本记录只根据仓库内的正式 `response_schema()` 和校验器分析。先前单句预检只留下 `missing_field:constraints` 等安全摘要；完整原始回复没有保存，因此不能断言它当时是 `{}`，也不能追溯其他缺失字段。本次没有修改正式 Schema、正式提示词、V2 标准答案或本地取值及逐字证据规则。

## 当前完整结构

- 顶层对象有 **9 个必填字段**，并禁止额外字段：六个核心意图字段、`requires_melody_present`、`evidence`、`constraints`。
- `evidence` 是嵌套对象，**7 个字段全部必填**，每个值可为字符串或 `null`。本地还要求非空意图的证据逐字出现在原句中。
- `target_valence`、`target_arousal` 和 `trajectory` 各用一次 `anyOf`。前两者接受可空精确整数或 `{relation, value}` 范围对象；`trajectory` 接受 `single_target`／`none` 字符串或 `from_to` 路径对象。路径可再嵌套 `valence`／`arousal` 的 `{from, to}`。
- `constraints` 是必填数组；每项是含 `evidence`、`classification`、`polarity` 三个必填字段的对象。没有不支持条件时仍须输出 `[]`。
- `current_valence`、`current_arousal`、`target_melodic_surprise`、`requires_melody_present` 及七个证据字段有可空值；target 范围的 `anyOf` 也包含 `null` 选项。压缩后的正式 Schema 约 **3192 UTF-8 字节**。

## 可供后续研究的简化点（本轮不实施）

1. 多处嵌套对象、三个 `anyOf` 和大量必填可空字段，可能增加提供方执行结构化输出的难度。仅靠一次极短回复不能证明这是根因。
2. `trajectory` 对象分支的 JSON Schema 只要求 `type`；本地校验还要求至少有一条路径、起终点不同，且终点匹配对应目标。Schema 与本地校验承担的约束层级不同，不能把 Schema 通过等同于正式意图卡通过。
3. `requires_melody_present` 的 Schema 允许 `false`，本地校验只接受 `true` 或 `null`；Schema 中的证据字符串也未禁止空串，本地校验会拒绝无效证据。这些差异需要单独审查，不能为通过预检而放宽本地规则。
4. 若未来考虑拆分解析步骤或调整 Schema，应先制定新的版本与回归测试，再评估对既有 V2 答案和评分的影响。本轮极简探针只用于区分“两个字段也失败”与“主要在完整结构下失败”，不会进入正式预检流程。

从现在起，缺字段错误会列出当前层级**全部已知必填字段名**；模型额外生成的未知字段名和值不会进入错误信息。模拟 `{}` 的离线测试覆盖全部九个顶层字段。
