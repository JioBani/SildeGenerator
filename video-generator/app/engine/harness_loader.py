from __future__ import annotations

import hashlib
import importlib
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from app.harness_sdk.api import CreativeHarness, HarnessManifest, HarnessSnapshot
from app.harness_sdk.errors import ManifestValidationError

ENGINE_API_VERSION = "1.0"
ID_PATTERN = re.compile(r"^[a-z][a-z0-9-]{1,63}$")
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file() and "__pycache__" not in item.parts and not path_ignored(item)):
        digest.update(path.relative_to(root).as_posix().encode()); digest.update(b"\0"); digest.update(path.read_bytes()); digest.update(b"\0")
    return digest.hexdigest()


def path_ignored(path: Path) -> bool:
    return path.suffix in {".pyc", ".mp4", ".mp3", ".png"}


def _inside(root: Path, relative: str) -> Path:
    target = (root / relative).resolve()
    if target != root.resolve() and root.resolve() not in target.parents:
        raise ManifestValidationError(f"manifest path escapes package: {relative}")
    return target


@dataclass(frozen=True)
class LoadedHarness:
    instance: CreativeHarness
    manifest: HarnessManifest
    snapshot: HarnessSnapshot
    root: Path
    config: dict[str, object]


class HarnessRegistry:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self._cache: dict[tuple[str, str], LoadedHarness] = {}
        if self.root.is_dir():
            for package_root in sorted(self.root.glob("*/src")):
                if str(package_root) not in sys.path: sys.path.append(str(package_root))

    def ids(self) -> list[str]:
        if not self.root.is_dir(): return []
        return sorted(path.name for path in self.root.iterdir() if (path / "harness.yaml").is_file())

    def load(self, harness_id: str) -> LoadedHarness:
        root = _inside(self.root, harness_id)
        raw = json.loads((root / "harness.yaml").read_text(encoding="utf-8"))
        if raw.get("id") != harness_id or not ID_PATTERN.fullmatch(harness_id): raise ManifestValidationError("invalid harness id")
        if not VERSION_PATTERN.fullmatch(str(raw.get("version", ""))): raise ManifestValidationError("invalid semantic version")
        if str(raw.get("engine_api")) != ">=1.0,<2.0": raise ManifestValidationError(f"incompatible engine API: {raw.get('engine_api')}")
        python = raw.get("python") or {}; defaults = raw.get("defaults") or {}
        manifest = HarnessManifest(
            id=harness_id, version=str(raw["version"]), engine_api=str(raw["engine_api"]), entrypoint=str(raw["entrypoint"]),
            display_name=str(raw["display_name"]), description=str(raw["description"]), prompts_dir=str(raw["prompts_dir"]),
            config_dir=str(raw["config_dir"]), fixtures_dir=str(raw["fixtures_dir"]), package=str(python["package"]),
            lockfile=str(python["lockfile"]), default_config=str(defaults["config"]), public=bool(raw.get("public", False)),
        )
        for relative in (manifest.prompts_dir, manifest.config_dir, manifest.fixtures_dir, manifest.lockfile, manifest.default_config):
            if not _inside(root, relative).exists(): raise ManifestValidationError(f"missing manifest path: {relative}")
        manifest_hash = _hash_file(root / "harness.yaml"); source_hash = _tree_hash(root); config_path = _inside(root, manifest.default_config)
        snapshot = HarnessSnapshot(harness_id, manifest.version, manifest.display_name, manifest_hash, source_hash, _hash_file(config_path), os.getenv("RUNNER_SOURCE_REVISION", "working-tree"), os.getenv("RUNNER_IMAGE_DIGEST", "unavailable"))
        key = (manifest.id, snapshot.source_sha256)
        if key in self._cache: return self._cache[key]
        src = _inside(root, "src")
        if str(src) not in sys.path: sys.path.insert(0, str(src))
        module_name, class_name = manifest.entrypoint.split(":", 1)
        instance = getattr(importlib.import_module(module_name), class_name)()
        instance.manifest = manifest
        loaded = LoadedHarness(instance, manifest, snapshot, root, json.loads(config_path.read_text(encoding="utf-8")))
        self._cache[key] = loaded
        return loaded

    def list(self) -> list[dict[str, object]]:
        entries = []
        for harness_id in self.ids():
            try:
                loaded = self.load(harness_id)
                entries.append({**loaded.snapshot.as_dict(), "description": loaded.manifest.description, "public": loaded.manifest.public, "compatible": True})
            except Exception as error:
                entries.append({"id": harness_id, "compatible": False, "error": str(error)})
        return entries
