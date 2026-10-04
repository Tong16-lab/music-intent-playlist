# 用户表达与意图标注 V2：作者已核对，正式测试已完成

完整 42 行见 [user_intents_v2_review.tsv](user_intents_v2_review.tsv)。V2 标注已由作者逐项核对；这些表达是示例，不是从受访者收集的原话。V2 已迁移到现行 12／30 两份 CSV 和 30 条不支持条件 CSV；迁移记录及旧版原件见 [V2_MIGRATION.md](V2_MIGRATION.md) 与 `legacy_v1/`。测试集冻结记录见 [test_set_freeze.json](test_set_freeze.json)，完成的正式结果见 [第二次评估报告](../reports/formal_run_02/EVALUATION_EN.md)。

V2 保留了原先 42 句表达示例的字面文本、case ID、P01–P14 角色编号及 12/30 分组。角色编号不代表实际受访者。evidence_json 中的每个短语均须是对应原句中的连续原文；空白数值及 `requires_melody_present` 空白表示 null，trajectory=none 没有证据短语。unsupported_condition_phrases 是 JSON 数组，非空时才预期 cannot_guarantee_constraint。全表 review_status=approved、ambiguous=false，表示作者已核对 V2 标注；现行正式 CSV 已与 V2 逐项同步，并已按冻结记录用于正式评估。

## V2 判定口径

1. current_valence/current_arousal 只描述说话者**现在的状态**，不代替“歌单第一首要怎样”。事件或场景本身不自动生成当前情绪；例如“刚失恋”“下雨天”不足以单独证明一种具体心情。明确的“困得睁不开眼”“心慌得不行”可以分别支持当前低／高唤醒。
2. target_valence/target_arousal 描述用户想听到的**音乐表达**。安静、提神、欢快、忧伤等可映射到相应维度；“治愈”“陪着我”等期望体验不自动变成精确歌曲标签，且不得保证实际心理效果。有明确“别太……”式边界且不等于某个精确档位时，原字段可记 `{"relation":"at_most","value":2}` 或 `{"relation":"at_least","value":0}`，不另增顶层字段；现有曲目标签仍是三档整数。范围仅在证据和三档口径足以支持时使用，不能一律把“别太”当精确中档。
3. target_melodic_surprise 沿用本项目已讨论的操作口径：“不可预测／小惊喜／变化／新鲜感／别太复杂”等宽泛说法按旋律探索维度处理。这个映射只是在本项目中预先约定，不声称一般听众一定这样理解。“新鲜感”映射中档已由作者核对。
   明确要求歌曲有可辨旋律时，另填 `requires_melody_present=true`，并在 evidence_json 中记录原句证据；未表达则留空（null）。它不是第七个核心意图指标，不从旋律意外感偏好自动推断。选歌时只将 `melody_present=yes` 视为满足；`no` 和 `unknown` 均不满足。该标签仅表示有可追踪的旋律，不保证每个人都能跟着哼。
4. trajectory 仅在明确要求**音乐顺序**从一种表达过渡到另一种时记为结构化对象，例如 `{"type":"from_to","arousal":{"from":3,"to":1}}`；末端数值须等于同维度 target 字段的精确值。选歌按三首位置形成 3→2→1 的目标序列；没有合格歌曲可填某位置时说明无法完整满足，不用未知标签冒充满足。用户只想自己慢慢平静／好起来，不等于要求第一首音乐高唤醒或后续歌曲改变。至少有一个明确的音乐情绪／唤醒目标、但未规定音乐顺序时仍用 `single_target`；仅旋律偏好、仅不支持条件或只有软愿望时用 `none`。
5. 不支持条件只收录明确要求且现有歌曲字段不能可靠保证的**歌曲属性**，包括有无人声、歌词语言、流派、速度、音量、口水歌／土嗨歌等。正向要求（“电子乐”）同样可能不支持；“陪着我”“治愈”这类软愿望不直接变成硬约束。可由 valence/arousal/旋律标签解释的词不得重复列入不支持条件。
6. `test_024` 的“别太悲”和 `test_029` 的“不想听太欢快”保留作者已确认的中性近似（其中 `test_029` 还依赖“安安静静待一会儿”的上下文），不把这些原话单独等同于“只要中性”。作者另确认 `dev_005` 在本项目按 `valence≥0` 操作：允许 0、1，排除 -1；这可能比“别太苦情”的日常含义更严格，报告时应说明是粗粒度操作口径。

