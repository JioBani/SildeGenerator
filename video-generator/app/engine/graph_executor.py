from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from app.harness_sdk.api import HarnessSnapshot
from app.harness_sdk.context import HarnessContext
from app.harness_sdk.errors import HarnessTaskError
from app.harness_sdk.graph import PipelineGraph
from app.harness_sdk.task import TaskResult
from .validation import require_outputs


class LocalLeaseProvider:
    def __init__(self, limits: dict[str, int] | None = None):
        values = limits or {"image": 4, "voice": 2, "ffmpeg": 1, "cpu": 2, "io": 4}
        self._semaphores = {kind: asyncio.Semaphore(limit) for kind, limit in values.items()}

    @asynccontextmanager
    async def request(self, kind: str, slots: int = 1):
        semaphore = self._semaphores.setdefault(kind, asyncio.Semaphore(1))
        for _ in range(max(1, slots)): await semaphore.acquire()
        try: yield
        finally:
            for _ in range(max(1, slots)): semaphore.release()


class GraphExecutor:
    def __init__(self, snapshot: HarnessSnapshot):
        self.snapshot = snapshot

    async def execute(self, graph: PipelineGraph, context: HarnessContext) -> dict[str, TaskResult | None]:
        graph.validate()
        pending = set(graph.nodes)
        completed: dict[str, TaskResult | None] = {}
        while pending:
            ready = sorted(task_id for task_id in pending if set(graph.nodes[task_id].dependencies) <= completed.keys())
            async def execute_one(task_id: str):
                node = graph.nodes[task_id]
                last_error: Exception | None = None
                for attempt in range(1, max(1, node.retry.attempts) + 1):
                    try:
                        async with context.leases.request(node.resource.kind, node.resource.slots):
                            result = await node.run(context)
                        require_outputs(node.expected_outputs)
                        return task_id, result
                    except asyncio.CancelledError:
                        raise
                    except Exception as error:
                        last_error = error
                        if attempt < node.retry.attempts and node.retry.backoff_seconds:
                            await asyncio.sleep(node.retry.backoff_seconds * attempt)
                assert last_error
                raise HarnessTaskError(self.snapshot.id, self.snapshot.version, task_id, last_error)
            results = await asyncio.gather(*(execute_one(task_id) for task_id in ready))
            for task_id, result in results:
                completed[task_id] = result; pending.remove(task_id)
        return completed
