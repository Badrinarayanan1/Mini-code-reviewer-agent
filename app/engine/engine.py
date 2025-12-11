from __future__ import annotations

from typing import Optional

from .models import CodeReviewState, ExecutionLogEntry, Graph, GraphRun
from .registry import tool_registry


class GraphEngine:
    """Core graph execution engine.

    It executes nodes sequentially, following edges defined in the Graph
    and using simple conditional branching to support loops.
    """

    def __init__(self, graph_store, run_store, max_iterations: int = 20) -> None:
        self.graph_store = graph_store
        self.run_store = run_store
        self.max_iterations = max_iterations

    async def run_graph(self, graph_id: str, initial_state: CodeReviewState) -> GraphRun:
        graph: Graph = self.graph_store.get(graph_id)
        run: GraphRun = self.run_store.create(graph_id, initial_state)

        while run.current_node is not None and not run.finished:
            if run.state.iteration >= self.max_iterations:
                # Safety guard to avoid infinite loops
                run.finished = True
                break

            node_cfg = graph.nodes[run.current_node]
            tool = tool_registry.get(node_cfg.tool)

            # Execute tool with the current state
            new_state = tool(run.state)
            if not isinstance(new_state, CodeReviewState):
                new_state = CodeReviewState(**new_state.dict())

            run.state = new_state

            # Log after node execution
            log_entry = ExecutionLogEntry(
                node=node_cfg.name,
                timestamp=self.run_store.now(),
                state_snapshot=run.state.dict(),
            )
            run.log.append(log_entry)

            # Decide next node
            next_node = self._decide_next_node(node_cfg, run.state)
            run.current_node = next_node
            if next_node is None:
                run.finished = True
                break

        self.run_store.update(run)
        return run

    def _decide_next_node(self, node_cfg, state: CodeReviewState) -> Optional[str]:
        if not node_cfg.condition_key:
            # Simple linear edge
            return node_cfg.next_node

        value = getattr(state, node_cfg.condition_key)
        target = node_cfg.condition_value
        op = node_cfg.condition_op

        if op is None or target is None:
            return node_cfg.next_node

        is_ok = False
        if op == ">=":
            is_ok = value >= target
        elif op == ">":
            is_ok = value > target
        elif op == "<=":
            is_ok = value <= target
        elif op == "<":
            is_ok = value < target
        elif op == "==":
            is_ok = value == target

        if is_ok:
            return node_cfg.next_on_success
        return node_cfg.next_on_failure or node_cfg.next_node
