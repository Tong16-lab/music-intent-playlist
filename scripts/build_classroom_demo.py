"""Rebuild a reviewable classroom report using fixed offline example cards."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from music_intent.catalog import load_catalog  # noqa: E402
from music_intent.display import fixed_samples, recommend, render_result  # noqa: E402

REPORT = ROOT / "reports/CLASSROOM_RECOMMENDATION_DEMO.md"


def build() -> str:
    catalog = load_catalog(ROOT / "data/catalog.csv")
    lines = ["# PE6201：35 首正式曲库的本机推荐演示", "",
             "以下均为**固定的合成样例及预设意图卡**，不调用模型，也不是冻结的 30 条正式测试句。"
             "歌曲和顺序由当前确定性选歌器对 35 首正式曲库计算；标题链接仅指向 Jamendo 原始页面。", "",
             "规则使用作者已核对的 `valence`、`arousal`、`melody_present`、`melodic_surprise`；"
             "MTG 原有 mood/theme 仅用于候选来源，不当作听评证据。", ""]
    samples = fixed_samples()
    for name in ("explore", "calm", "path", "melody", "unsupported"):
        utterance, card = samples[name]
        result = recommend(card, catalog)
        lines.extend([f"## 样例 `{name}`", "", f"合成输入：{utterance}", "",
                      render_result(result, card, heading="实际推荐", heading_level=3), ""])
    lines.extend(["## 评价边界", "",
                  "这些结果只证明当前规则和已核对标签能产生可复现的匹配，"
                  "不证明歌曲质量更高，也不证明真实听众喜欢。作者后续试听反馈请填"
                  " [`data/RECOMMENDATION_LISTENING_REVIEW_TO_FILL.md`](../data/RECOMMENDATION_LISTENING_REVIEW_TO_FILL.md)。"
                  "当前音频许可为 `not_checked`，演示仅打开外部页面。", "",
                  "冻结后正式意图评估以 [`formal_run_02/evaluation.md`](formal_run_02/evaluation.md) 为准；"
                  "本报告没有重跑意图模型。", ""])
    return "\n".join(lines)


def main() -> int:
    expected = build()
    if REPORT.exists() and REPORT.read_text(encoding="utf-8") != expected:
        print("classroom_report=failed reason=existing_file_differs", file=sys.stderr)
        return 1
    if not REPORT.exists():
        REPORT.write_text(expected, encoding="utf-8")
    print("classroom_report=passed fixed_samples=5")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
