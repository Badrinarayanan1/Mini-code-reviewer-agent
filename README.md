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
    "code": "BAL = 0\nOWNER = None\n\nclass Acct:\n    def __init__(self, name, bal=0):\n        global OWNER, BAL\n        OWNER = name\n        BAL = bal\n\n    def depo(self, amt):\n        global BAL\n        BAL = BAL + amt\n\n    def wd(self, amt):\n        global BAL\n        BAL = BAL - amt\n\n    def bal(self):\n        return BAL\n\n\ndef run():\n    a = Acct(\"Bob\", 100)\n    a.depo(200)\n    a.wd(50)\n    print(\"bal:\", a.bal())\n\n\nrun()\n",
    "threshold": 0.8
  }
}

```

- `code` is the Python source to review.
- `threshold` is the minimum quality score to stop the loop (default 0.8).

**Response:**

```json
      "node": "suggest",
      "timestamp": "2025-12-11T00:48:24.780810+00:00",
      "state_snapshot": {
        "code": "BAL = 0\nOWNER = None\n\nclass Acct:\n    def __init__(self, name, bal=0):\n        global OWNER, BAL\n        OWNER = name\n        BAL = bal\n\n    def depo(self, amt):\n        global BAL\n        BAL = BAL + amt\n\n    def wd(self, amt):\n        global BAL\n        BAL = BAL - amt\n\n    def bal(self):\n        return BAL\n\n\ndef run():\n    a = Acct(\"Bob\", 100)\n    a.depo(200)\n    a.wd(50)\n    print(\"bal:\", a.bal())\n\n\nrun()\n",
        "functions": [
          "run",
          "__init__",
          "depo",
          "wd",
          "bal"
        ],
        "complexity": {
          "run": 4,
          "__init__": 3,
          "depo": 2,
          "wd": 2,
          "bal": 1
        },
        "issues": [
          {
            "line": 6,
            "message": "8: W0603: Using the global statement (global-statement)"
          },
          {
            "line": 11,
            "message": "8: W0603: Using the global statement (global-statement)"
          },
          {
            "line": 15,
            "message": "8: W0603: Using the global statement (global-statement)"
          }
        ],
        "suggestions": [
          "Resolve issue at line 6: 8: W0603: Using the global statement (global-statement)",
          "Resolve issue at line 11: 8: W0603: Using the global statement (global-statement)",
          "Resolve issue at line 15: 8: W0603: Using the global statement (global-statement)"
        ],
        "quality_score": 0.64,
        "threshold": 0.8,
        "iteration": 1
      }
    }
  ]
}
```

### `GET /graph/state/{run_id}`

Fetch the final state and execution log for a previously executed run.


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

## Working
<img width="3151" height="1834" alt="image" src="https://github.com/user-attachments/assets/7e752324-5f9b-4dbc-bed0-163a2f5ec273" />

<img width="3193" height="1818" alt="image" src="https://github.com/user-attachments/assets/6295a54f-5aa4-4f15-83cd-3452828fbe21" />

## Interactive Manual Client

A manual client script `manual_client.py` is included to interactively test the WebSocket-based code review workflow.

### Usage

1.  **Ensure the server is running**:
    ```bash
    uvicorn app.main:app --reload
    ```
2.  **Run the client**:
    ```bash
    python manual_client.py
    ```
3.  **Follow the prompts**:
    - Enter a quality threshold (default is 0.8).
    - The client will create/monitor `input_code.py` in the current directory.
    - Modify `input_code.py` in your editor.
    - Press **Enter** in the client terminal to send the code for review.
    - View the feedback (score, issues, suggestions) directly in the terminal.
    - Repeat until the code is accepted (score >= threshold).
<img width="2622" height="1871" alt="image" src="https://github.com/user-attachments/assets/0de24e93-c5ea-4ee6-938d-d3efc2a9d1cd" />

<img width="2623" height="1897" alt="image" src="https://github.com/user-attachments/assets/ef35ba39-74ab-480a-bb3e-bb200cc07738" />

## Possible Improvements

With more time, the following enhancements would be natural:

- Persistent storage using SQLite or Postgres via SQLAlchemy.
- Optional WebSocket endpoint to stream step-by-step execution logs.
- A major enhancement would be to allow the system to iteratively improve the code using a Large Language Model (e.g., OpenAI, Llama, Gemini).
  The workflow becomes:
extract → complexity → issues → suggest → ai_improve_code → re-evaluate → loop
- Richer quality score that uses different issue weights from `pylint`.