## 作者于 2026-10-02 核定的测试句

- test_010：“先听点难过的”表示此刻想听这类歌；“哭一哭，然后慢慢好起来”描述人的状态变化，**不是**三首歌的编排指令。记 target_valence=-1、trajectory=single_target，不需要首曲专属字段，也不凭此指定后续歌曲情绪。
- test_017：“吵吵闹闹”指高能量，不指音量大；target_arousal=3。
- test_025：“软软的”描述用户当前状态，而非首曲目标；current_arousal=1、target_arousal=3，trajectory=single_target。不能凭“从……慢慢……”在此句强行推断首曲音乐要求。
- test_029：结合“想安安静静待一会儿”，本项目接受 target_valence=0、target_arousal=1 作为操作性近似；这不表示“不要太欢快”单独严格等于中性。
- test_026：作者确认加入 `requires_melody_present=true`，证据为“能跟着哼的调调”；“没人唱的”仍列为不能保证的人声条件。两项要求独立判断，不因可辨旋律标签而声称歌曲无人声。
- test_019：作者核定的是**歌曲**从高活跃度 3 逐渐走向低活跃度 1，起点与终点均写在原 `trajectory` 字段；target_arousal=1 是终点，不写到 current_arousal。
- test_024：“别太闹”指音乐活跃度上限 2，而非音量或精确目标 2；只允许已知活跃度为 1／2 的歌满足此项。`target_valence=0` 仍是作者确认的中性近似。

以上句子的**语义判断**已由作者核定，表中这些行标为 ambiguous=false。整份 V2 已获作者核对并迁移为现行正式测试答案，随后完成冻结与评估。

## 同类案例复核与剩余判断

- dev_011：与 test_019 同型，使用 `trajectory={"type":"from_to","arousal":{"from":3,"to":1}}`。作者已确认“猛的”对应歌曲活跃度 3，故本句标为 ambiguous=false。
- dev_005：与 test_024 一样属于**边界表达**，但维度是情绪下限。作者确认 `target_valence={"relation":"at_least","value":0}`，活跃度仍为精确 2；本句标为 ambiguous=false。
- test_029：表面也是“不要太……”的边界表达，但作者明确同意结合上下文把它近似为中性、低活跃，故保留 `target_valence=0`、`target_arousal=1`，不改成单纯上限。test_024 的 `target_valence=0` 也保留作者核定的近似。
- dev_002、test_003、test_021 的“别太吵”仍按音量要求处理；test_017 的“吵吵闹闹”已核定为高能量。不能因为 test_024 的“别太闹”可映射活跃度，就把所有“吵／闹”统一改成活跃度。
- dev_001、test_004、test_011 的“别太花哨／复杂／绕”和 test_014 的“别忽然来个大变化”已有作者确认的低旋律意外感口径，保留精确 1；test_012 的“慢悠悠”涉及速度，不能按低活跃度重标。它们不是本次可直接转成情绪或活跃度范围的案例。
- dev_007、test_001、test_010、test_025 说的是**人的变化**，不改成歌曲 `from_to`。test_027 的“每首不一样”包含跨歌曲多样性要求；现有逐首高旋律意外感标签不能保证曲目彼此不同，选歌端若未做去重／多样性检查须单独说明这一局限。

42 条 V2 标注的 ambiguous 均为 false，review_status 均为 approved；现行正式测试 CSV 与 V2 一致。运行时 schema、提示词、校验器和选歌规则支持结构化路径、范围值与 `requires_melody_present`，并有离线测试；`≤2` 不会当成 `=2`。冻结记录和已完成的评估结果分别保存在上述文件中。

## 与现有代码的关系

现行正式 CSV 由 `scripts/sync_v2_answers.py` 从本 TSV 转换；`scripts/review_test_answers.py` 会核对它们与 V2 的逐项一致性。`scripts/export_test_sets.py` 是**历史旧版导出器**，不可用于重建 V2 答案。`scripts/freeze_test_set.py verify` 可核对已保存的冻结时间及 V2 源文件、30 条测试答案、30 条不支持条件答案各自的 SHA-256。第二次正式评估在冻结后运行，其结果与首次网络失败的运行分开保存。
