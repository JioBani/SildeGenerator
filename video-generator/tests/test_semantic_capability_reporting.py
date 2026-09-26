import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import httpx

from app.harness_sdk.semantic_beats import semantic_planning_extension
from app.semantic_planning import analyze_script
from app.tracking import Tracker
from test_semantic_planning import analysis_payload, contract, SCRIPT


class CapabilityReportingTests(unittest.IsolatedAsyncioTestCase):
    async def test_unsupported_requirement_stops_once_without_silent_substitute(self):
        payload = analysis_payload()
        payload["beats"][1]["grammar"] = "map_spatial"
        for opted_in in (False, True):
            capability = contract()
            capability["semantic_analysis"] = semantic_planning_extension(report_missing=opted_in)
            calls = []
            def respond(request):
                calls.append(json.loads(request.content))
                completed = {"type": "response.completed", "response": {"id": "offline-capability",
                    "usage": {}, "output": [{"content": [{"type": "output_text", "text": json.dumps(payload)}]}]}}
                return httpx.Response(200, text="event: response.completed\ndata: " + json.dumps(completed) + "\n\n")
            settings = SimpleNamespace(codex_model="offline", codex_reasoning_effort="low", codex_fast_mode=False,
                codex_read_timeout_seconds=10, codex_connect_timeout_seconds=2, subscription_base_url="http://offline.invalid")
            original = httpx.AsyncClient
            with tempfile.TemporaryDirectory() as folder:
                work = Path(folder)
                with patch("app.semantic_planning.httpx.AsyncClient", side_effect=lambda **kw: original(transport=httpx.MockTransport(respond), **kw)):
                    with self.assertRaisesRegex(RuntimeError, "grammar_not_supported"):
                        await analyze_script(SCRIPT, settings, Tracker(work), work, capability)
                self.assertEqual(1, len(calls))
                saved = json.loads((work / "semantic-analysis-0.json").read_text())
                self.assertEqual("map_spatial", saved["analysis"]["beats"][1]["grammar"])
                self.assertEqual("REVISE", saved["status"])
                prompt = calls[0]["input"][0]["content"][0]["text"]
                self.assertEqual(opted_in, "Choose the grammar REQUIRED" in prompt)
                self.assertEqual(not opted_in, "Use only the registered source IDs and actually supported grammars." in prompt)


if __name__ == "__main__":
    unittest.main()
