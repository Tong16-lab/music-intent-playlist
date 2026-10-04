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
    lines = ["# PE6201: Local Recommendation Demonstration of 35 Official Tracks", "",
             "The following are **fixed examples and preset intent cards**, which do not call the model and are not the 30 frozen test examples. "
             "Songs and order are calculated by the current deterministic song selector over the 35 official tracks; title links point only to the original Jamendo pages.", "",
             "Rules use `valence`, `arousal`, `melody_present`, and `melodic_surprise` verified by the author;"
             "MTG original mood/theme is only used as a candidate source, not as listening evaluation evidence.", ""]
    samples = fixed_samples()
    for name in ("explore", "calm", "path", "melody", "unsupported"):
        utterance, card = samples[name]
        result = recommend(card, catalog)
        lines.extend([f"## Example `{name}`", "", f"Synthetic input: {utterance}", "",
                      render_result(result, card, heading="Actual Recommendation", heading_level=3), ""])
    lines.extend(["## Evaluation Boundaries", "",
                  "These results only prove that the current rules and verified tags produce reproducible matches,"
                  "and do not prove higher song quality or that real listeners will like them. Enter subsequent author listening feedback in "
                  " [`data/RECOMMENDATION_LISTENING_REVIEW_TO_FILL.md`](../data/RECOMMENDATION_LISTENING_REVIEW_TO_FILL.md)."
                  "Current audio license is `not_checked`, demo only opens external page.", "",
                  "After freezing, the formal intent evaluation shall be based on [`formal_run_02/evaluation.md`](formal_run_02/evaluation.md);"
                  "This report did not rerun the intent model.", ""])
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
