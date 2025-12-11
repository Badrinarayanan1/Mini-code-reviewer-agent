from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict

from app.engine.models import CodeReviewState, Graph, GraphRun


class GraphStore:
    """In-memory store for graphs."""

    def __init__(self) -> None:
        self._graphs: Dict[str, Graph] = {}

    def save(self, graph: Graph) -> None:
        self._graphs[graph.id] = graph

    def get(self, graph_id: str) -> Graph:
        if graph_id not in self._graphs:
            raise KeyError(f"Graph '{graph_id}' not found")
        return self._graphs[graph_id]


class RunStore:
    """In-memory store for graph runs."""

    def __init__(self, graph_store: GraphStore) -> None:
        self._runs: Dict[str, GraphRun] = {}
        self._graph_store = graph_store

    def now(self):
        return datetime.now(timezone.utc)

    def create(self, graph_id: str, state: CodeReviewState) -> GraphRun:
        graph = self._graph_store.get(graph_id)
        run_id = str(uuid.uuid4())
        run = GraphRun(
            run_id=run_id,
            graph_id=graph_id,
            current_node=graph.start_node,
            state=state,
            log=[],
            finished=False,
        )
        self._runs[run_id] = run
        return run

    def update(self, run: GraphRun) -> None:
        self._runs[run.run_id] = run

    def get(self, run_id: str) -> GraphRun:
        if run_id not in self._runs:
            raise KeyError(f"Run '{run_id}' not found")
        return self._runs[run_id]


graph_store = GraphStore()
run_store = RunStore(graph_store=graph_store)
