"""Offline checks for the translated reading and demonstration branch.

These checks do not re-evaluate the model. Exact scored inputs are at commit
a39e3fc and are checked separately through the historical freeze verifier.
"""

from __future__ import annotations

import re
import csv
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import export_catalog
import sync_v2_answers
import verify_historical_freeze
from music_intent.catalog import load_catalog
from music_intent.display import fixed_samples, recommend


class EnglishSubmissionTests(unittest.TestCase):
    def test_tracked_text_has_no_chinese_characters(self):
        paths = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
        for relative in paths:
            if not relative or relative.endswith(".mp4"):
                continue
            try:
                content = (ROOT / relative).read_text(encoding="utf-8")
            except UnicodeError:
                continue
            with self.subTest(path=relative):
                self.assertIsNone(re.search(r"[\u3400-\u9fff]", content))

    def test_translated_tables_are_synchronized(self):
        self.assertEqual(sync_v2_answers.check(), {
            "synthetic_intents_dev.csv": 12,
            "synthetic_intents_test.csv": 30,
            "unsupported_conditions_test.csv": 30,
        })

    def test_reading_page_uses_the_same_request_wording_as_data(self):
        page = (ROOT / "data" / "USER_INTENT_ANNOTATION_V2.md").read_text(encoding="utf-8")
        with (ROOT / "data" / "user_intents_v2_review.tsv").open(encoding="utf-8", newline="") as handle:
            cases = list(csv.DictReader(handle, delimiter="\t"))
        self.assertEqual(len(cases), 42)
        for case in cases:
            with self.subTest(case_id=case["case_id"]):
                self.assertIn(f"### {case['case_id']} · {case['role_id']}", page)
                self.assertIn(f"> {case['utterance']}", page)

    def test_catalog_and_fixed_offline_demonstration(self):
        source = export_catalog.SOURCE_DOCUMENT.read_text(encoding="utf-8")
        self.assertEqual(export_catalog.render_csv(export_catalog.build_rows(source)),
                         export_catalog.CATALOG.read_text(encoding="utf-8"))
        catalog = load_catalog(export_catalog.CATALOG)
        self.assertEqual(len(catalog), 35)
        for name, (utterance, card) in fixed_samples().items():
            result = recommend(card, catalog)
            with self.subTest(sample=name):
                self.assertEqual(result["status"],
                                 "cannot_guarantee_constraint" if name == "unsupported" else "ready")
                self.assertEqual(len(result["tracks"]), 0 if name == "unsupported" else 3)

    def test_original_freeze_is_verifiable_without_rerunning(self):
        verify_historical_freeze.verify()


if __name__ == "__main__":
    unittest.main()
