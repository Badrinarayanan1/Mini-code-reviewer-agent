from __future__ import annotations

from fastapi import FastAPI, HTTPException

from .engine.engine import GraphEngine
from .engine.models import Graph, GraphRunRequest, GraphRunResponse
from .storage.memory_store import graph_store, run_store
from .workflows.code_review import (
    create_default_code_review_graph,
    register_code_review_tools,
)

app = FastAPI(title="Mini Agent Workflow Engine")

# Initialize workflow tools and default graph
register_code_review_tools()
create_default_code_review_graph()

engine = GraphEngine(graph_store=graph_store, run_store=run_store)


@app.post("/graph/create")
def create_graph(graph: Graph):
    """Create or overwrite a graph definition."""
    graph_store.save(graph)
    return {"graph_id": graph.id}


@app.post("/graph/run", response_model=GraphRunResponse)
async def run_graph(request: GraphRunRequest):
    """Run a graph from the beginning with an initial state."""
    try:
        run = await engine.run_graph(request.graph_id, request.state)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return GraphRunResponse(
        run_id=run.run_id,
        graph_id=run.graph_id,
        finished=run.finished,
        current_node=run.current_node,
        final_state=run.state,
        log=run.log,
    )


@app.get("/graph/state/{run_id}", response_model=GraphRunResponse)
def get_graph_state(run_id: str):
    """Return the state and log for a previously started run."""
    try:
        run = run_store.get(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return GraphRunResponse(
        run_id=run.run_id,
        graph_id=run.graph_id,
        finished=run.finished,
        current_node=run.current_node,
        final_state=run.state,
        log=run.log,
    )


from fastapi import WebSocket, WebSocketDisconnect
from .engine.models import CodeReviewState

@app.websocket("/ws/code-review")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # We can reuse the same graph definition
    graph_id = "code_review_default"
    
    # Persist iteration across the session
    current_iteration = 0
    
    try:
        while True:
            # 1. Receive code from client
            # Expected JSON: {"code": "...", "threshold": 0.8}
            data = await websocket.receive_json()
            
            # 2. Parse into state
            # If we don't have code, just skip
            code_input = data.get("code")
            if not code_input:
                await websocket.send_json({"error": "No code provided"})
                continue
            
            threshold = data.get("threshold", 0.8)
            
            # Increment iteration logic
            # If it's the first run, iteration is 0 (or 1). 
            # We want to preserve the history notion, so we pass current_iteration.
            initial_state = CodeReviewState(
                code=code_input,
                threshold=threshold,
                iteration=current_iteration
            )
            
            # 3. Run the analysis graph (linear)
            # We run it once. The graph is now configured to stop after 'suggest'.
            run = await engine.run_graph(graph_id, initial_state)
            
            final_state = run.state
            # Update our session iteration tracker
            current_iteration = final_state.iteration
            
            # 4. Construct response
            response = {
                "quality_score": final_state.quality_score,
                "threshold": final_state.threshold,
                "issues": final_state.issues,
                "suggestions": final_state.suggestions,
                "complexity": final_state.complexity,
                "functions": final_state.functions,
                "node": run.current_node or "finished",
                "iteration": final_state.iteration,
            }
            
            # 5. Check if accepted
            if final_state.quality_score >= final_state.threshold:
                response["accepted"] = True
                response["message"] = f"Code accepted! Quality score meets threshold. (Iterations: {final_state.iteration})"
            else:
                response["accepted"] = False
                response["message"] = f"Quality score too low. Rejected. Looping... (Iteration {final_state.iteration})"
                
            await websocket.send_json(response)
            
    except WebSocketDisconnect:
        print("Client disconnected")

