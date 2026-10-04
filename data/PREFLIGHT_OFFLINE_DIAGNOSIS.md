# 单句预检离线排查（2026-10-03）

本记录只检查本地代码与此前已经报告的安全用量数据；本次没有读取 `.env` 中的密钥、发起 API 请求、冻结测试集或运行正式评估。下方 JSON 是手工构造的**离线估算样例**，不是模型回复，也不是测试集标准答案。

## 实际请求设置与本地处理

- `build_request` 发送一个 system 消息和一个 user 消息；模型由 `OPENROUTER_MODEL` 提供。此前两次预检报告的模型为 `google/gemini-3.1-flash-lite`。本次未读取 `.env`，因此不重新断言当前运行时环境变量的值。
- 当前代码发送 `max_tokens=2048`、`reasoning={"effort":"minimal"}`、`temperature=0`、`response_format.type=json_schema`、`json_schema.strict=true`、`provider.require_parameters=true` 和 `usage.include=true`。没有并存的第二种 token 上限或推理参数，也没有重复的 system 消息。
- JSON Schema 压缩后约 3192 UTF-8 字节：顶层 9 个必需字段、`evidence` 中 7 个必需字段，另有范围值、歌单路径和不支持条件结构。system 提示词约 734 字符。它们确有一定复杂度，但没有要求输出歌曲列表或长篇解释；提示词和 Schema 都要求全部字段，是相互对应的约束。
- 响应解析先检查 `finish_reason`，再解析内容及逐字证据。`length` 会直接归类为 `output_token_limit`，即使响应中已有部分内容也不会被当作有效意图卡。
- 用量解析原本已读取 `usage.completion_tokens_details.reasoning_tokens`，但预检终端未显示该值。本次改为在有值时显示，并兼容顶层 `usage.reasoning_tokens`；无值时显示 `unavailable`，不能写作 0。完成原因只保留允许的状态词，其他服务商文本归为 `other`，不会原样打印。

## 仅供长度估算的合法示例

对应现有非测试句单句预检输入，以下样例通过 `validate_intent` 的字段和逐字证据校验：

```json
{
  "current_valence": -1,
  "current_arousal": null,
  "target_valence": null,
  "target_arousal": 1,
  "target_melodic_surprise": null,
  "trajectory": "single_target",
  "requires_melody_present": true,
  "evidence": {
    "current_valence": "有点烦",
    "current_arousal": null,
    "target_valence": null,
    "target_arousal": "安静",
    "target_melodic_surprise": null,
    "trajectory": "想听一首安静、有清楚旋律的音乐",
    "requires_melody_present": "有清楚旋律"
  },
  "constraints": []
}
```

去掉展示用空格与换行后，它有 **394 个字符、444 个 UTF-8 字节**。按一般文本 token 化的粗略量级，可先把完成这种 JSON 的需求估为**约 100–250 token**；Gemini 实际 token 化可能不同，不能把此范围当成计费测量。即使写成带缩进的 JSON，也无需数千 token。此比较不能证明模型实际把输出额度花在推理、冗长内容或其他位置。

## 既有记录能确定什么

- 两次预检分别触及 1024 与 2048 的设置上限；此前安全报告分别记录 `completion_tokens=1008` 和 `2032`，第二次有 `prompt_tokens=409`。两次都因 `finish_reason=length` 归类为 `output_token_limit`，没有生成成功预检标记。
- 仓库没有保存这两次的原始响应或推理 token 明细；此前终端报告也没有显示 `reasoning_tokens`。从现有本地记录看，**两次的推理 token 数均无法追溯**。本次不访问服务商后台，无法确认其是否另有可查询记录。
- 当前静态请求没有发现明显参数冲突或意外重复消息。旧版 1024 设置不是当前代码的设置；不能仅凭现在的代码重建第一次调用的完整请求。

## 可能原因与下一次最小诊断

1. **确定的近因：完成 token 预算耗尽。** 两次均以 `length` 结束，且已报告的完成用量接近各自上限；短 JSON 本身不足以解释全部用量。
2. **待验证：推理 token 占用了完成预算。** 当前档位虽是 `minimal`，但旧报告没有细分用量。下一次应先看 `tokens_reasoning` 是否返回，以及它占完成用量多少。
3. **待验证：实际生成内容过长或结构化输出过程耗尽预算。** 现有代码不保存或打印原始响应，无法区分这类情况；下一次若推理用量很低而仍到上限，只能确认“非已报告的推理 token 消耗”，不能凭空判定具体文本内容。
4. **较弱的可能：Schema 与提示词复杂度导致生成困难。** 两者有多个嵌套结构，但合法样例很短，且没有发现重复消息。需要完成原因和用量明细来判断是否值得进一步简化措辞；不能为通过预检放宽字段或证据校验。
5. **目前无代码证据：参数冲突或配置错误。** 静态请求仅有一种模型、推理档位和 token 上限。下一次单句预检应核对安全报告中的实际响应模型；本次没有读取 `.env` 或覆盖配置。

下一次付费预检须由作者另行授权，只调用现有的一条合成句且不自动重试。核心问题是：服务商是否提供 `reasoning_tokens`，以及它能否解释接近上限的 `completion_tokens`。若没有该明细，继续加大上限不会成为有证据的修复方案。测试集目前未冻结，30 条正式评估尚未运行。
