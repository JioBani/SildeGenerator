from __future__ import annotations

import asyncio
import hashlib
import json
import os
import random
import time
import uuid
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable

import asyncpg
import httpx
import redis.asyncio as redis

from .config import Settings


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def voice_settings_hash(narration: str, settings_snapshot: dict[str, Any]) -> str:
    payload = {"narration": narration, **settings_snapshot}
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


@dataclass(frozen=True)
class VoiceTaskSpec:
    voice_task_id: str
    job_id: str
    scene_id: str
    output_path: Path
    provider: str
    model: str
    settings_hash: str
    settings_snapshot: dict[str, Any]
    narration_sha256: str


@dataclass
class VoiceTaskHandle:
    spec: VoiceTaskSpec
    future: asyncio.Future[tuple[Path, dict[str, Any]]]


@dataclass
class _ReadyTask:
    handle: VoiceTaskHandle
    operation: Callable[[Path, int], Awaitable[dict[str, Any]]]
    submitted_at: datetime
    queued_at: datetime


class VoiceTaskBroker:
    """Durable fair voice scheduler with a Redis-wide concurrency lease."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.pool: asyncpg.Pool | None = None
        self.redis: redis.Redis | None = None
        self._condition = asyncio.Condition()
        self._queues: dict[str, deque[_ReadyTask]] = {}
        self._job_order: deque[str] = deque()
        self._workers: list[asyncio.Task[None]] = []
        self._closing = False
        self._cancelled_jobs: set[str] = set()

    async def start(self) -> None:
        if self._workers:
            return
        self.pool = await asyncpg.create_pool(self.settings.database_url, min_size=1, max_size=4)
        self.redis = redis.from_url(self.settings.redis_url, decode_responses=True)
        await self.redis.ping()
        for _ in range(60):
            if await self.pool.fetchval("SELECT to_regclass('public.voice_tasks')"):
                break
            await asyncio.sleep(1)
        else:
            raise RuntimeError("voice task tables are not ready")
        self._workers = [asyncio.create_task(self._worker(i + 1), name=f"voice-slot-{i + 1}") for i in range(self.settings.voice_task_concurrency)]

    async def close(self) -> None:
        self._closing = True
        async with self._condition:
            self._condition.notify_all()
        await asyncio.gather(*self._workers, return_exceptions=True)
        if self.redis:
            await self.redis.aclose()
        if self.pool:
            await self.pool.close()
        self._workers.clear()

    @staticmethod
    def task_id(job_id: str, scene_id: str) -> str:
        return str(uuid.uuid5(uuid.NAMESPACE_URL, f"slidegen:{job_id}:voice:{scene_id}"))

    async def submit(self, spec: VoiceTaskSpec, operation: Callable[[Path, int], Awaitable[dict[str, Any]]]) -> VoiceTaskHandle:
        if not self.pool or not self._workers:
            raise RuntimeError("voice task broker is not started")
        handle = VoiceTaskHandle(spec, asyncio.get_running_loop().create_future())
        submitted = _now()
        await self.pool.execute("""
          INSERT INTO voice_tasks(voice_task_id,job_id,scene_id,status,provider,model,settings_hash,settings_snapshot,narration_sha256,output_path,submitted_at)
          VALUES($1,$2,$3,'queued',$4,$5,$6,$7::jsonb,$8,$9,$10)
          ON CONFLICT(voice_task_id) DO UPDATE SET
            status=CASE WHEN voice_tasks.settings_hash=excluded.settings_hash AND voice_tasks.narration_sha256=excluded.narration_sha256 THEN voice_tasks.status ELSE 'queued' END,
            output_sha256=CASE WHEN voice_tasks.settings_hash=excluded.settings_hash AND voice_tasks.narration_sha256=excluded.narration_sha256 THEN voice_tasks.output_sha256 ELSE NULL END,
            output_bytes=CASE WHEN voice_tasks.settings_hash=excluded.settings_hash AND voice_tasks.narration_sha256=excluded.narration_sha256 THEN voice_tasks.output_bytes ELSE NULL END,
            qc=CASE WHEN voice_tasks.settings_hash=excluded.settings_hash AND voice_tasks.narration_sha256=excluded.narration_sha256 THEN voice_tasks.qc ELSE '{}'::jsonb END,
            updated_at=now(),settings_hash=excluded.settings_hash,settings_snapshot=excluded.settings_snapshot,narration_sha256=excluded.narration_sha256
        """, uuid.UUID(spec.voice_task_id), uuid.UUID(spec.job_id), spec.scene_id, spec.provider, spec.model,
            spec.settings_hash, json.dumps(spec.settings_snapshot, ensure_ascii=False), spec.narration_sha256, str(spec.output_path), submitted)
        cached = await self._completed(spec)
        if cached:
            handle.future.set_result(cached)
            return handle
        item = _ReadyTask(handle, operation, submitted, _now())
        async with self._condition:
            self._queues.setdefault(spec.job_id, deque()).append(item)
            if spec.job_id not in self._job_order:
                self._job_order.append(spec.job_id)
            self._condition.notify_all()
        return handle

    async def _completed(self, spec: VoiceTaskSpec) -> tuple[Path, dict[str, Any]] | None:
        assert self.pool
        row = await self.pool.fetchrow("SELECT status,output_path,output_sha256,qc,settings_hash FROM voice_tasks WHERE voice_task_id=$1", uuid.UUID(spec.voice_task_id))
        if not row or row["status"] != "succeeded" or row["settings_hash"] != spec.settings_hash:
            return None
        path = Path(row["output_path"])
        if path.is_file() and _sha256(path) == row["output_sha256"]:
            qc = row["qc"] if isinstance(row["qc"], dict) else json.loads(row["qc"] or "{}")
            return path, {"duration": float(qc.get("duration_seconds") or 0), "qc": qc, "reused": True}
        await self.pool.execute("UPDATE voice_tasks SET status='queued',error_code='ARTIFACT_INVALID',updated_at=now() WHERE voice_task_id=$1", uuid.UUID(spec.voice_task_id))
        return None

    async def _next(self) -> _ReadyTask | None:
        async with self._condition:
            while not self._closing:
                if self._job_order:
                    job_id = self._job_order.popleft()
                    queue = self._queues[job_id]
                    item = queue.popleft()
                    if queue:
                        self._job_order.append(job_id)
                    else:
                        self._queues.pop(job_id, None)
                    return item
                await self._condition.wait()
        return None

    async def _worker(self, slot: int) -> None:
        while True:
            item = await self._next()
            if item is None:
                return
            try:
                result = await self._execute(item, slot)
                if not item.handle.future.done():
                    item.handle.future.set_result(result)
            except Exception as error:
                if not item.handle.future.done():
                    item.handle.future.set_exception(error)

    async def _execute(self, item: _ReadyTask, slot: int) -> tuple[Path, dict[str, Any]]:
        spec = item.handle.spec
        for attempt in range(1, 4):
            token = f"{spec.voice_task_id}:{attempt}:{uuid.uuid4()}"
            await self._acquire(token)
            started_at = _now()
            started = time.perf_counter()
            attempt_dir = spec.output_path.parent / ".attempts" / spec.voice_task_id
            attempt_dir.mkdir(parents=True, exist_ok=True)
            temporary = attempt_dir / f"attempt-{attempt}.mp3"
            active = int(await self.redis.zcard("slidegen:voice:leases")) if self.redis else 0
            try:
                await self.pool.execute("UPDATE voice_tasks SET status='running',leased_at=now(),started_at=coalesce(started_at,now()),updated_at=now() WHERE voice_task_id=$1", uuid.UUID(spec.voice_task_id))
                result = await item.operation(temporary, attempt)
                if spec.job_id in self._cancelled_jobs:
                    raise asyncio.CancelledError()
                spec.output_path.parent.mkdir(parents=True, exist_ok=True)
                os.replace(temporary, spec.output_path)
                output_hash = _sha256(spec.output_path)
                elapsed = round((time.perf_counter() - started) * 1000)
                await self.pool.execute("""
                  INSERT INTO voice_task_attempts(voice_task_id,attempt,status,slot_id,active_calls,configured_concurrency,queue_wait_ms,provider_duration_ms,total_duration_ms,usage,submitted_at,queued_at,leased_at,provider_started_at,response_received_at,persisted_at)
                  VALUES($1,$2,'succeeded',$3,$4,$5,$6,$7,$7,$8::jsonb,$9,$10,now(),$11,now(),now())
                  ON CONFLICT(voice_task_id,attempt) DO NOTHING
                """, uuid.UUID(spec.voice_task_id), attempt, f"voice-slot-{slot}", active, self.settings.voice_task_concurrency,
                    max(0, round((started_at - item.queued_at).total_seconds() * 1000)), elapsed,
                    json.dumps(result, ensure_ascii=False), item.submitted_at, item.queued_at, started_at)
                qc = result.get("qc") or {}
                await self.pool.execute("""UPDATE voice_tasks SET status='succeeded',output_sha256=$2,output_bytes=$3,qc=$4::jsonb,finished_at=now(),updated_at=now(),error_code=null,error_message=null WHERE voice_task_id=$1""",
                    uuid.UUID(spec.voice_task_id), output_hash, spec.output_path.stat().st_size, json.dumps(qc, ensure_ascii=False))
                return spec.output_path, result
            except asyncio.CancelledError:
                temporary.unlink(missing_ok=True)
                await self.pool.execute("UPDATE voice_tasks SET status='cancelled',finished_at=now(),updated_at=now() WHERE voice_task_id=$1", uuid.UUID(spec.voice_task_id))
                raise
            except Exception as error:
                temporary.unlink(missing_ok=True)
                retryable, status, code = self._classify(error)
                backoff = 0 if not retryable or attempt == 3 else round((2 ** (attempt - 1) + random.random()) * 1000)
                await self.pool.execute("""
                  INSERT INTO voice_task_attempts(voice_task_id,attempt,status,slot_id,active_calls,configured_concurrency,queue_wait_ms,provider_duration_ms,total_duration_ms,http_status,error_code,error_message,retry_backoff_ms,potential_duplicate_cost,submitted_at,queued_at,leased_at,provider_started_at,response_received_at)
                  VALUES($1,$2,'failed',$3,$4,$5,$6,$7,$7,$8,$9,$10,$11,$12,$13,$14,now(),$15,now()) ON CONFLICT(voice_task_id,attempt) DO NOTHING
                """, uuid.UUID(spec.voice_task_id), attempt, f"voice-slot-{slot}", active, self.settings.voice_task_concurrency,
                    max(0, round((started_at - item.queued_at).total_seconds() * 1000)), round((time.perf_counter() - started) * 1000), status, code, str(error)[:1000], backoff,
                    isinstance(error, (httpx.TimeoutException, httpx.TransportError)), item.submitted_at, item.queued_at, started_at)
                if not retryable or attempt == 3:
                    await self.pool.execute("UPDATE voice_tasks SET status='failed',error_code=$2,error_message=$3,finished_at=now(),updated_at=now() WHERE voice_task_id=$1", uuid.UUID(spec.voice_task_id), code, str(error)[:1000])
                    raise
                await self.pool.execute("UPDATE voice_tasks SET status='retry_wait',updated_at=now() WHERE voice_task_id=$1", uuid.UUID(spec.voice_task_id))
                await asyncio.sleep(backoff / 1000)
            finally:
                await self._release(token)
        raise RuntimeError("voice task failed")

    @staticmethod
    def _classify(error: Exception) -> tuple[bool, int | None, str]:
        text = str(error)
        status = next((value for value in (429, 500, 502, 503, 504) if str(value) in text), None)
        if isinstance(error, (httpx.TimeoutException, httpx.TransportError)):
            return True, status, "NETWORK_ERROR"
        if status == 429:
            return True, status, "RATE_LIMITED"
        if status and status >= 500:
            return True, status, "PROVIDER_5XX"
        return False, status, "NON_RETRYABLE"

    async def _acquire(self, token: str) -> None:
        assert self.redis
        script = """redis.call('ZREMRANGEBYSCORE',KEYS[1],'-inf',ARGV[1]); if redis.call('ZCARD',KEYS[1]) < tonumber(ARGV[3]) then redis.call('ZADD',KEYS[1],ARGV[2],ARGV[4]); return 1 end; return 0"""
        while not self._closing:
            now = int(time.time() * 1000)
            if await self.redis.eval(script, 1, "slidegen:voice:leases", now, now + 300_000, self.settings.voice_task_concurrency, token):
                return
            await asyncio.sleep(0.1 + random.random() * 0.1)
        raise asyncio.CancelledError()

    async def _release(self, token: str) -> None:
        if self.redis:
            await self.redis.zrem("slidegen:voice:leases", token)

    async def cancel_job(self, job_id: str) -> None:
        self._cancelled_jobs.add(job_id)
        async with self._condition:
            queued = list(self._queues.pop(job_id, ()))
            self._job_order = deque(value for value in self._job_order if value != job_id)
        for item in queued:
            if not item.handle.future.done():
                item.handle.future.cancel()
        if self.pool:
            await self.pool.execute("UPDATE voice_tasks SET status='cancelled',finished_at=now(),updated_at=now() WHERE job_id=$1 AND status IN ('queued','running','retry_wait')", uuid.UUID(job_id))

    def resume_job(self, job_id: str) -> None:
        self._cancelled_jobs.discard(job_id)

    async def usage_events(self, job_id: str) -> list[dict[str, Any]]:
        assert self.pool
        rows = await self.pool.fetch("""SELECT task.scene_id,task.provider,task.model,attempt.attempt,attempt.status,attempt.usage,attempt.provider_started_at,attempt.response_received_at,attempt.provider_duration_ms FROM voice_tasks task JOIN voice_task_attempts attempt USING(voice_task_id) WHERE task.job_id=$1 ORDER BY attempt.provider_started_at""", uuid.UUID(job_id))
        events = []
        for row in rows:
            usage = row["usage"] if isinstance(row["usage"], dict) else json.loads(row["usage"] or "{}")
            events.append({
                "provider": row["provider"], "model": row["model"], "stage": "voice_generation", "scene_id": row["scene_id"],
                "request_id": usage.get("request_id"), "characters": usage.get("characters", 0),
                "audio_duration_ms": round(float(usage.get("duration", 0)) * 1000),
                "started_at": row["provider_started_at"].isoformat(),
                "finished_at": row["response_received_at"].isoformat() if row["response_received_at"] else None,
                "duration_ms": row["provider_duration_ms"], "raw_usage": {**usage, "attempt": row["attempt"], "status": row["status"]},
            })
        return events
