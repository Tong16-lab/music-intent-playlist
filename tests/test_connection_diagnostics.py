"""Offline checks for the synthetic preflight's safe console output."""

import contextlib
import importlib.util
import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("connection_test", ROOT / "scripts" / "connection_test.py")
connection_test = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(connection_test)


class ConnectionDiagnosticsTests(unittest.TestCase):
    def test_token_limit_reports_only_safe_metadata(self):
        fake_key = "sk-test-secret-never-print"
        error = connection_test.OpenRouterFailure(
            "output_token_limit",
            usage={"prompt_tokens": 409, "completion_tokens": 2048,
                   "total_tokens": 2457, "reasoning_tokens": 1800},
            model="google/gemini-3.5-flash-lite", finish_reason="length",
            content_shape={"content_empty": False, "content_chars": 88,
                           "repeated_suffix": True},
        )
        output = io.StringIO()
        with (patch.object(connection_test, "get_settings", return_value=(fake_key, error.model)),
              patch.object(connection_test, "parse_once", side_effect=error),
              patch.object(sys, "argv", ["connection_test.py"]),
              contextlib.redirect_stdout(output)):
            result = connection_test.main()
        report = output.getvalue()
        self.assertEqual(result, 1)
        self.assertIn("category=output_token_limit", report)
        self.assertIn("finish_reason=length", report)
        self.assertIn("tokens_reasoning=1800", report)
        self.assertIn("content_empty=false content_chars=88 repeated_suffix=true", report)
        self.assertNotIn(fake_key, report)
        self.assertNotIn(connection_test.SYNTHETIC_SENTENCE, report)

    def test_missing_reasoning_usage_is_not_reported_as_zero(self):
        error = connection_test.OpenRouterFailure("output_token_limit", finish_reason="length")
        output = io.StringIO()
        with (patch.object(connection_test, "get_settings", return_value=("sk-test", "test/model")),
              patch.object(connection_test, "parse_once", side_effect=error),
              patch.object(sys, "argv", ["connection_test.py"]),
              contextlib.redirect_stdout(output)):
            self.assertEqual(connection_test.main(), 1)
        self.assertIn("tokens_reasoning=unavailable", output.getvalue())


if __name__ == "__main__":
    unittest.main()
