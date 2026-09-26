from __future__ import annotations

import asyncio
import hashlib
import sys
from types import SimpleNamespace
from pathlib import Path

import pytest

from app.engine.graph_executor import GraphExecutor, LocalLeaseProvider
from app.engine.harness_loader import HarnessRegistry
from app.engine.process_runner import ProcessRunner
from app.harness_sdk.artifacts import ArtifactStore
from app.harness_sdk.context import HarnessContext
from app.harness_sdk.errors import GraphValidationError
from app.harness_sdk.graph import PipelineGraph
from app.harness_sdk.task import ResourceRequest, TaskNode, TaskResult
from app.models import RenderRequest

ROOT = Path(__file__).resolve().parents[2]


def registry() -> HarnessRegistry:
    return HarnessRegistry(ROOT / "harnesses")


def test_discovers_versioned_harnesses_and_hashes_entire_packages():
    entries = registry().list()
    assert [entry["id"] for entry in entries if entry.get("public")] == ["astra-motion", "classic-slide", "experimental-cut-move"]
    assert any(entry['id']=='genre-slide' and not entry['public'] for entry in entries)
    assert all(entry["compatible"] for entry in entries)
    assert all(len(entry["manifest_sha256"]) == 64 and len(entry["source_sha256"]) == 64 for entry in entries)
    assert len({entry["source_sha256"] for entry in entries}) == len(entries)


def test_harness_source_hash_uses_portable_path_order(tmp_path):
    from app.engine.harness_loader import _tree_hash

    (tmp_path / "z.txt").write_bytes(b"z")
    (tmp_path / "A.txt").write_bytes(b"A")
    expected = hashlib.sha256()
    for name, content in (("A.txt", b"A"), ("z.txt", b"z")):
        expected.update(name.encode())
        expected.update(b"\0")
        expected.update(content)
        expected.update(b"\0")
    assert _tree_hash(tmp_path) == expected.hexdigest()


def test_render_request_accepts_registry_snapshot_metadata():
    entry = registry().list()[0]
    request = RenderRequest(job_id="00000000-0000-0000-0000-000000000001", scenario="A complete scene.", harness_snapshot=entry)
    assert request.harness_snapshot is not None
    assert request.harness_snapshot["public"] is True
    assert request.harness_snapshot["compatible"] is True
    assert request.duration_profile == "episode_60"


def test_experimental_effect_is_loaded_without_core_effect_allowlist():
    loaded = registry().load("experimental-cut-move")
    assert loaded.instance.transition == "slideleft"
    source = (loaded.root / "src/experimental_cut_move/plugin.py").read_text(encoding="utf-8")
    assert "app.engine" not in source


def test_genre_plugin_rejects_bad_delivery_timing():
    harness=registry().load('genre-slide')
    context=SimpleNamespace(settings=SimpleNamespace(width=1920,height=1080,fps=30))
    result={'video_codec':'h264','audio_codec':'aac','width':1920,'height':1080,'fps':30,'duration_seconds':20}
    assert asyncio.run(harness.instance.validate_result(context,result)).valid
    for override in ({'fps':24},{'duration_seconds':0},{'duration_seconds':61},{'duration_seconds':float('nan')}):
        assert not asyncio.run(harness.instance.validate_result(context,{**result,**override})).valid


def test_graph_executes_arbitrary_dependencies_concurrently(tmp_path):
    graph = PipelineGraph(); events: list[str] = []
    async def first(_): await asyncio.sleep(0.01); events.append("first"); return TaskResult()
    async def second(_): events.append("second"); return TaskResult()
    async def final(_): events.append("final"); return TaskResult()
    graph.add(TaskNode("first", first, resource=ResourceRequest("cpu")))
    graph.add(TaskNode("second", second, resource=ResourceRequest("io")))
    graph.add(TaskNode("final", final, dependencies=("first", "second")))
    loaded = registry().load("classic-slide")
    context = HarnessContext("job", tmp_path, object(), ProcessRunner(), ArtifactStore(tmp_path), LocalLeaseProvider())
    asyncio.run(GraphExecutor(loaded.snapshot).execute(graph, context))
    assert events[-1] == "final" and set(events[:2]) == {"first", "second"}


def test_graph_rejects_cycle_and_unknown_dependency():
    async def task(_): return None
    cycle = PipelineGraph().add(TaskNode("a", task, dependencies=("b",))).add(TaskNode("b", task, dependencies=("a",)))
    with pytest.raises(GraphValidationError, match="cycle"): cycle.validate()
    unknown = PipelineGraph().add(TaskNode("a", task, dependencies=("missing",)))
    with pytest.raises(GraphValidationError, match="unknown"): unknown.validate()


def test_artifact_store_rejects_workspace_escape(tmp_path):
    store = ArtifactStore(tmp_path)
    with pytest.raises(ValueError, match="escapes"): store.resolve("../secret")


def test_process_runner_preserves_stdout_diagnostics_on_failure():
    with pytest.raises(RuntimeError, match="stdout-diagnostic"):
        asyncio.run(ProcessRunner().run([
            sys.executable, "-c", "print('stdout-diagnostic'); raise SystemExit(2)",
        ]))
