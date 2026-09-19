from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ArtifactStore:
    workspace: Path

    def resolve(self, relative: str) -> Path:
        target = (self.workspace / relative).resolve()
        if target != self.workspace.resolve() and self.workspace.resolve() not in target.parents:
            raise ValueError("artifact path escapes the job workspace")
        return target

    def commit(self, temporary: Path, relative: str) -> Path:
        target = self.resolve(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        os.replace(temporary, target)
        return target
