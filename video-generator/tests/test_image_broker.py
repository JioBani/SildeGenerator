from __future__ import annotations

import asyncio
import hashlib
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
        for task in self.broker._workers:
            task.cancel()
        await asyncio.wait_for(asyncio.gather(*self.broker._workers, return_exceptions=True), 3)
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

    async def test_global_active_calls_never_exceed_twelve_across_jobs(self) -> None:
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

        self.assertLessEqual(self.maximum_active, 12)
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

    async def test_worker_termination_resolves_handle_and_releases_lease(self) -> None:
        entered = asyncio.Event()

        async def operation(path, references, attempt):
            entered.set()
            await asyncio.Event().wait()

        handle = await self.broker.submit(self.spec(str(uuid4()), "interrupted"), operation)
        await asyncio.wait_for(entered.wait(), 1)
        for worker in self.broker._workers:
            worker.cancel()
        with self.assertRaisesRegex(RuntimeError, "worker stopped"):
            await asyncio.wait_for(handle.future, 3)
        await asyncio.gather(*self.broker._workers, return_exceptions=True)
        self.assertEqual(self.active, 0)
        self.broker._mark_task_failed.assert_awaited_once()
        self.assertFalse(handle.spec.output_path.exists())

    async def test_close_resolves_running_and_dependency_waiters(self) -> None:
        self.broker.pool = AsyncMock()
        entered = asyncio.Event()

        async def operation(path, references, attempt):
            entered.set()
            await asyncio.Event().wait()

        first = await self.broker.submit(self.spec(str(uuid4()), "first"), operation)
        second = await self.broker.submit(self.spec(str(uuid4()), "second"), operation, [first])
        await asyncio.wait_for(entered.wait(), 1)
        await asyncio.wait_for(self.broker.close(), 3)
        results = await asyncio.gather(first.future, second.future, return_exceptions=True)
        self.assertTrue(all(isinstance(result, RuntimeError) for result in results))
        self.assertEqual(self.active, 0)
        with self.assertRaises(RuntimeError):
            await self.broker.submit(self.spec(str(uuid4()), "late"), operation)

    async def test_replacement_slot_runs_new_task_without_retrying_interrupted_call(self) -> None:
        for task in self.broker._workers:
            task.cancel()
        await asyncio.gather(*self.broker._workers, return_exceptions=True)
        self.broker._workers = [self.broker._spawn_worker(1)]
        entered = asyncio.Event()
        calls = []

        async def stuck(path, references, attempt):
            calls.append(attempt)
            entered.set()
            await asyncio.Event().wait()

        handle = await self.broker.submit(self.spec(str(uuid4()), "stuck"), stuck)
        await asyncio.wait_for(entered.wait(), 1)
        worker = self.broker._workers[0]
        worker.cancel()
        with self.assertRaises(RuntimeError):
            await asyncio.wait_for(handle.future, 3)
        await asyncio.gather(worker, return_exceptions=True)
        await asyncio.sleep(0)

        async def healthy(path, references, attempt):
            Image.new("RGB", (16, 16), "blue").save(path)

        next_handle = await self.broker.submit(self.spec(str(uuid4()), "new"), healthy)
        result = await asyncio.wait_for(next_handle.future, 2)
        self.assertTrue(result.exists())
        self.assertEqual(calls, [1])

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


class ImageBrokerCacheTests(unittest.IsolatedAsyncioTestCase):
    async def test_provider_change_invalidates_completed_mock_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scene.png"
            Image.new("RGB", (16, 16), "blue").save(path)
            spec = ImageTaskSpec(
                image_task_id=str(uuid4()), job_id=str(uuid4()), task_type="scene",
                scene_id="scene-001", output_path=path,
                prompt_path=Path(directory) / "prompt.txt", prompt_sha256="a" * 64,
                provider="oauth", model="gpt-image-2.5-sunburst",
                quality="medium", size="1536x1024", image_style="cute_character",
            )
            row = {
                "status": "succeeded", "output_path": str(path),
                "output_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "provider": "mock", "model": "mock-image-v1",
                "quality": spec.quality, "size": spec.size,
                "input_fidelity": None, "prompt_sha256": spec.prompt_sha256,
                "prompt_bundle": {}, "reference_asset_ids": [],
                "dependency_task_ids": [], "parent_keycut_task_id": None,
                "reference_kinds": [], "image_style": spec.image_style,
                "reference_files": [],
            }
            broker = ImageTaskBroker(settings)
            broker.pool = AsyncMock()
            broker.pool.fetchrow = AsyncMock(return_value=row)

            cached = await broker._completed_artifact(spec, [])

            self.assertIsNone(cached)
            broker.pool.execute.assert_awaited_once()
            self.assertIn("CACHE_SIGNATURE_CHANGED", broker.pool.execute.await_args.args[0])


if __name__ == "__main__":
    unittest.main()
