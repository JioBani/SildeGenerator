from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .context import HarnessContext
from .graph import PipelineGraph


@dataclass(frozen=True)
class HarnessManifest:
    id: str
    version: str
    engine_api: str
    entrypoint: str
    display_name: str
    description: str
    prompts_dir: str
    config_dir: str
    fixtures_dir: str
    package: str
    lockfile: str
    default_config: str
    public: bool = False


@dataclass(frozen=True)
class HarnessSnapshot:
    id: str
    version: str
    display_name: str
    manifest_sha256: str
    source_sha256: str
    config_sha256: str
    source_revision: str
    image_digest: str

    def as_dict(self) -> dict[str, str]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class HarnessValidation:
    valid: bool
    checks: tuple[str, ...] = ()
    message: str = ""


class CreativeHarness(Protocol):
    manifest: HarnessManifest

    async def build_pipeline(self, context: HarnessContext) -> PipelineGraph: ...

    async def validate_result(self, context: HarnessContext, result: dict[str, object]) -> HarnessValidation: ...
