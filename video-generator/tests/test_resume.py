from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from app.config import settings
from app.main import render
from app.models import RenderRequest, RunnerResult


class RetryResumeTests(unittest.IsolatedAsyncioTestCase):
    async def test_retry_returns_completed_runner_result_without_regenerating(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            job_id = str(uuid4())
            root = Path(directory) / "jobs" / job_id
            video = root / "output" / "video.mp4"
            video.parent.mkdir(parents=True)
            video.write_bytes(b"completed-video")
            expected = RunnerResult(success=True, video_path=str(video))
            (root / "result.json").write_text(
                json.dumps(expected.model_dump()),
                encoding="utf-8",
            )
            request = RenderRequest(job_id=job_id, attempt=2, scenario="재시도 대본입니다.")

            with patch("app.main.settings", replace(settings, data_dir=Path(directory))):
                actual = await render(request)

            self.assertTrue(actual.success)
            self.assertEqual(actual.video_path, str(video))


if __name__ == "__main__":
    unittest.main()
