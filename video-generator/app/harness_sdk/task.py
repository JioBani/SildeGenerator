from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Awaitable, Callable, Literal

ResourceKind = Literal["image", "voice", "ffmpeg", "cpu", "io"]


@dataclass(frozen=True)
class ResourceRequest:
    kind: ResourceKind | str = "cpu"
    slots: int = 1


@dataclass(frozen=True)
class RetryPolicy:
    attempts: int = 1
    backoff_seconds: float = 0.0


@dataclass(frozen=True)
class TaskResult:
    outputs: tuple[Path, ...] = ()
    metadata: dict[str, object] = field(default_factory=dict)


TaskCallable = Callable[[object], Awaitable[TaskResult | None]]


@dataclass(frozen=True)
class TaskNode:
    id: str
    run: TaskCallable
    dependencies: tuple[str, ...] = ()
    resource: ResourceRequest = ResourceRequest()
    expected_outputs: tuple[Path, ...] = ()
    fingerprint: str = ""
    retry: RetryPolicy = RetryPolicy()
