"""Offline checks for the reviewed catalog and link-only recommendation layer."""

import csv
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import audit_formal_recommendations as audit_script
import build_classroom_demo
import demo_recommendations
import export_catalog
from music_intent.catalog import load_catalog
from music_intent.display import fixed_samples, recommend, render_result
from music_intent.recommender import select_tracks


def minimal_intent(**overrides):
    card = {"current_valence": None, "current_arousal": None,
            "target_valence": None, "target_arousal": None,
            "target_melodic_surprise": None, "requires_melody_present": None,
            "trajectory": "none", "evidence": {}, "constraints": []}
    card.update(overrides)
    return card


def fixture(track_id, artist, *, valence="0", arousal="1", melody="yes", surprise="2",
            identity="matched", verified="verified"):
    return {"track_id": track_id, "artist": artist, "valence": valence, "arousal": arousal,
            "melody_present": melody, "melodic_surprise": surprise,
            "link_identity_status": identity, "label_status": verified}


class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = export_catalog.SOURCE_DOCUMENT.read_text(encoding="utf-8")
        cls.catalog = load_catalog(export_catalog.CATALOG)

    def test_exact_export_and_status_separation(self):
        expected = export_catalog.render_csv(export_catalog.build_rows(self.document))
        self.assertEqual(export_catalog.CATALOG.read_text(encoding="utf-8"), expected)
        self.assertEqual(len(self.catalog), 35)
        self.assertEqual(len({row["track_id"] for row in self.catalog}), 35)
        self.assertEqual({row["label_status"] for row in self.catalog}, {"verified"})
        self.assertEqual({row["current_audio_license_status"] for row in self.catalog}, {"not_checked"})
        self.assertEqual({row["display_policy"] for row in self.catalog}, {"external_link_only"})
        self.assertEqual(sum(row["link_identity_status"] == "artist_variant_confirmed"
                             for row in self.catalog), 2)

    def test_source_label_identity_mismatch_rejected(self):
        changed = re.sub(r"(\| track_0287980 \|) Robot_Star(\s+\| Nationale2)",
                         r"\1 Wrong Title\2", self.document, count=1)
        self.assertNotEqual(changed, self.document)
        with self.assertRaisesRegex(ValueError, "catalog_source_label_identity_mismatch"):
            export_catalog.build_rows(changed)

    def test_id_mismatch_and_duplicate_rejected(self):
        changed = self.document.replace("| track_0287980 | [Robot_Star]",
                                        "| track_0287981 | [Robot_Star]", 1)
        self.assertNotEqual(changed, self.document)
        with self.assertRaises(ValueError):
            export_catalog.build_rows(changed)

    def test_loader_rejects_duplicate_or_unverified(self):
        rows = [dict(row) for row in self.catalog]
        rows[0]["track_id"] = rows[1]["track_id"]
        fields = list(rows[0])
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "catalog.csv"
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
            with self.assertRaisesRegex(ValueError, "catalog_count_or_duplicate_id"):
                load_catalog(path)
            rows[0]["track_id"] = self.catalog[0]["track_id"]
            rows[0]["label_status"] = "source_only"
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
            with self.assertRaisesRegex(ValueError, "catalog_invalid_status"):
                load_catalog(path)


class RecommendationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_catalog(export_catalog.CATALOG)

    def test_fixed_samples_are_valid_reproducible_and_linked(self):
        samples = fixed_samples()
        self.assertEqual(len(samples), 5)
        for name in ("explore", "calm", "path", "melody"):
            _, intent = samples[name]
            first = recommend(intent, self.catalog)
            self.assertEqual(first, recommend(intent, self.catalog))
            self.assertEqual((first["status"], len(first["tracks"])), ("ready", 3))
            self.assertEqual(len({row["track_id"] for row in first["tracks"]}), 3)
            self.assertEqual(len({row["artist"] for row in first["tracks"]}), 3)
            output = render_result(first, intent)
            self.assertIn("https://www.jamendo.com/track/", output)
            self.assertNotIn("许可已核实", output)
        self.assertEqual(recommend(samples["unsupported"][1], self.catalog)["status"],
                         "cannot_guarantee_constraint")

    def test_path_is_three_step_and_current_state_does_not_set_target(self):
        _, card = fixed_samples()["path"]
        self.assertEqual([row["arousal"] for row in recommend(card, self.catalog)["tracks"]],
                         ["3", "2", "1"])
        current_only = minimal_intent(current_arousal=3)
        self.assertEqual(select_tracks(current_only, self.catalog),
                         select_tracks(minimal_intent(), self.catalog))

    def test_english_display_preserves_selection_and_explains_refusal(self):
        samples = fixed_samples()
        _, path_card = samples["path"]
        path_result = recommend(path_card, self.catalog)
        english = render_result(path_result, path_card, language="en")
        self.assertIn("song-path position 1", english)
        self.assertIn("arousal=3", english)
        self.assertEqual([item["track_id"] for item in path_result["tracks"]],
                         [item["track_id"] for item in recommend(path_card, self.catalog)["tracks"]])
        _, unsupported_card = samples["unsupported"]
        refused = render_result(recommend(unsupported_card, self.catalog),
                                unsupported_card, language="en")
        self.assertIn("cannot reliably guarantee", refused)
        self.assertNotIn("| 1 |", refused)

    def test_unknown_melody_and_ranges(self):
        tracks = [fixture("a", "A", valence="0", arousal="1"),
                  fixture("b", "B", valence="1", arousal="2"),
                  fixture("c", "C", valence="unknown", arousal="1"),
                  fixture("d", "D", valence="0", arousal="unknown"),
                  fixture("e", "E", valence="0", arousal="2", melody="unknown", surprise="unknown")]
        card = minimal_intent(target_valence={"relation": "at_least", "value": 0},
                              target_arousal={"relation": "at_most", "value": 2},
                              requires_melody_present=True)
        result = select_tracks(card, tracks)
        self.assertEqual(result["status"], "insufficient_catalog")
        self.assertEqual({row["track_id"] for row in result["tracks"]}, {"a", "b"})

    def test_source_identity_filter_and_shortage(self):
        tracks = [fixture("a", "A"), fixture("b", "B", identity="review_needed"),
                  fixture("c", "C", verified="source_only")]
        self.assertEqual(select_tracks(minimal_intent(), tracks)["status"], "insufficient_catalog")
        self.assertEqual(len(select_tracks(minimal_intent(), tracks)["tracks"]), 1)
        self.assertEqual(select_tracks(minimal_intent(), tracks[1:])["status"], "catalog_not_ready")
        confirmed = [fixture("a", "A", identity="artist_variant_confirmed"),
                     fixture("b", "B", identity="minor_spelling_variant"), fixture("c", "C")]
        self.assertEqual(select_tracks(minimal_intent(), confirmed)["status"], "ready")

    def test_duplicate_track_and_artist_tie_break(self):
        tracks = [fixture("a", "Same"), fixture("a", "Same"),
                  fixture("b", "Same"), fixture("c", "Other"), fixture("d", "Third")]
        result = select_tracks(minimal_intent(), tracks)
        self.assertEqual(result["status"], "ready")
        self.assertEqual([row["track_id"] for row in result["tracks"]], ["a", "c", "d"])

    def test_exploration_label_diversity_breaks_only_ties(self):
        tracks = [fixture("a", "A", valence="0"), fixture("b", "B", valence="0"),
                  fixture("c", "C", valence="1")]
        result = select_tracks(minimal_intent(), tracks)
        self.assertEqual([row["track_id"] for row in result["tracks"]], ["a", "c", "b"])

    def test_unsupported_is_not_filled(self):
        card = minimal_intent(constraints=[{"evidence": "不要英文歌",
                                             "classification": "unsupported_constraint",
                                             "polarity": "exclude"}])
        self.assertEqual(select_tracks(card, self.catalog),
                         {"status": "cannot_guarantee_constraint", "tracks": []})

    def test_live_demo_never_calls_without_explicit_paid_flag(self):
        with patch.object(demo_recommendations, "call_candidate_once",
                          side_effect=AssertionError("API called")):
            with self.assertRaisesRegex(ValueError, "live_mode_requires_allow_paid"):
                demo_recommendations.live_intent("合成输入", False)

    def test_classroom_report_uses_fixed_cards(self):
        report = build_classroom_demo.build()
        self.assertEqual(report.count("状态：`ready`"), 4)
        self.assertIn("状态：`cannot_guarantee_constraint`", report)
        self.assertIn("不调用模型", report)

    def test_private_formal_audit_is_offline_and_complete(self):
        result = audit_script.audit()
        self.assertEqual(sum(result["counts"].values()), 30)
        self.assertEqual(result["input_cases"], 30)


if __name__ == "__main__":
    unittest.main()
