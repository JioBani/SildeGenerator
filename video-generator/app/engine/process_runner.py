from __future__ import annotations

import asyncio
import os
from pathlib import Path


class ProcessRunner:
    async def run(self, arguments: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None, timeout: float | None = None) -> None:
        if not arguments or any(not isinstance(argument, str) for argument in arguments):
            raise ValueError("process arguments must be a non-empty string array")
        allowed_env = {key: value for key, value in (env or {}).items() if key in {"PATH", "LANG", "LC_ALL", "FONTCONFIG_PATH"}}
        process = await asyncio.create_subprocess_exec(
            *arguments, cwd=str(cwd) if cwd else None, env={**os.environ, **allowed_env},
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        try:
            _, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        except (asyncio.CancelledError, TimeoutError):
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=5)
            except TimeoutError:
                process.kill(); await process.wait()
            raise
        if process.returncode:
            tail = stderr.decode("utf-8", errors="replace")[-2500:]
            raise RuntimeError(f"command failed ({arguments[0]}): {tail}")
