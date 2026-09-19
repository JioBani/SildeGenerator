from __future__ import annotations

import asyncio
import hashlib
import os
import random
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable

import asyncpg
import httpx
import redis.asyncio as redis
from PIL import Image

from .config import Settings


IMAGE_PRICE_SNAPSHOTS: dict[str, dict[str, Any]] = {
    "gpt-image-2": {"text_input_usd_per_token": 2.50 / 1_000_000, "text_cached_input_usd_per_token": 0.625 / 1_000_000, "image_input_usd_per_token": 4 / 1_000_000, "image_cached_input_usd_per_token": 1 / 1_000_000, "image_output_usd_per_token": 15 / 1_000_000},
    "gpt-image-2.5-sunburst": {"text_input_usd_per_token": 5 / 1_000_000, "text_cached_input_usd_per_token": 1.25 / 1_000_000, "image_input_usd_per_token": 8 / 1_000_000, "image_cached_input_usd_per_token": 2 / 1_000_000, "image_output_usd_per_token": 30 / 1_000_000},
    "gpt-image-2.5-flare": {"text_input_usd_per_token": 5 / 1_000_000, "text_cached_input_usd_per_token": 1.25 / 1_000_000, "image_input_usd_per_token": 8 / 1_000_000, "image_cached_input_usd_per_token": 2 / 1_000_000, "image_output_usd_per_token": 30 / 1_000_000},
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class ImageTaskSpec:
    image_task_id: str
    job_id: str
    task_type: str
    output_path: Path
    prompt_path: Path
    prompt_sha256: str
    provider: str
    model: str
    quality: str
    size: str
    input_fidelity: str | None = None
    scene_id: str | None = None
    asset_id: str | None = None
    reference_asset_ids: list[str] = field(default_factory=list)
    dependency_task_ids: list[str] = field(default_factory=list)
    prompt_bundle: dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    parent_keycut_task_id: str | None = None
    reference_kinds: list[str] = field(default_factory=list)
    image_style: str | None = None


@dataclass
class ImageTaskHandle:
    spec: ImageTaskSpec
    future: asyncio.Future[Path]


class ImageTaskCancelled(RuntimeError):
    pass


@dataclass
class _ReadyTask:
    handle: ImageTaskHandle
    operation: Callable[[Path, list[Path], int], Awaitable[dict[str, Any] | None]]
    references: list[Path]
    submitted_at: datetime
    dependency_ready_at: datetime
    queued_at: datetime


class ImageTaskBroker:
    """Durable, fair image task scheduler with a Redis-wide provider lease."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.pool: asyncpg.Pool | None = None
        self.redis: redis.Redis | None = None
        self._condition = asyncio.Condition()
        self._queues: dict[str, deque[_ReadyTask]] = {}
        self._job_order: deque[str] = deque()
        self._workers: list[asyncio.Task[None]] = []
        self._closing = False
        self._effective_concurrency = settings.image_task_concurrency
        self._healthy_attempts = 0
        self._cancelled_jobs: set[str] = set()

    async def start(self) -> None:
        if self._workers:
            return
        self.pool = await asyncpg.create_pool(self.settings.database_url, min_size=1, max_size=4)
        self.redis = redis.from_url(self.settings.redis_url, decode_responses=True)
        await self.redis.ping()
        for _ in range(60):
            if await self.pool.fetchval("SELECT to_regclass('public.image_tasks')"):
                break
            await asyncio.sleep(1)
        else:
            raise RuntimeError("image task tables are not ready")
        self._workers = [
            asyncio.create_task(self._worker(index + 1), name=f"image-slot-{index + 1}")
            for index in range(self.settings.image_task_concurrency)
        ]

    async def close(self) -> None:
        self._closing = True
        async with self._condition:
            self._condition.notify_all()
        if self._workers:
            await asyncio.gather(*self._workers, return_exceptions=True)
        if self.redis:
            await self.redis.aclose()
        if self.pool:
            await self.pool.close()
        self._workers.clear()

    @staticmethod
    def task_id(job_id: str, task_type: str, entity_id: str) -> str:
        return str(uuid.uuid5(uuid.NAMESPACE_URL, f"slidegen:{job_id}:{task_type}:{entity_id}"))

    async def submit(
        self,
        spec: ImageTaskSpec,
        operation: Callable[[Path, list[Path], int], Awaitable[dict[str, Any] | None]],
        dependencies: list[ImageTaskHandle] | None = None,
    ) -> ImageTaskHandle:
        if not self.pool or not self._workers:
            raise RuntimeError("image task broker is not started")
        loop = asyncio.get_running_loop()
        handle = ImageTaskHandle(spec, loop.create_future())
        submitted_at = _now()
        await self._persist_submission(spec, submitted_at)
        cached = await self._completed_artifact(spec)
        if cached:
            handle.future.set_result(cached)
            return handle
        asyncio.create_task(
            self._wait_dependencies(handle, operation, dependencies or [], submitted_at),
            name=f"image-dependencies-{spec.image_task_id}",
        )
        return handle

    async def cancel_job(self, job_id: str) -> None:
        """Cancel waiting work and discard results from provider calls already in flight."""
        self._cancelled_jobs.add(job_id)
        async with self._condition:
            queued = list(self._queues.pop(job_id, ()))
            self._job_order = deque(item for item in self._job_order if item != job_id)
            self._condition.notify_all()
        for item in queued:
            if not item.handle.future.done():
                item.handle.future.set_exception(ImageTaskCancelled("image task cancelled"))
        if self.pool:
            await self.pool.execute(
                "UPDATE image_tasks SET status='cancelled',finished_at=now(),updated_at=now() "
                "WHERE job_id=$1 AND status IN ('waiting_dependencies','queued','leased','running','retry_wait')",
                uuid.UUID(job_id),
            )

    def resume_job(self, job_id: str) -> None:
        self._cancelled_jobs.discard(job_id)

    async def _wait_dependencies(
        self,
        handle: ImageTaskHandle,
        operation: Callable[[Path, list[Path], int], Awaitable[dict[str, Any] | None]],
        dependencies: list[ImageTaskHandle],
        submitted_at: datetime,
    ) -> None:
        try:
            references = await asyncio.gather(*(dependency.future for dependency in dependencies))
            if handle.spec.job_id in self._cancelled_jobs:
                raise ImageTaskCancelled("image task cancelled")
            ready_at = _now()
            queued_at = _now()
            await self._set_ready(handle.spec, references, ready_at, queued_at)
            item = _ReadyTask(handle, operation, list(references), submitted_at, ready_at, queued_at)
            async with self._condition:
                queue = self._queues.setdefault(handle.spec.job_id, deque())
                queue.append(item)
                if handle.spec.job_id not in self._job_order:
                    self._job_order.append(handle.spec.job_id)
                self._condition.notify_all()
        except ImageTaskCancelled as error:
            await self._mark_cancelled(handle.spec)
            if not handle.future.done():
                handle.future.set_exception(error)
        except Exception as error:
            await self._fail_dependency(handle.spec, error)
            if not handle.future.done():
                if handle.spec.parent_keycut_task_id:
                    sequence = handle.spec.prompt_bundle.get("sequence_id", "해당 시퀀스")
                    handle.future.set_exception(RuntimeError(f"{sequence}의 기준 키컷 이미지를 만들지 못했습니다: {error}"))
                else:
                    handle.future.set_exception(RuntimeError(f"image dependency failed: {error}"))

    async def _next_ready(self, slot_index: int) -> _ReadyTask | None:
        async with self._condition:
            while not self._closing:
                if slot_index <= self._effective_concurrency and self._job_order:
                    job_id = self._job_order.popleft()
                    queue = self._queues[job_id]
                    best_index = max(range(len(queue)), key=lambda index: queue[index].handle.spec.priority)
                    item = queue[best_index]
                    del queue[best_index]
                    if queue:
                        self._job_order.append(job_id)
                    else:
                        self._queues.pop(job_id, None)
                    return item
                await self._condition.wait()
        return None

    async def _worker(self, slot_index: int) -> None:
        while True:
            item = await self._next_ready(slot_index)
            if item is None:
                return
            try:
                result = await self._execute(item, slot_index)
                if not item.handle.future.done():
                    item.handle.future.set_result(result)
            except Exception as error:
                if not item.handle.future.done():
                    item.handle.future.set_exception(error)

    async def _execute(self, item: _ReadyTask, slot_index: int) -> Path:
        spec = item.handle.spec
        last_error: Exception | None = None
        for attempt in range(1, 4):
            lease_token = f"{spec.image_task_id}:{attempt}:{uuid.uuid4()}"
            lease_started = _now()
            await self._acquire_global_lease(lease_token)
            started_at = _now()
            started = time.perf_counter()
            attempt_dir = spec.output_path.parent / ".attempts" / spec.image_task_id
            attempt_dir.mkdir(parents=True, exist_ok=True)
            temporary = attempt_dir / f"attempt-{attempt}.png"
            queue_depth = sum(len(queue) for queue in self._queues.values())
            active_calls = await self._active_leases()
            await self._mark_running(spec, attempt, slot_index, lease_started, started_at)
            try:
                usage = await item.operation(temporary, item.references, attempt) or {}
                response_at = _now()
                if spec.job_id in self._cancelled_jobs:
                    temporary.unlink(missing_ok=True)
                    raise ImageTaskCancelled("image task cancelled after provider completion")
                with Image.open(temporary) as image:
                    image.verify()
                with Image.open(temporary) as image:
                    width, height = image.size
                spec.output_path.parent.mkdir(parents=True, exist_ok=True)
                os.replace(temporary, spec.output_path)
                output_hash = _sha256(spec.output_path)
                persisted_at = _now()
                await self._mark_succeeded(
                    spec, attempt, slot_index, item, lease_started, started_at,
                    response_at, persisted_at, output_hash, width, height,
                    queue_depth, active_calls, usage,
                    round((time.perf_counter() - started) * 1000),
                )
                self._healthy_attempts += 1
                if self._healthy_attempts >= 8 and self._effective_concurrency < self.settings.image_task_concurrency:
                    self._effective_concurrency += 1
                    self._healthy_attempts = 0
                    async with self._condition:
                        self._condition.notify_all()
                return spec.output_path
            except ImageTaskCancelled:
                temporary.unlink(missing_ok=True)
                await self._mark_cancelled(spec)
                raise
            except Exception as error:
                last_error = error
                retryable, status, code = self._classify(error)
                if status == 429:
                    self._effective_concurrency = max(1, self._effective_concurrency // 2)
                    self._healthy_attempts = 0
                backoff_ms = 0 if not retryable or attempt == 3 else round((2 ** (attempt - 1) + random.random()) * 1000)
                await self._mark_attempt_failed(
                    spec, attempt, slot_index, item, lease_started, started_at,
                    queue_depth, active_calls, error, code, status, backoff_ms,
                    round((time.perf_counter() - started) * 1000),
                )
                temporary.unlink(missing_ok=True)
                if not retryable or attempt == 3:
                    await self._mark_task_failed(spec, code, error)
                    raise
                await asyncio.sleep(backoff_ms / 1000)
            finally:
                await self._release_global_lease(lease_token)
        raise last_error or RuntimeError("image task failed")

    def _classify(self, error: Exception) -> tuple[bool, int | None, str]:
        text = str(error)
        status = None
        for candidate in (429, 500, 502, 503, 504):
            if str(candidate) in text:
                status = candidate
                break
        if isinstance(error, (httpx.TimeoutException, httpx.TransportError)):
            return True, status, "NETWORK_ERROR"
        if status == 429:
            return True, status, "RATE_LIMITED"
        if status and status >= 500:
            return True, status, "PROVIDER_5XX"
        return False, status, "NON_RETRYABLE"

    async def _acquire_global_lease(self, token: str) -> None:
        assert self.redis
        script = """
        redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', ARGV[1])
        if redis.call('ZCARD', KEYS[1]) < tonumber(ARGV[3]) then
          redis.call('ZADD', KEYS[1], ARGV[2], ARGV[4]); return 1
        end
        return 0
        """
        while not self._closing:
            now_ms = int(time.time() * 1000)
            acquired = await self.redis.eval(
                script, 1, "slidegen:image:leases", now_ms,
                now_ms + 600_000, self.settings.image_task_concurrency, token,
            )
            if acquired:
                return
            await asyncio.sleep(0.1 + random.random() * 0.1)
        raise asyncio.CancelledError()

    async def _release_global_lease(self, token: str) -> None:
        if self.redis:
            await self.redis.zrem("slidegen:image:leases", token)

    async def _active_leases(self) -> int:
        return int(await self.redis.zcard("slidegen:image:leases")) if self.redis else 0

    async def usage_events(self, job_id: str) -> list[dict[str, Any]]:
        assert self.pool
        rows = await self.pool.fetch("""
          SELECT task.image_task_id::text,task.task_type,task.scene_id,task.asset_id,task.provider,task.model,
            task.quality,task.size,task.input_fidelity,task.reference_asset_ids,
            attempt.attempt,attempt.status,attempt.usage,attempt.provider_started_at,attempt.response_received_at,
            attempt.provider_duration_ms,attempt.error_code,attempt.potential_duplicate_cost
          FROM image_tasks task JOIN image_task_attempts attempt USING(image_task_id)
          WHERE task.job_id=$1 ORDER BY attempt.provider_started_at,task.image_task_id,attempt.attempt
        """, uuid.UUID(job_id))
        events: list[dict[str, Any]] = []
        for row in rows:
            raw = _decode_json(row["usage"])
            image_usage = raw.get("image") or {}
            provider = "mock" if row["provider"] == "mock" else "chatgpt_oauth_image"
            events.append({
                "provider": provider,
                "model": row["model"],
                "stage": "continuity_asset_generation" if row["task_type"] == "continuity_asset" else "keycut_generation" if row["task_type"] == "keycut" else "image_generation",
                "scene_id": row["scene_id"] or row["asset_id"],
                "request_id": raw.get("provider_request_id"),
                "input_tokens": int(image_usage.get("input_tokens") or image_usage.get("text_input_tokens") or 0),
                "cached_input_tokens": int(image_usage.get("cached_input_tokens") or (image_usage.get("input_tokens_details") or {}).get("cached_tokens") or 0),
                "output_tokens": int(image_usage.get("output_tokens") or image_usage.get("image_output_tokens") or 0),
                "images_generated": 1 if row["status"] == "succeeded" else 0,
                "started_at": row["provider_started_at"].isoformat(),
                "finished_at": row["response_received_at"].isoformat() if row["response_received_at"] else None,
                "duration_ms": row["provider_duration_ms"],
                "raw_usage": {
                    **raw,
                    "image_task_id": row["image_task_id"],
                    "task_type": row["task_type"],
                    "attempt": row["attempt"],
                    "status": row["status"],
                    "quality": row["quality"],
                    "size": row["size"],
                    "input_fidelity": row["input_fidelity"],
                    "reference_asset_ids": _decode_json(row["reference_asset_ids"], []),
                    "error_code": row["error_code"],
                    "potential_duplicate_cost": row["potential_duplicate_cost"],
                },
            })
        return events

    async def _persist_submission(self, spec: ImageTaskSpec, submitted_at: datetime) -> None:
        assert self.pool
        await self.pool.execute("""
          INSERT INTO image_tasks(image_task_id,job_id,task_type,scene_id,asset_id,status,provider,model,quality,size,input_fidelity,prompt_path,prompt_sha256,prompt_bundle,reference_asset_ids,dependency_task_ids,output_path,submitted_at,priority,parent_keycut_task_id,reference_kinds,image_style)
          VALUES($1,$2,$3,$4,$5,'waiting_dependencies',$6,$7,$8,$9,$10,$11,$12,$13::jsonb,$14::jsonb,$15::jsonb,$16,$17,$18,$19,$20::jsonb,$21)
          ON CONFLICT(image_task_id) DO UPDATE SET updated_at=now(),prompt_path=excluded.prompt_path,prompt_sha256=excluded.prompt_sha256,prompt_bundle=excluded.prompt_bundle
        """, uuid.UUID(spec.image_task_id), uuid.UUID(spec.job_id), spec.task_type, spec.scene_id, spec.asset_id,
            spec.provider, spec.model, spec.quality, spec.size, spec.input_fidelity,
            str(spec.prompt_path), spec.prompt_sha256, _json(spec.prompt_bundle),
            _json(spec.reference_asset_ids), _json(spec.dependency_task_ids), str(spec.output_path), submitted_at,
            spec.priority, uuid.UUID(spec.parent_keycut_task_id) if spec.parent_keycut_task_id else None,
            _json(spec.reference_kinds), spec.image_style)

    async def _completed_artifact(self, spec: ImageTaskSpec) -> Path | None:
        assert self.pool
        row = await self.pool.fetchrow("SELECT status,output_path,output_sha256 FROM image_tasks WHERE image_task_id=$1", uuid.UUID(spec.image_task_id))
        if not row or row["status"] != "succeeded" or not row["output_path"]:
            return None
        path = Path(row["output_path"])
        if path.is_file() and _sha256(path) == row["output_sha256"]:
            return path
        await self.pool.execute("UPDATE image_tasks SET status='waiting_dependencies',error_code='ARTIFACT_INVALID',updated_at=now() WHERE image_task_id=$1", uuid.UUID(spec.image_task_id))
        return None

    async def _set_ready(self, spec: ImageTaskSpec, references: list[Path], ready_at: datetime, queued_at: datetime) -> None:
        assert self.pool
        snapshot = [{
            "reference_id": reference_id, "asset_id": reference_id,
            "kind": spec.reference_kinds[index] if index < len(spec.reference_kinds) else "continuity_asset",
            "position": index + 1, "path": str(path), "sha256": _sha256(path), "bytes": path.stat().st_size,
        } for index, (reference_id, path) in enumerate(zip(spec.reference_asset_ids, references))]
        await self.pool.execute("UPDATE image_tasks SET status='queued',dependency_ready_at=$2,queued_at=$3,reference_files=$4::jsonb,updated_at=now() WHERE image_task_id=$1", uuid.UUID(spec.image_task_id), ready_at, queued_at, _json(snapshot))

    async def _mark_running(self, spec: ImageTaskSpec, attempt: int, slot: int, leased_at: datetime, started_at: datetime) -> None:
        assert self.pool
        await self.pool.execute("UPDATE image_tasks SET status='running',leased_at=$2,started_at=$3,updated_at=now() WHERE image_task_id=$1", uuid.UUID(spec.image_task_id), leased_at, started_at)

    async def _mark_succeeded(self, spec: ImageTaskSpec, attempt: int, slot: int, item: _ReadyTask, leased_at: datetime, started_at: datetime, response_at: datetime, persisted_at: datetime, output_hash: str, width: int, height: int, queue_depth: int, active_calls: int, usage: dict[str, Any], total_ms: int) -> None:
        assert self.pool
        await self.pool.execute("UPDATE image_tasks SET status='succeeded',output_sha256=$2,output_bytes=$3,width=$4,height=$5,finished_at=$6,updated_at=now(),error_code=NULL,error_message=NULL WHERE image_task_id=$1", uuid.UUID(spec.image_task_id), output_hash, spec.output_path.stat().st_size, width, height, persisted_at)
        await self._insert_attempt(spec, attempt, "succeeded", slot, item, leased_at, started_at, response_at, persisted_at, queue_depth, active_calls, total_ms, usage=usage)

    async def _mark_attempt_failed(self, spec: ImageTaskSpec, attempt: int, slot: int, item: _ReadyTask, leased_at: datetime, started_at: datetime, queue_depth: int, active_calls: int, error: Exception, code: str, status: int | None, backoff_ms: int, total_ms: int) -> None:
        await self._insert_attempt(spec, attempt, "failed", slot, item, leased_at, started_at, _now(), None, queue_depth, active_calls, total_ms, status=status, error=error, code=code, backoff_ms=backoff_ms)
        if backoff_ms and self.pool:
            await self.pool.execute("UPDATE image_tasks SET status='retry_wait',updated_at=now() WHERE image_task_id=$1", uuid.UUID(spec.image_task_id))

    async def _insert_attempt(self, spec: ImageTaskSpec, attempt: int, status_text: str, slot: int, item: _ReadyTask, leased_at: datetime, started_at: datetime, response_at: datetime, persisted_at: datetime | None, queue_depth: int, active_calls: int, total_ms: int, *, usage: dict[str, Any] | None = None, status: int | None = None, error: Exception | None = None, code: str | None = None, backoff_ms: int = 0) -> None:
        assert self.pool
        dependency_ms = max(0, round((item.dependency_ready_at - item.submitted_at).total_seconds() * 1000))
        queue_ms = max(0, round((leased_at - item.queued_at).total_seconds() * 1000))
        provider_ms = max(0, round((response_at - started_at).total_seconds() * 1000))
        await self.pool.execute("""
          INSERT INTO image_task_attempts(image_task_id,attempt,status,slot_id,active_calls,configured_concurrency,effective_concurrency,queue_depth,dependency_wait_ms,queue_wait_ms,provider_duration_ms,total_duration_ms,http_status,error_code,error_message,retry_backoff_ms,potential_duplicate_cost,usage,price_snapshot,reference_snapshot,submitted_at,dependency_ready_at,queued_at,leased_at,provider_started_at,response_received_at,persisted_at,finished_at)
          VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18::jsonb,$19::jsonb,(SELECT reference_files FROM image_tasks WHERE image_task_id=$1),$20,$21,$22,$23,$24,$25,$26,now())
          ON CONFLICT(image_task_id,attempt) DO UPDATE SET status=excluded.status,error_code=excluded.error_code,error_message=excluded.error_message,finished_at=excluded.finished_at
        """, uuid.UUID(spec.image_task_id), attempt, status_text, f"slot-{slot}", active_calls,
            self.settings.image_task_concurrency, self._effective_concurrency, queue_depth,
            dependency_ms, queue_ms, provider_ms, total_ms, status, code,
            str(error)[:1500] if error else None, backoff_ms,
            isinstance(error, (httpx.TimeoutException, httpx.TransportError)), _json(usage or {}),
            _json({"model": spec.model, **IMAGE_PRICE_SNAPSHOTS.get(spec.model, {})}),
            item.submitted_at, item.dependency_ready_at, item.queued_at, leased_at, started_at, response_at, persisted_at)

    async def _mark_task_failed(self, spec: ImageTaskSpec, code: str, error: Exception) -> None:
        assert self.pool
        await self.pool.execute("UPDATE image_tasks SET status='failed',finished_at=now(),error_code=$2,error_message=$3,updated_at=now() WHERE image_task_id=$1", uuid.UUID(spec.image_task_id), code, str(error)[:1500])

    async def _mark_cancelled(self, spec: ImageTaskSpec) -> None:
        if self.pool:
            await self.pool.execute("UPDATE image_tasks SET status='cancelled',finished_at=now(),updated_at=now() WHERE image_task_id=$1", uuid.UUID(spec.image_task_id))

    async def _fail_dependency(self, spec: ImageTaskSpec, error: Exception) -> None:
        if self.pool:
            await self.pool.execute("UPDATE image_tasks SET status='failed',finished_at=now(),error_code='DEPENDENCY_FAILED',error_message=$2,updated_at=now() WHERE image_task_id=$1", uuid.UUID(spec.image_task_id), str(error)[:1500])


def _json(value: Any) -> str:
    import json
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _decode_json(value: Any, fallback: Any = None) -> Any:
    import json
    if value is None:
        return {} if fallback is None else fallback
    if isinstance(value, str):
        return json.loads(value)
    return value
