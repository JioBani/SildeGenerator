import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.planning_stream_guard import PlanningStreamGuard, bounded_phase_schema
from app.codex_transcript import CodexTranscript
from app.tracking import atomic_json


class StreamGuardTests(unittest.TestCase):
    def test_split_escaped_quotes_do_not_bypass_string_limit(self):
        guard = PlanningStreamGuard(max_string_chars=32)
        text = json.dumps({"phase": 'say "hold" ' * 20})
        with self.assertRaisesRegex(RuntimeError, "single_string"):
            for char in text: guard.feed(char)

    def test_ordinary_repeated_keys_are_allowed(self):
        data = json.dumps([{"id": "same", "phase": "hold briefly"} for _ in range(200)])
        guard = PlanningStreamGuard()
        for start in range(0, len(data), 17): guard.feed(data[start:start+17])

    def test_runaway_single_string_is_stopped_without_salvaging(self):
        text = json.dumps({"phase": "Hold still. Read the result. End the scene. " * 200})
        guard = PlanningStreamGuard()
        with self.assertRaisesRegex(RuntimeError, "repeated_string_block"):
            for char in text: guard.feed(char)
        self.assertLess(guard.total, 1000)

    def test_total_bound_and_schema_does_not_mutate_legacy(self):
        guard = PlanningStreamGuard(max_chars=5)
        with self.assertRaisesRegex(RuntimeError, "total_characters"): guard.feed("123456")
        original = {"properties": {"phases": {"type": "array", "items": {"type": "string"}}}}
        result = bounded_phase_schema(original)
        self.assertNotIn("maxLength", original["properties"]["phases"]["items"])
        self.assertEqual(240, result["properties"]["phases"]["items"]["maxLength"])


class TranscriptResilienceTests(unittest.TestCase):
    def test_summary_is_throttled_and_terminal_state_flushed(self):
        with tempfile.TemporaryDirectory() as folder:
            transcript = CodexTranscript(Path(folder), 1, {}, model="test", effort="low", fast_mode=False)
            with patch("app.codex_transcript.atomic_json", wraps=atomic_json) as writer:
                for i in range(20):
                    transcript.record(None, "{}", {"type": "delta"})
                    transcript.append_output("x")
                self.assertLess(writer.call_count, 10)
                transcript.fail("expected stop")
            saved = json.loads(transcript.summary_path.read_text())
            self.assertEqual("failed", saved["status"])
            self.assertEqual(20, saved["event_count"])
            self.assertEqual("x"*20, transcript.output_path.read_text())

    def test_transient_lock_retries_but_persistent_failure_is_not_hidden(self):
        with tempfile.TemporaryDirectory() as folder:
            transcript = CodexTranscript(Path(folder), 1, {}, model="test", effort="low", fast_mode=False)
            with patch("app.codex_transcript.time.sleep"), patch("app.codex_transcript.atomic_json", side_effect=[PermissionError(), None]) as writer:
                transcript._write_summary(force=True)
                self.assertEqual(2, writer.call_count)
            with patch("app.codex_transcript.time.sleep"), patch("app.codex_transcript.atomic_json", side_effect=PermissionError()) as writer:
                with self.assertRaises(PermissionError): transcript._write_summary(force=True)
                self.assertEqual(3, writer.call_count)
