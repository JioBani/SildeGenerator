from __future__ import annotations

import asyncio
import hashlib
import json
import random
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Awaitable

import asyncpg
import redis.asyncio as redis

from .config import Settings
from .engine.artifact_store import ArtifactStore
from .engine.graph_executor import GraphExecutor, LocalLeaseProvider
from .engine.harness_loader import LoadedHarness
from .engine.process_runner import ProcessRunner
from .harness_sdk.context import HarnessContext
from .models import Scene


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _input_hash(scenes: list[Scene], settings: Settings, harness: LoadedHarness) -> str:
    value = {
        "scenes": [{"id": scene.id, "image": _file_hash(Path(scene.image_path)), "audio": _file_hash(Path(scene.audio_path)), "duration": scene.duration_seconds} for scene in scenes],
        "fps": settings.fps, "width": settings.width, "height": settings.height,
        "crossfade": settings.crossfade_seconds, "preset": settings.ffmpeg_preset,
        "harness": harness.snapshot.as_dict(), "harness_config": harness.config,
    }
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


class ProgressiveRenderer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.redis = redis.from_url(settings.redis_url, decode_responses=True)
        self.pool: asyncpg.Pool | None = None
        self.process = ProcessRunner()

    async def start(self) -> None:
        self.pool = await asyncpg.create_pool(self.settings.database_url, min_size=1, max_size=2)
        await self.redis.ping()

    async def close(self) -> None:
        await self.redis.aclose()
        if self.pool:
            await self.pool.close()

    async def render_ready_segments(self, job_id: str, scenes: list[Scene], prepared: list[Awaitable[None]], work: Path, harness: LoadedHarness) -> list[Path]:
        assert self.pool
        render_dir = work / "render-segments"
        render_dir.mkdir(parents=True, exist_ok=True)
        segments: list[Path] = []
        for start in range(0, len(scenes), self.settings.render_segment_scenes):
            chunk = scenes[start:start + self.settings.render_segment_scenes]
            await asyncio.gather(*prepared[start:start + self.settings.render_segment_scenes])
            index = len(segments) + 1
            ready_at = _now()
            input_hash = _input_hash(chunk, self.settings, harness)
            output = render_dir / f"segment-{index:03d}.mp4"
            metadata = output.with_suffix(".json")
            reused = False
            if output.is_file() and metadata.is_file():
                try:
                    reused = json.loads(metadata.read_text(encoding="utf-8")).get("input_hash") == input_hash and output.stat().st_size > 0
                except (OSError, ValueError):
                    reused = False
            await self.pool.execute("""INSERT INTO render_segments(job_id,segment_index,first_scene_id,last_scene_id,input_hash,output_path,status,ready_at,settings)
              VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9::jsonb) ON CONFLICT(job_id,segment_index) DO UPDATE SET input_hash=excluded.input_hash,output_path=excluded.output_path,status=excluded.status,ready_at=excluded.ready_at,settings=excluded.settings""",
              uuid.UUID(job_id), index, chunk[0].id, chunk[-1].id, input_hash, str(output), "succeeded" if reused else "ready", ready_at,
              json.dumps({"fps": self.settings.fps, "crossfade_seconds": self.settings.crossfade_seconds, "scene_count": len(chunk), "harness": harness.snapshot.as_dict()}))
            if not reused:
                token = f"{job_id}:{index}:{uuid.uuid4()}"
                await self._acquire(token)
                started = time.perf_counter()
                try:
                    await self.pool.execute("UPDATE render_segments SET status='running',started_at=now() WHERE job_id=$1 AND segment_index=$2", uuid.UUID(job_id), index)
                    subtitles = render_dir / f"segment-{index:03d}.ass"
                    context = HarnessContext(
                        job_id=job_id, workspace=work, settings=self.settings, process=self.process,
                        artifacts=ArtifactStore(work), leases=LocalLeaseProvider({"ffmpeg": 1, "cpu": 2, "io": 4}),
                        metadata={"operation": "render_segment", "task_prefix": f"segment-{index:03d}", "scenes": chunk, "subtitles": subtitles, "output": output, "config": harness.config},
                    )
                    graph = await harness.instance.build_pipeline(context)
                    await GraphExecutor(harness.snapshot).execute(graph, context)
                    metadata.write_text(json.dumps({"input_hash": input_hash}, indent=2), encoding="utf-8")
                    await self.pool.execute("UPDATE render_segments SET status='succeeded',finished_at=now(),duration_ms=$3 WHERE job_id=$1 AND segment_index=$2", uuid.UUID(job_id), index, round((time.perf_counter() - started) * 1000))
                except Exception:
                    await self.pool.execute("UPDATE render_segments SET status='failed',finished_at=now(),duration_ms=$3 WHERE job_id=$1 AND segment_index=$2", uuid.UUID(job_id), index, round((time.perf_counter() - started) * 1000))
                    raise
                finally:
                    await self.redis.zrem("slidegen:ffmpeg:leases", token)
            segments.append(output)
        return segments

    async def _acquire(self, token: str) -> None:
        script = """redis.call('ZREMRANGEBYSCORE',KEYS[1],'-inf',ARGV[1]); if redis.call('ZCARD',KEYS[1]) < tonumber(ARGV[3]) then redis.call('ZADD',KEYS[1],ARGV[2],ARGV[4]); return 1 end; return 0"""
        while True:
            now = int(time.time() * 1000)
            if await self.redis.eval(script, 1, "slidegen:ffmpeg:leases", now, now + 900_000, self.settings.ffmpeg_task_concurrency, token):
                return
            await asyncio.sleep(0.1 + random.random() * 0.1)
