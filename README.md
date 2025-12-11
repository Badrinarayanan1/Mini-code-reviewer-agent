# Mini Agent Workflow Engine (Code Review Mini-Agent)

This repository implements a small workflow engine in Python using FastAPI.
It supports:

- Nodes as Python functions ("tools") that read and mutate a shared state.
- A simple graph model that connects nodes with edges.
- Basic branching and looping based on values in the shared state.
- A sample **Code Review Mini-Agent** workflow using `pylint`.

## Project Structure

```text
app/
  __init__.py
  main.py                 # FastAPI application and HTTP endpoints
  engine/
    __init__.py
    models.py             # Pydantic models for state, graph, and runs
    registry.py           # Tool registry
    engine.py             # Core graph execution logic
  storage/
    __init__.py
    memory_store.py       # In-memory stores for graphs and runs
  workflows/
    __init__.py
    code_review.py        # Code Review Mini-Agent implementation
```

## Installation

Create and activate a virtual environment, then install dependencies:

```bash
pip install -r requirements.txt
```

## Running the API

Start the FastAPI application with Uvicorn:

```bash
uvicorn app.main:app --reload
```

The API will be available at:

- OpenAPI docs: http://127.0.0.1:8000/docs
- Root: http://127.0.0.1:8000

When the application starts, it automatically:

1. Registers the tools for the Code Review workflow.
2. Creates a default graph with ID `code_review_default`.

## Endpoints

### `POST /graph/create`

Create or overwrite a graph definition.

**Request body:**

```json
{
  "id": "my_graph",
  "start_node": "extract",
  "nodes": {
    "extract": {
      "name": "extract",
      "tool": "extract_functions",
      "next_node": "complexity"
    }
  }
}
```

**Response:**

```json
{
  "graph_id": "my_graph"
}
```

### `POST /graph/run`

Run a graph with an initial state.

For the default Code Review graph, send:

```json
{
  "graph_id": "code_review_default",
  "state": {
    "code": "def add(a, b):\n    return a + b",
    "threshold": 0.8
  }
}
```

- `code` is the Python source to review.
- `threshold` is the minimum quality score to stop the loop (default 0.8).

**Response:**

```json
{
  "run_id": "uuid-here",
  "graph_id": "code_review_default",
  "finished": true,
  "current_node": null,
  "final_state": { ... },
  "log": [
    {
      "node": "extract",
      "timestamp": "...",
      "state_snapshot": { ... }
    },
    ...
  ]
}
```

### `GET /graph/state/{run_id}`

Fetch the final state and execution log for a previously executed run.

**Response:** Same shape as `POST /graph/run`.

## Sample Code Snippets to Test

### High-quality code

```python
def add(a: int, b: int) -> int:
    """Return the sum of two integers."""
    return a + b


def is_even(n: int) -> bool:
    """Check whether a number is even."""
    return n % 2 == 0


def average(numbers: list[int]) -> float:
    """Calculate the average of a list of numbers."""
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)
```

### Poor-quality code

```python
def badFunction(x,y,z):
    a=1
    b=2
    c=3
    d=4
    e=5
    f=6
    g=7
    h=8
    i=9
    j=10

    if x>0:
        if y>0:
            if z>0:
                print("all positive")
            else:
                print("z negative")
        else:
            print("y negative")
    else:
        print("x negative")

    for i in range(0,10):
        for j in range(0,10):
            if i==j:
                print(i,j)

    unused_variable = 999
    return x+y+z
```

## What the Engine Supports

- Shared state model (`CodeReviewState`) flowing across nodes.
- Tool registry to register reusable node functions.
- Graph model with simple branching and looping:
  - `condition_key`, `condition_op`, and `condition_value` control routing.
  - `next_on_success` and `next_on_failure` allow loops.
- Code Review Mini-Agent:
  - Extracts functions.
  - Computes a naive complexity measure.
  - Uses `pylint` to detect issues.
  - Generates suggestions and a quality score between `0.0` and `1.0`.
  - Loops between `issues` and `suggest` until `quality_score >= threshold` or a
    safety limit on iterations is reached.

## Possible Improvements

With more time, the following enhancements would be natural:

- Persistent storage using SQLite or Postgres via SQLAlchemy.
- Optional WebSocket endpoint to stream step-by-step execution logs.
- A more expressive graph description language with additional validation.
- Support for multiple different workflows (e.g., summarization, data quality).
- Richer quality score that uses different issue weights from `pylint`.
