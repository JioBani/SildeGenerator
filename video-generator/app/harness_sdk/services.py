from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from pathlib import Path
from typing import Protocol


class ProcessService(Protocol):
    async def run(self, arguments: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None, timeout: float | None = None) -> None: ...


class LeaseProvider(Protocol):
    def request(self, kind: str, slots: int = 1) -> AbstractAsyncContextManager[None]: ...
