from __future__ import annotations

import hashlib
import json
import os
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class Tracker:
    def __init__(self, job_root: Path, attempt: int = 1) -> None:
        self.job_root = job_root
        self.attempt = attempt
        self.stages: list[dict[str, Any]] = []
        self.usage: list[dict[str, Any]] = []
        self.assets: list[dict[str, Any]] = []

    @contextmanager
    def stage(self, name: str, scene_id: str | None = None, **metadata: Any) -> Iterator[None]:
        started_at = utc_now()
        started = time.perf_counter()
        record: dict[str, Any] = {
            "stage": name,
            "scene_id": scene_id,
            "attempt": self.attempt,
            "status": "running",
            "started_at": started_at,
            "metadata": metadata,
        }
        try:
            yield
            record["status"] = "completed"
        except Exception as error:
            record["status"] = "failed"
            record["metadata"] = {**metadata, "error": str(error)[:1000]}
            raise
        finally:
            record["finished_at"] = utc_now()
            record["duration_ms"] = round((time.perf_counter() - started) * 1000)
            self.stages.append(record)

    def add_usage(self, **event: Any) -> None:
        self.usage.append(event)

    def add_asset(
        self,
        path: Path,
        asset_type: str,
        scene_id: str | None = None,
        duration_ms: int | None = None,
        width: int | None = None,
        height: int | None = None,
        **metadata: Any,
    ) -> None:
        self.assets.append({
            "scene_id": scene_id,
            "asset_type": asset_type,
            "relative_path": path.relative_to(self.job_root).as_posix(),
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
            "duration_ms": duration_ms,
            "width": width,
            "height": height,
            "metadata": metadata,
        })


def atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, path)
