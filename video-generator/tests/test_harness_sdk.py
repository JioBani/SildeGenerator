from __future__ import annotations

import asyncio
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

ROOT = Path(__file__).resolve().parents[2]


def registry() -> HarnessRegistry:
    return HarnessRegistry(ROOT / "harnesses")


def test_discovers_versioned_harnesses_and_hashes_entire_packages():
    entries = registry().list()
    assert [entry["id"] for entry in entries] == ["classic-slide", "experimental-cut-move"]
    assert all(entry["compatible"] for entry in entries)
    assert all(len(entry["manifest_sha256"]) == 64 and len(entry["source_sha256"]) == 64 for entry in entries)
    assert entries[0]["source_sha256"] != entries[1]["source_sha256"]


def test_experimental_effect_is_loaded_without_core_effect_allowlist():
    loaded = registry().load("experimental-cut-move")
    assert loaded.instance.transition == "slideleft"
    source = (loaded.root / "src/experimental_cut_move/plugin.py").read_text(encoding="utf-8")
    assert "app.engine" not in source


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
