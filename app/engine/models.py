from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class CodeReviewState(BaseModel):
    """Shared state that flows through the code review workflow."""

    code: str = Field(..., description="Python source code to review")
    functions: List[str] = Field(default_factory=list)
    complexity: Dict[str, int] = Field(default_factory=dict)
    issues: List[Dict[str, Any]] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    quality_score: float = 0.0
    threshold: float = 0.8
    iteration: int = 0


class NodeConfig(BaseModel):
    """Configuration for a single node in the graph."""

    name: str
    tool: str
    next_node: Optional[str] = None

    # Optional branching / looping
    condition_key: Optional[str] = None
    condition_op: Optional[Literal[">=", ">", "<=", "<", "=="]] = None
    condition_value: Optional[float] = None
    next_on_success: Optional[str] = None
    next_on_failure: Optional[str] = None


class Graph(BaseModel):
    """A simple directed graph of nodes."""

    id: str
    start_node: str
    nodes: Dict[str, NodeConfig]


class ExecutionLogEntry(BaseModel):
    node: str
    timestamp: datetime
    state_snapshot: Dict[str, Any]


class GraphRun(BaseModel):
    run_id: str
    graph_id: str
    current_node: Optional[str]
    state: CodeReviewState
    log: List[ExecutionLogEntry] = Field(default_factory=list)
    finished: bool = False


class GraphRunRequest(BaseModel):
    graph_id: str
    state: CodeReviewState


class GraphRunResponse(BaseModel):
    run_id: str
    graph_id: str
    finished: bool
    current_node: Optional[str]
    final_state: CodeReviewState
    log: List[ExecutionLogEntry]
