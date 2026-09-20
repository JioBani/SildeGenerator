from __future__ import annotations

import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock
from uuid import uuid4

import httpx
from PIL import Image

from app.config import settings
from app.image_broker import ImageTaskBroker, ImageTaskSpec


class ImageBrokerSchedulingTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.broker = ImageTaskBroker(settings)
        self.broker.pool = object()  # type: ignore[assignment]
        self.broker._persist_submission = AsyncMock()
        self.broker._completed_artifact = AsyncMock(return_value=None)
        self.broker._set_ready = AsyncMock()
        self.broker._mark_running = AsyncMock()
        self.broker._mark_succeeded = AsyncMock()
        self.broker._mark_attempt_failed = AsyncMock()
        self.broker._mark_task_failed = AsyncMock()
        self.broker._mark_cancelled = AsyncMock()
        self.broker._fail_dependency = AsyncMock()
        self.active = 0
        self.maximum_active = 0

        async def acquire(_: str) -> None:
            self.active += 1
            self.maximum_active = max(self.maximum_active, self.active)

        async def release(_: str) -> None:
            self.active -= 1

        self.broker._acquire_global_lease = acquire  # type: ignore[method-assign]
        self.broker._release_global_lease = release  # type: ignore[method-assign]
        self.broker._active_leases = AsyncMock(side_effect=lambda: self.active)
        self.broker._workers = [
            asyncio.create_task(self.broker._worker(index + 1))
            for index in range(settings.image_task_concurrency)
        ]
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    async def asyncTearDown(self) -> None:
        self.broker._closing = True
        async with self.broker._condition:
            self.broker._condition.notify_all()
        await asyncio.gather(*self.broker._workers)
        self.temp.cleanup()

    def spec(self, job_id: str, entity: str, dependencies: list[str] | None = None) -> ImageTaskSpec:
        return ImageTaskSpec(
            image_task_id=self.broker.task_id(job_id, "scene", entity),
            job_id=job_id,
            task_type="scene",
            scene_id=entity,
            output_path=self.root / job_id / f"{entity}.png",
            prompt_path=self.root / "prompt.txt",
            prompt_sha256="0" * 64,
            provider="mock",
            model="mock-image-v1",
            quality="medium",
            size="16x16",
            dependency_task_ids=dependencies or [],
        )

    async def test_global_active_calls_never_exceed_eight_across_jobs(self) -> None:
        async def operation(path: Path, references: list[Path], attempt: int):
            path.parent.mkdir(parents=True, exist_ok=True)
            await asyncio.sleep(0.03)
            Image.new("RGB", (16, 16), "blue").save(path)
            return {}

        handles = []
        for index in range(12):
            job_id = "00000000-0000-0000-0000-000000000001" if index % 2 == 0 else "00000000-0000-0000-0000-000000000002"
            handles.append(await self.broker.submit(self.spec(job_id, f"scene-{index + 1:03d}"), operation))

        await asyncio.gather(*(handle.future for handle in handles))

        self.assertLessEqual(self.maximum_active, 8)
        self.assertGreater(self.maximum_active, 1)

    async def test_dependent_scene_waits_while_independent_scene_runs(self) -> None:
        events: list[str] = []
        job_id = str(uuid4())

        async def asset_operation(path: Path, references: list[Path], attempt: int):
            events.append("asset-start")
            await asyncio.sleep(0.05)
            path.parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (16, 16), "red").save(path)
            events.append("asset-end")
            return {}

        async def independent_operation(path: Path, references: list[Path], attempt: int):
            events.append("independent-start")
            path.parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (16, 16), "green").save(path)
            return {}

        async def dependent_operation(path: Path, references: list[Path], attempt: int):
            events.append("dependent-start")
            self.assertEqual(len(references), 1)
            path.parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (16, 16), "blue").save(path)
            return {}

        asset_spec = self.spec(job_id, "scene-001")
        asset_handle = await self.broker.submit(asset_spec, asset_operation)
        independent = await self.broker.submit(self.spec(job_id, "scene-002"), independent_operation)
        dependent_spec = self.spec(job_id, "scene-003", [asset_spec.image_task_id])
        dependent = await self.broker.submit(dependent_spec, dependent_operation, [asset_handle])

        await asyncio.gather(asset_handle.future, independent.future, dependent.future)

        self.assertLess(events.index("independent-start"), events.index("asset-end"))
        self.assertGreater(events.index("dependent-start"), events.index("asset-end"))

    def test_retry_policy_distinguishes_transient_and_validation_errors(self) -> None:
        self.assertTrue(self.broker._classify(httpx.ReadTimeout("slow"))[0])
        self.assertTrue(self.broker._classify(RuntimeError("provider returned 429"))[0])
        self.assertFalse(self.broker._classify(ValueError("invalid dimensions"))[0])

    async def test_cancelled_running_task_discards_provider_result(self) -> None:
        job_id = str(uuid4())
        entered = asyncio.Event()
        release = asyncio.Event()

        async def operation(path: Path, references: list[Path], attempt: int):
            path.parent.mkdir(parents=True, exist_ok=True)
            entered.set()
            await release.wait()
            Image.new("RGB", (16, 16), "red").save(path)
            return {}

        handle = await self.broker.submit(self.spec(job_id, "scene-001"), operation)
        await entered.wait()
        self.broker._cancelled_jobs.add(job_id)
        release.set()

        with self.assertRaisesRegex(RuntimeError, "cancelled"):
            await handle.future
        self.assertFalse(handle.spec.output_path.exists())
        self.broker._mark_cancelled.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
