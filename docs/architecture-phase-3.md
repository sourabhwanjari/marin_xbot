# MARINEX AI — Phase 3 Architecture: LangGraph Multi-Agent Orchestration

## Overview
**MARINEX AI** (Problem Statement: *ORCA — Marine EcOsystem Reasoning with Collaborative Agents*) orchestrates collaborative AI agents using **LangGraph StateGraph** to analyze marine conditions, evaluate navigation safety, identify Potential Fishing Zones (PFZ), and query marine regulatory guidelines.

Phase 3 introduces a graph-based multi-agent reasoning layer on top of Phase 1 (UI, Leaflet map, telemetry cards) and Phase 2 (LangChain, Chroma vector store, RAG pipeline).

---

## Architecture Diagram

```
                       User Marine Query
                               │
                               ▼
                    ┌──────────────────────┐
                    │     Planner Agent    │
                    │ (Intent Classification│
                    │ & Task Decomposition)│
                    └──────────┬───────────┘
                               │
               Conditional Edge (Routing Policy)
                               │
       ┌───────────────────────┼────────────────────────┐
       ▼                       ▼                        ▼
┌──────────────┐       ┌──────────────┐        ┌─────────────────┐
│Weather Agent │       │ Ocean Agent  │        │Geospatial Agent │
│ (IMD / GFS)  │       │  (INCOIS)    │        │   (PostGIS)     │
└──────┬───────┘       └──────┬───────┘        └────────┬────────┘
       │                      │                         │
       └──────────────────────┼─────────────────────────┘
                              ▼
                 ┌───────────────────────────┐
                 │   Marine Knowledge Agent  │
                 │   (Chroma Vector Store)   │
                 └────────────┬──────────────┘
                              │
                              ▼
                 ┌───────────────────────────┐
                 │   Risk Assessment Agent   │
                 │ (Multi-Factor Evaluation) │
                 └────────────┬──────────────┘
                              │
                              ▼
                 ┌───────────────────────────┐
                 │ Response Synthesizer Agent│
                 │  (Decision Recommendation)│
                 └────────────┬──────────────┘
                              │
                              ▼
                        Agent Response
```

---

## Core Components

### 1. Shared State: `MarineAgentState`
Defined in `backend/app/graph/state.py` as a `TypedDict`:
- `query`: Original natural language query.
- `intent`: Classified intent (`fishing_safety`, `weather_inquiry`, `ocean_conditions`, `pfz_discovery`, `restricted_zones`, `marine_knowledge`, `general_marine`, `out_of_scope`).
- `location`: Extracted target coastal region (e.g., "Mumbai", "Chennai", "Kochi", "Goa").
- `time_context`: Extracted temporal context (e.g., "tomorrow morning", "tonight", "this weekend").
- `selected_agents`: List of agents required for the query.
- `weather_result`: Output from `WeatherAgent` (wind, gusts, rain probability, storm risk).
- `ocean_result`: Output from `OceanAgent` (SST, chlorophyll, wave height, swell period, sea state).
- `geospatial_result`: Output from `GeospatialAgent` (coordinates, nearest port, distance from coast, restricted zone check).
- `knowledge_result`: Output from `MarineKnowledgeAgent` (retrieved document chunks and citations).
- `risk_result`: Output from `RiskAgent` (risk level `LOW`/`MEDIUM`/`HIGH`, risk factors, recommendation basis).
- `evidence`: Cumulative list of quantitative findings.
- `sources`: Cited documents from RAG knowledge base.
- `execution_steps`: Execution trace of each agent node (`completed`, `skipped`, `failed`).
- `final_answer`: Synthesized natural language decision recommendation.
- `data_status`: `"demo"` tag for synthetic/simulated data transparency.

---

### 2. Specialized Agents

| Agent | Responsibility | Tools Used |
|---|---|---|
| **Planner Agent** | Classifies query intent, extracts location/time entities, identifies necessary agents. | Rule-based semantic entity extraction |
| **Weather Agent** | Analyzes meteorological conditions (wind speed, squall gusts, precipitation). | `get_weather_data` |
| **Ocean Agent** | Analyzes sea-state dynamics (wave heights, swell period, SST, chlorophyll). | `get_ocean_data` |
| **Geospatial Agent** | Evaluates coordinates, coastal distances, port proximity, restricted corridors. | `get_coordinates`, `calculate_distance`, `check_restricted_zone`, `find_nearest_port` |
| **Marine Knowledge Agent** | Queries Chroma vector store for marine safety guidelines and heavy weather SOPs. | `search_marine_knowledge` (Phase 2 RAG) |
| **Risk Assessment Agent** | Multi-factor reasoning over wave, wind, storm, and zone boundaries $\rightarrow$ `LOW`/`MEDIUM`/`HIGH`. | Deterministic multi-factor risk matrix |
| **Response Synthesizer** | Combines evidence, risk level, and sources into clear, actionable recommendations. | Structured decision synthesizer |

---

### 3. Conditional Routing & Graph Edges
Defined in `backend/app/graph/edges.py`:
- `route_after_planner(state)`:
  - If `intent == "out_of_scope"` $\rightarrow$ bypasses all domain agents directly to `response`.
  - If `intent == "marine_knowledge"` $\rightarrow$ routes directly to `marine_knowledge`.
  - If `intent == "weather_inquiry"` $\rightarrow$ routes to `weather` $\rightarrow$ `response`.
  - If `intent == "ocean_conditions"` $\rightarrow$ routes to `ocean` $\rightarrow$ `response`.
  - For `fishing_safety`, `general_marine`, `pfz_discovery` $\rightarrow$ routes through domain agents sequentially (`weather` $\rightarrow$ `ocean` $\rightarrow$ `geospatial` $\rightarrow$ `marine_knowledge` $\rightarrow$ `risk` $\rightarrow$ `response`).

---

### 4. API Endpoints

#### `POST /api/agent/chat`
Dedicated endpoint returning full multi-agent orchestration payload:
```json
{
  "message": "Is it safe to go fishing tomorrow morning near Mumbai?",
  "location": "Mumbai"
}
```
Response:
```json
{
  "answer": "SAFETY ASSESSMENT: CAUTION ADVISED (DEMO)...",
  "intent": "fishing_safety",
  "risk_level": "MEDIUM",
  "location": "Mumbai",
  "time_context": "tomorrow morning",
  "sources": [{"file": "demo_marine_safety.txt", "page": 1}],
  "evidence": [
    "Significant wave height: 2.3m (Caution threshold: 2.0m)",
    "Wind speed: 18.0 knots (Gusts up to 24.0 knots)",
    "Rain probability: 45%"
  ],
  "execution_steps": [
    {"agent": "planner", "status": "completed", "details": "Classified fishing_safety near Mumbai"},
    {"agent": "weather", "status": "completed", "details": "Wind 18kt, rain prob 45%"},
    {"agent": "ocean", "status": "completed", "details": "Wave height 2.3m, SST 28.2°C"},
    {"agent": "geospatial", "status": "completed", "details": "Validated Mumbai coastal sector"},
    {"agent": "risk", "status": "completed", "details": "Risk level: MEDIUM"},
    {"agent": "response", "status": "completed", "details": "Synthesized decision recommendation"}
  ],
  "data_status": "demo",
  "is_demo": true
}
```

#### `GET /api/agent/status`
Returns agent registry and graph orchestrator status.

#### `POST /api/chat`
Updated to route through the LangGraph workflow while preserving backward compatibility with Phase 1 & 2 clients.
