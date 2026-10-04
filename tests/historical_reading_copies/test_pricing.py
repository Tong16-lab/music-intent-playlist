"""Offline checks that cost estimates use the response model's own rate."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from music_intent.pricing import estimate_standard_cost_usd  # noqa: E402
from connection_test import estimate_cost  # noqa: E402
from evaluate import cost  # noqa: E402


class PricingTests(unittest.TestCase):
    def test_new_model_rate_is_distinct_from_old_model(self):
        usage = {"prompt_tokens": 409, "completion_tokens": 2032}
        old = estimate_standard_cost_usd("google/gemini-3.1-flash-lite", usage)
        new = estimate_standard_cost_usd("google/gemini-3.5-flash-lite", usage)
        self.assertAlmostEqual(old, 0.00315025)
        self.assertAlmostEqual(new, 0.0052027)
        self.assertEqual(estimate_cost("google/gemini-3.5-flash-lite", usage),
                         "USD 0.005203 (standard list-rate estimate)")
        self.assertEqual(cost(usage, "google/gemini-3.5-flash-lite"), new)

    def test_unknown_model_or_usage_cannot_inherit_old_rate(self):
        usage = {"prompt_tokens": 409, "completion_tokens": 2032}
        self.assertIsNone(estimate_standard_cost_usd("unverified/model", usage))
        self.assertEqual(estimate_cost("unverified/model", usage), "unavailable")
        self.assertIsNone(cost(usage, "unverified/model"))
        self.assertIsNone(estimate_standard_cost_usd("google/gemini-3.5-flash-lite", {}))


if __name__ == "__main__":
    unittest.main()
