# LangGraph Multi-Agent Orchestration — Phase 3 Implementation

## Overview
MARINEX AI uses a **LangGraph StateGraph** to orchestrate specialized marine agents. The graph enables dynamic task decomposition, multi-domain tool execution, risk assessment, and decision synthesis.

---

## State Schema (`MarineAgentState`)

Defined in `backend/app/graph/state.py`:

```python
class MarineAgentState(TypedDict):
    query: str
    intent: Optional[str]
    location: Optional[str]
    time_context: Optional[str]
    selected_agents: List[str]
    tasks: List[str]
    weather_result: Optional[Dict[str, Any]]
    ocean_result: Optional[Dict[str, Any]]
    geospatial_result: Optional[Dict[str, Any]]
    knowledge_result: Optional[Dict[str, Any]]
    risk_result: Optional[Dict[str, Any]]
    evidence: List[str]
    sources: List[Dict[str, Any]]
    execution_steps: List[Dict[str, Any]]
    final_answer: Optional[str]
    data_status: str
    errors: List[str]
```

---

## Active Nodes & Execution Flow

```
                      [START]
                         │
                         ▼
                  [planner_node]
                         │
        (route_after_planner conditional edge)
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
  [weather_node]   [knowledge_node]   [response_node]
        │                │                │
        ▼                │                │
  [ocean_node]           │                │
        │                │                │
        ▼                │                │
[geospatial_node]        │                │
        │                │                │
        ▼                │                │
 [knowledge_node]        │                │
        │                │                │
        ▼                │                │
   [risk_node]           │                │
        │                │                │
        ▼                ▼                ▼
 ┌───────────────────────────────────────────────┐
 │                [response_node]                │
 └───────────────────────┬───────────────────────┘
                         │
                         ▼
                       [END]
```

---

## How to Add a New Agent

Follow these steps to add a new specialized agent (e.g., `SatelliteObservationAgent` or `RouteOptimizationAgent`):

### 1. Define Model & State Field
In `backend/app/models/agent_models.py`:
```python
class SatelliteResult(BaseModel):
    sst_fronts: List[str]
    turbidity_index: float
    data_status: str = "demo"
```
In `backend/app/graph/state.py`:
```python
class MarineAgentState(TypedDict):
    ...
    satellite_result: Optional[Dict[str, Any]]
```

### 2. Implement Agent Logic
In `backend/app/agents/satellite_agent.py`:
```python
from app.graph.state import MarineAgentState

def run_satellite_agent(state: MarineAgentState) -> MarineAgentState:
    # 1. Fetch satellite observation telemetry
    # 2. Append findings to state["evidence"]
    # 3. Record execution step: {"agent": "satellite", "status": "completed", "details": ...}
    return state
```

### 3. Add Graph Node
In `backend/app/graph/nodes.py`:
```python
from app.agents.satellite_agent import run_satellite_agent

def satellite_node(state: MarineAgentState) -> MarineAgentState:
    return run_satellite_agent(state)
```

### 4. Wire Node & Edges in Workflow
In `backend/app/graph/workflow.py`:
```python
builder.add_node("satellite", satellite_node)
# Add edge or conditional edge as appropriate:
builder.add_edge("ocean", "satellite")
builder.add_edge("satellite", "geospatial")
```

### 5. Write Tests
Add unit tests in `backend/tests/test_agents.py` and integration tests in `backend/tests/test_graph.py`.
