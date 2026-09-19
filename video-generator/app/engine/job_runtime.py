from __future__ import annotations

from dataclasses import dataclass

from app.harness_sdk.api import HarnessSnapshot


@dataclass(frozen=True)
class JobRuntime:
    harness: HarnessSnapshot
    prompt_set_version: str | None = None
