from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .artifacts import ArtifactStore
from .services import LeaseProvider, ProcessService


@dataclass(frozen=True)
class HarnessContext:
    job_id: str
    workspace: Path
    settings: Any
    process: ProcessService
    artifacts: ArtifactStore
    leases: LeaseProvider
    cancellation: Any = None
    job_input: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
