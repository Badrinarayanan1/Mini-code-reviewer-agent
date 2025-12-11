from __future__ import annotations

import ast
import os
import tempfile
from io import StringIO
from typing import Dict, List

from pylint.lint import Run
from pylint.reporters.text import TextReporter

from app.engine.models import CodeReviewState, Graph, NodeConfig
from app.engine.registry import tool_registry
from app.storage.memory_store import graph_store


def extract_functions(state: CodeReviewState) -> CodeReviewState:
    """Parse the code and extract function names."""
    try:
        tree = ast.parse(state.code)
    except SyntaxError:
        # If code is not valid Python, treat as no functions
        state.functions = []
        return state

    functions: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions.append(node.name)
    state.functions = functions
    return state


def check_complexity(state: CodeReviewState) -> CodeReviewState:
    """Very naive complexity metric based on number of statements per function."""
    try:
        tree = ast.parse(state.code)
    except SyntaxError:
        state.complexity = {}
        return state

    complexity: Dict[str, int] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            complexity[node.name] = len(node.body)
    state.complexity = complexity
    return state


def detect_basic_issues(state: CodeReviewState) -> CodeReviewState:
    """Use pylint to detect basic issues in the provided code.

    We run pylint on a temporary file and parse its text output into a list of
    issues with line numbers and short messages.
    """
    # Write code to a temporary file
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tmp:
        tmp.write(state.code)
        tmp_path = tmp.name

    buffer = StringIO()
    reporter = TextReporter(output=buffer)

    try:
        # Disable some noisy conventions and refactors to keep the output focused
        Run([tmp_path, "--disable=R,C"], reporter=reporter, exit=False)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    output = buffer.getvalue().splitlines()
    issues: List[Dict[str, str]] = []

    for line in output:
        # Typical pylint line format:
        # tmp.py:10:0: W0612: Unused variable 'x' (unused-variable)
        if ".py:" not in line:
            continue
        try:
            before, message_part = line.split(".py:", 1)
            location, rest = message_part.split(":", 1)
            line_number_str = location.split(":")[0]
            line_number = int(line_number_str.strip())
            rest = rest.strip()
            issues.append(
                {
                    "line": line_number,
                    "message": rest,
                }
            )
        except ValueError:
            # If parsing fails, skip this line
            continue

    state.issues = issues
    return state


def suggest_improvements(state: CodeReviewState) -> CodeReviewState:
    """Generate human-readable suggestions and update the quality score."""
    suggestions: List[str] = []

    # Suggestions based on complexity
    for func_name, score in state.complexity.items():
        if score > 15:
            suggestions.append(
                f"Function '{func_name}' looks quite complex with {score} statements. "
                f"Consider breaking it into smaller functions."
            )
        elif score > 8:
            suggestions.append(
                f"Function '{func_name}' could be simplified; it has {score} statements."
            )

    # Suggestions based on issues reported by pylint
    for issue in state.issues:
        line = issue.get("line", "?")
        message = issue.get("message", "")
        suggestions.append(f"Resolve issue at line {line}: {message}")

    state.suggestions = suggestions

    # Compute quality score
    issues_count = len(state.issues)
    issue_penalty = min(0.6, 0.12 * issues_count)

    if state.complexity:
        avg_complexity = sum(state.complexity.values()) / len(state.complexity)
    else:
        avg_complexity = 0.0

    # Only penalize complexity significantly if average is high
    complexity_penalty = min(0.3, max(0.0, (avg_complexity - 5) / 25.0))

    raw_score = 1.0 - issue_penalty - complexity_penalty

    if raw_score < 0.0:
        raw_score = 0.0
    if raw_score > 1.0:
        raw_score = 1.0

    state.quality_score = raw_score
    state.iteration += 1
    return state


def register_code_review_tools() -> None:
    """Register all tools used by the code review workflow."""
    tool_registry.register("extract_functions", extract_functions)
    tool_registry.register("check_complexity", check_complexity)
    tool_registry.register("detect_basic_issues", detect_basic_issues)
    tool_registry.register("suggest_improvements", suggest_improvements)


def create_default_code_review_graph() -> None:
    """Create and store a default graph for the code review mini-agent."""
    graph = Graph(
        id="code_review_default",
        start_node="extract",
        nodes={
            "extract": NodeConfig(
                name="extract",
                tool="extract_functions",
                next_node="complexity",
            ),
            "complexity": NodeConfig(
                name="complexity",
                tool="check_complexity",
                next_node="issues",
            ),
            "issues": NodeConfig(
                name="issues",
                tool="detect_basic_issues",
                next_node="suggest",
            ),
            "suggest": NodeConfig(
                name="suggest",
                tool="suggest_improvements",
                condition_key="quality_score",
                condition_op=">=",
                condition_value=0.8,
                next_on_success=None,
                next_on_failure=None,  # Stop and let the user re-submit via WebSocket
            ),
        },
    )
    graph_store.save(graph)
