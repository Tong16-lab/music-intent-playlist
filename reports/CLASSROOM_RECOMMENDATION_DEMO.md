# PE6201：35 首正式曲库的本机推荐演示

以下均为**固定的合成样例及预设意图卡**，不调用模型，也不是冻结的 30 条正式测试句。歌曲和顺序由当前确定性选歌器对 35 首正式曲库计算；标题链接仅指向 Jamendo 原始页面。

规则使用作者已核对的 `valence`、`arousal`、`melody_present`、`melodic_surprise`；MTG 原有 mood/theme 仅用于候选来源，不当作听评证据。

## 样例 `explore`

合成输入：随便来点音乐

### 实际推荐

状态：`ready`。
未指定可执行的歌曲目标；按已核对标签组合探索。

| 顺序 | 歌曲（Jamendo 原始页面） | 艺术家 | 已核对标签 | 依据 |
| ---: | --- | --- | --- | --- |
| 1 | [Give Me A Hand](https://www.jamendo.com/track/111374) | Traffic In My Head | valence=-1；arousal=1；melody_present=yes；melodic_surprise=1 | 已核对标签；探索选择 |
| 2 | [Binz Flow](https://www.jamendo.com/track/114199) | Pedro Collares | valence=0；arousal=1；melody_present=yes；melodic_surprise=2 | 已核对标签；探索选择 |
| 3 | [Robot_Star](https://www.jamendo.com/track/287980) | Nationale2 | valence=0；arousal=3；melody_present=yes；melodic_surprise=2 | 已核对标签；探索选择 |

标签匹配与规则通过不代表真人喜欢这些歌；音频许可尚未核查，本页只提供外部链接。


## 样例 `calm`

合成输入：我想听安静舒缓的歌

### 实际推荐

状态：`ready`。
以下依据已核对的歌曲标签与明确的音乐目标匹配。

| 顺序 | 歌曲（Jamendo 原始页面） | 艺术家 | 已核对标签 | 依据 |
| ---: | --- | --- | --- | --- |
| 1 | [Give Me A Hand](https://www.jamendo.com/track/111374) | Traffic In My Head | valence=-1；arousal=1；melody_present=yes；melodic_surprise=1 | arousal=1 |
| 2 | [Binz Flow](https://www.jamendo.com/track/114199) | Pedro Collares | valence=0；arousal=1；melody_present=yes；melodic_surprise=2 | arousal=1 |
| 3 | [Simplicity](https://www.jamendo.com/track/579315) | Macroform | valence=0；arousal=1；melody_present=yes；melodic_surprise=1 | arousal=1 |

标签匹配与规则通过不代表真人喜欢这些歌；音频许可尚未核查，本页只提供外部链接。


## 样例 `path`

合成输入：先来有冲劲的歌，再逐渐安静下来

### 实际推荐

状态：`ready`。
以下依据已核对的歌曲标签与明确的音乐目标匹配。

| 顺序 | 歌曲（Jamendo 原始页面） | 艺术家 | 已核对标签 | 依据 |
| ---: | --- | --- | --- | --- |
| 1 | [Robot_Star](https://www.jamendo.com/track/287980) | Nationale2 | valence=0；arousal=3；melody_present=yes；melodic_surprise=2 | arousal=3；歌曲顺序路径第 1 首 |
| 2 | [How Things Change](https://www.jamendo.com/track/938333) | Jonathan Dimmel | valence=1；arousal=2；melody_present=yes；melodic_surprise=2 | arousal=2；歌曲顺序路径第 2 首 |
| 3 | [Give Me A Hand](https://www.jamendo.com/track/111374) | Traffic In My Head | valence=-1；arousal=1；melody_present=yes；melodic_surprise=1 | arousal=1；歌曲顺序路径第 3 首 |

标签匹配与规则通过不代表真人喜欢这些歌；音频许可尚未核查，本页只提供外部链接。


## 样例 `melody`

合成输入：想听旋律清楚、走向有惊喜的歌

### 实际推荐

状态：`ready`。
以下依据已核对的歌曲标签与明确的音乐目标匹配。

| 顺序 | 歌曲（Jamendo 原始页面） | 艺术家 | 已核对标签 | 依据 |
| ---: | --- | --- | --- | --- |
| 1 | [Itiro (Road and Rain)](https://www.jamendo.com/track/654634) | Alexandr Ossipov production music | valence=-1；arousal=1；melody_present=yes；melodic_surprise=3 | melodic_surprise=3；可辨旋律=yes |
| 2 | [Res Publica](https://www.jamendo.com/track/844698) | Sevenless | valence=0；arousal=3；melody_present=yes；melodic_surprise=3 | melodic_surprise=3；可辨旋律=yes |
| 3 | [Crash Of Night](https://www.jamendo.com/track/978031) | StatueOfDiveo | valence=1；arousal=3；melody_present=yes；melodic_surprise=3 | melodic_surprise=3；可辨旋律=yes |

试听提示（作者原有记录）：

- 第 1 首（track_0654634）：约1:36和2:16旋律音区及句法节奏均发生明显变化，后段较前文更难预料。
- 第 2 首（track_0844698）：约3:12与3:56主题音高重心和和声走向两次明显转换，后段较难由前文直接预料。
- 第 3 首（track_0978031）：约1:50与3:56主导音高重心和节奏型多次转折，变化幅度较大。

标签匹配与规则通过不代表真人喜欢这些歌；音频许可尚未核查，本页只提供外部链接。


## 样例 `unsupported`

合成输入：不要英文歌

### 实际推荐

状态：`cannot_guarantee_constraint`。
当前曲库标签无法可靠保证原句中的硬条件；未选歌。

标签匹配与规则通过不代表真人喜欢这些歌；音频许可尚未核查，本页只提供外部链接。


## 评价边界

这些结果只证明当前规则和已核对标签能产生可复现的匹配，不证明歌曲质量更高，也不证明真实听众喜欢。作者后续试听反馈请填 [`data/RECOMMENDATION_LISTENING_REVIEW_TO_FILL.md`](../data/RECOMMENDATION_LISTENING_REVIEW_TO_FILL.md)。当前音频许可为 `not_checked`，演示仅打开外部页面。

冻结后正式意图评估以 [`formal_run_02/evaluation.md`](formal_run_02/evaluation.md) 为准；本报告没有重跑意图模型。
