"""Fully offline transport exception fixtures; no requests or frozen data changes."""

from __future__ import annotations

import contextlib
import errno
import io
import socket
import ssl
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "prototypes"), str(ROOT / "scripts")]

import check_transport_once as connection  # noqa: E402
import evaluate_compact_dev as candidate  # noqa: E402
from music_intent.openrouter_client import OpenRouterFailure, classify_transport_error  # noqa: E402


class _TimedOutBody:
    status = 200
    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self, *_):
        raise TimeoutError("secret response data")


class TransportDiagnosticsTests(unittest.TestCase):
    def test_fixed_categories_never_contain_exception_text(self):
        cases = [
            (URLError(socket.gaierror(socket.EAI_NONAME, "secret-host")), "network_dns"),
            (URLError(ssl.SSLError("secret certificate")), "network_tls"),
            (URLError(ssl.SSLCertVerificationError("secret certificate")), "network_tls_certificate"),
            (URLError(TimeoutError("secret timeout")), "network_timeout_open_or_headers"),
            (URLError(PermissionError(errno.EPERM, "secret permission")), "network_local_permission"),
            (URLError(ConnectionRefusedError(errno.ECONNREFUSED, "secret refused")), "network_connection_refused"),
            (URLError(ConnectionResetError(errno.ECONNRESET, "secret reset")), "network_connection_reset"),
            (URLError(OSError(errno.ENETUNREACH, "secret network")), "network_unreachable"),
            (URLError(OSError("Tunnel connection failed: 407 secret proxy")), "network_proxy_tunnel"),
            (URLError("secret unknown reason"), "network_other"),
        ]
        for error, expected in cases:
            with self.subTest(expected=expected):
                label = classify_transport_error(error, "open_or_headers")
                self.assertEqual(label, expected)
                self.assertNotIn("secret", label)

    def test_http_status_and_phase_are_safe_without_error_body(self):
        error = HTTPError("https://invalid.example", 429, "secret response", None, None)
        with patch.object(candidate, "urlopen", side_effect=error):
            with self.assertRaises(OpenRouterFailure) as raised:
                candidate.call_candidate_once("synthetic fixture", "secret-key", "fixture-model", "system", {})
        failure = raised.exception
        self.assertEqual(failure.category, "rate_or_quota_limit")
        self.assertEqual(failure.http_status, 429)
        self.assertEqual(failure.transport_phase, "http_status")
        self.assertNotIn("secret", str(failure))
        proxy = HTTPError("https://invalid.example", 407, "secret proxy", None, None)
        with patch.object(candidate, "urlopen", side_effect=proxy):
            with self.assertRaises(OpenRouterFailure) as raised:
                candidate.call_candidate_once("synthetic fixture", "secret-key", "fixture-model", "system", {})
        self.assertEqual(raised.exception.category, "proxy_authentication")
        self.assertEqual(raised.exception.http_status, 407)

    def test_open_and_body_timeouts_remain_distinct(self):
        with patch.object(candidate, "urlopen", side_effect=URLError(TimeoutError("secret"))):
            with self.assertRaises(OpenRouterFailure) as raised:
                candidate.call_candidate_once("synthetic fixture", "secret-key", "fixture-model", "system", {})
        self.assertEqual(raised.exception.category, "network_timeout_open_or_headers")
        self.assertEqual(raised.exception.transport_phase, "open_or_headers")
        self.assertIsNone(raised.exception.http_status)
        with patch.object(candidate, "urlopen", return_value=_TimedOutBody()):
            with self.assertRaises(OpenRouterFailure) as raised:
                candidate.call_candidate_once("synthetic fixture", "secret-key", "fixture-model", "system", {})
        self.assertEqual(raised.exception.category, "network_timeout_body")
        self.assertEqual(raised.exception.transport_phase, "response_body")
        self.assertEqual(raised.exception.http_status, 200)

    def test_connection_script_needs_future_flag_and_never_writes_formal_artifacts(self):
        output = io.StringIO()
        with (patch.object(connection, "get_settings", side_effect=AssertionError("read settings")),
              patch.object(candidate, "call_candidate_once", side_effect=AssertionError("network called")),
              contextlib.redirect_stdout(output)):
            self.assertEqual(connection.main([]), 2)
        self.assertIn("authorization_required", output.getvalue())

    def test_future_connection_failure_only_prints_safe_metadata(self):
        failure = OpenRouterFailure("network_dns", model=connection.MODEL,
                                    transport_phase="open_or_headers")
        output = io.StringIO()
        with (patch.object(connection, "ROOT", ROOT),
              patch.object(connection, "get_settings", return_value=("secret-key", connection.MODEL)),
              patch.object(candidate, "call_candidate_once", side_effect=failure),
              contextlib.redirect_stdout(output)):
            self.assertEqual(connection.run(), 1)
        report = output.getvalue()
        self.assertIn("category=network_dns", report)
        self.assertIn("http_status=unavailable", report)
        self.assertIn("processable_response=false", report)
        self.assertIn("finish_reason=unavailable", report)
        self.assertIn("provider_reached=unknown", report)
        self.assertNotIn("secret-key", report)
        self.assertNotIn(connection.SYNTHETIC_SENTENCE, report)


if __name__ == "__main__":
    unittest.main()
