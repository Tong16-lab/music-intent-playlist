import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from freeze_test_set import TEST_FILES, freeze, verify_manifest
from review_test_answers import validate_all
from sync_v2_answers import expected_outputs, source_rows


class FreezeTests(unittest.TestCase):
    def test_v2_counts_roles_and_special_cases(self):
        source = source_rows()
        self.assertEqual((len(source), sum(r["split"] == "dev" for r in source),
                          sum(r["split"] == "test" for r in source)), (42, 12, 30))
        self.assertEqual(validate_all(approved=True)["test"], 30)
        rows = {r["case_id"]: r for r in expected_outputs()["unsupported_conditions_test.csv"][1]}
        self.assertEqual(json.loads(rows["test_022"]["unsupported_condition_phrases"]), [])
        self.assertEqual(json.loads(rows["test_024"]["unsupported_condition_phrases"]), ["viral pop song", "tu-hai song"])
        for name in ("synthetic_intents_dev.csv", "synthetic_intents_test.csv", "unsupported_conditions_test.csv"):
            self.assertTrue((ROOT / "data" / "legacy_v1" / name).exists())

    def test_no_early_freeze_without_author_confirmation(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            for name in (*TEST_FILES, "synthetic_intents_dev.csv"):
                shutil.copyfile(ROOT / "data" / name, folder / name)
            with patch("sys.stdin.isatty", return_value=False):
                with self.assertRaisesRegex(ValueError, "interactive_author_confirmation_required"):
                    freeze(folder)
            self.assertFalse((folder / "test_set_freeze.json").exists())

    def test_changed_file_fails_verification(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            for name in (*TEST_FILES, "synthetic_intents_dev.csv"):
                shutil.copyfile(ROOT / "data" / name, folder / name)
            manifest = {"schema_version": 2, "timezone": "Asia/Singapore",
                        "frozen_at": "2026-10-03T12:00:00+08:00",
                        "files": {name: hashlib.sha256((folder / name).read_bytes()).hexdigest() for name in TEST_FILES}}
            (folder / "test_set_freeze.json").write_text(json.dumps(manifest), encoding="utf-8")
            verify_manifest(folder)
            with (folder / TEST_FILES[1]).open("a", encoding="utf-8") as handle:
                handle.write("\n")
            with self.assertRaisesRegex(ValueError, "modified_after_freeze"):
                verify_manifest(folder)


if __name__ == "__main__":
    unittest.main()
