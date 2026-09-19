from __future__ import annotations

from pathlib import Path


def require_outputs(paths: tuple[Path, ...]) -> None:
    missing = [str(path) for path in paths if not path.is_file() or path.stat().st_size <= 0]
    if missing:
        raise ValueError(f"harness task outputs are missing: {', '.join(missing)}")
