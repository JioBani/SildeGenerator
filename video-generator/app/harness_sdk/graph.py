from __future__ import annotations

from dataclasses import dataclass, field

from .errors import GraphValidationError
from .task import TaskNode


@dataclass
class PipelineGraph:
    nodes: dict[str, TaskNode] = field(default_factory=dict)

    def add(self, node: TaskNode) -> "PipelineGraph":
        if not node.id or node.id in self.nodes:
            raise GraphValidationError(f"duplicate or empty task id: {node.id}")
        self.nodes[node.id] = node
        return self

    def validate(self) -> None:
        unknown = sorted({dependency for node in self.nodes.values() for dependency in node.dependencies if dependency not in self.nodes})
        if unknown:
            raise GraphValidationError(f"unknown dependencies: {', '.join(unknown)}")
        state: dict[str, int] = {}
        def visit(task_id: str) -> None:
            if state.get(task_id) == 1:
                raise GraphValidationError(f"cycle detected at {task_id}")
            if state.get(task_id) == 2:
                return
            state[task_id] = 1
            for dependency in self.nodes[task_id].dependencies:
                visit(dependency)
            state[task_id] = 2
        for task_id in self.nodes:
            visit(task_id)

    def topological_ids(self) -> list[str]:
        self.validate()
        completed: set[str] = set()
        ordered: list[str] = []
        while len(ordered) < len(self.nodes):
            ready = sorted(task_id for task_id, node in self.nodes.items() if task_id not in completed and set(node.dependencies) <= completed)
            if not ready:
                raise GraphValidationError("graph has no executable node")
            ordered.extend(ready)
            completed.update(ready)
        return ordered
