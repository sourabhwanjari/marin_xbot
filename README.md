# MARINEX AI
### AI-Powered Marine Intelligence & Decision Support
**Official Problem Statement**: **ORCA — Marine EcOsystem Reasoning with Collaborative Agents**

[![System Status](https://img.shields.io/badge/Status-Phase%204%20Real%20Marine%20Data%20%2B%20Geo--Spatial%20Intelligence-00f0ff?style=flat-square)](#)
[![Stack](https://img.shields.io/badge/Stack-FastAPI%20%7C%20Next.js%2014%20%7C%20TypeScript%20%7C%20Tailwind%20%7C%20Leaflet-00ffaa?style=flat-square)](#)
[![Architecture](https://img.shields.io/badge/Architecture-LangGraph%20%2B%20RAG%20%2B%20MarineDataGateway-blue?style=flat-square)](#)
[![License](https://img.shields.io/badge/License-MIT-gray?style=flat-square)](#)

---

## 1. Project Name & Subtitle
- **Name**: **MARINEX AI**
- **Subtitle**: *"AI-Powered Marine Intelligence & Decision Support"*
- **Hackathon Context**: Smart India Hackathon (SIH 57) — **ORCA: Marine EcOsystem Reasoning with Collaborative Agents**

---

## 2. Problem Statement
> *"Develop an Agentic AI-powered conversational Marine Intelligence Platform that enables users to access, analyze, and reason over marine information using natural language.*
>
> *The platform should eventually be able to interpret user intent, decompose complex requests into executable tasks, coordinate multiple specialized AI agents, retrieve marine and geospatial datasets, perform spatial-temporal reasoning, and synthesize actionable recommendations through a conversational interface."*

Marine stakeholders — from artisanal and mechanized fishermen to coastal disaster authorities and ocean researchers — face critical challenges accessing and interpreting disparate oceanographic data. Current systems isolate satellite Earth Observation (EO) data, weather forecasts, high wave alerts, and regulatory geofencing across separate portals, creating information friction that risks lives and reduces fishing productivity.

---

## 3. Solution Overview
**MARINEX AI** implements the ORCA vision: a multi-agent collaborative platform accessible via an intuitive natural language interface coupled with an interactive geospatial marine map.

Instead of a generic AI chatbot, MARINEX AI is tailored exclusively for marine decision support:
- Translates natural language inquiries into structured spatial-temporal queries.
- Connects to live meteorological and oceanographic feeds (Open-Meteo Weather & Marine APIs).
- Employs a centralized **MarineDataGateway** with in-memory TTL caching and deterministic data models.
- Ingests INCOIS Potential Fishing Zones (PFZs) correlated with SST and Chlorophyll-a thermal fronts.
- Executes geospatial boundary intelligence (ray-casting point-in-polygon, port proximity, hazard buffers).
- Orchestrates 7 specialized AI agents via **LangGraph StateGraph**.
- Provides transparent data provenance tagging (`external`, `verified`, `demo`, `not_configured`).

---

## 4. System Architecture

```
                                  User Marine Query / Map Layer Toggle
                                                   │
                                                   ▼
                                    ┌─────────────────────────────┐
                                    │    MARINEX AI Frontend      │
                                    │  - Next.js 14 / TypeScript  │
                                    │  - Data Feeds Status Popover│
                                    │  - Leaflet Layer Toggles    │
                                    └──────────────┬──────────────┘
                                                   │
                         ┌─────────────────────────┴─────────────────────────┐
                         │                                                   │
                         ▼                                                   ▼
          ┌─────────────────────────────┐                     ┌─────────────────────────────┐
          │   REST Endpoints (/api)     │                     │  LangGraph Multi-Agent Hub  │
          │ - /data-sources/status      │                     │  - Planner Agent            │
          │ - /data-sources/pfz         │                     │  - Weather Agent            │
          │ - /data-sources/geospatial  │                     │  - Ocean Agent              │
          │ - /agent/chat               │                     │  - Geospatial Agent         │
          └──────────────┬──────────────┘                     │  - Knowledge Agent (RAG)    │
                         │                                    │  - Risk Assessment Agent    │
                         │                                    │  - Response Synthesizer     │
                         │                                    └──────────────┬──────────────┘
                         │                                                   │
                         └─────────────────────────┬─────────────────────────┘
                                                   │
                                                   ▼
                              ┌─────────────────────────────────────────┐
                              │           MarineDataGateway             │
                              │  (Centralized Ingestion & Cache Hub)   │
                              │  - In-Memory LRU Cache with TTLs        │
                              │  - Status Tracking (external/demo/...)  │
                              │  - Resilient Graceful Degradation       │
                              └────────────────────┬────────────────────┘
                                                   │
         ┌───────────────────┬─────────────────────┼─────────────────────┬───────────────────┐
         ▼                   ▼                     ▼                     ▼                   ▼
┌─────────────────┐ ┌─────────────────┐  ┌───────────────────┐ ┌───────────────────┐ ┌─────────────────┐
│ Weather Service │ │  Ocean Service  │  │    PFZ Service    │ │ Satellite Service │ │Geospatial Engine│
│  (Open-Meteo)   │ │  (Open-Meteo)   │  │ (INCOIS Sectors)  │ │  (ISRO MOSDAC)    │ │(GeoJSON/PostGIS)│
│  Live Forecast  │ │  Marine Dynamics│  │ Thermal Fronts    │ │ Oceansat-3/INSAT  │ │ Boundary/Safety │
└────────┬────────┘ └────────┬────────┘  └─────────┬─────────┘ └─────────┬─────────┘ └────────┬────────┘
         │                   │                     │                     │                    │
         ▼                   ▼                     ▼                     ▼                    ▼
   [api.open-meteo]   [marine-api.open]     [Sector Models]       [Not Configured]      [Spatial Math &
   Wind/Gust/Rain     Wave/Swell/Current    SST/Chlorophyll       Credential Guard]     GeoJSON Layers]
```

---

## 5. Technology Stack

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Library**: React 18
- **Language**: TypeScript
- **Styling**: Tailwind CSS (with custom Marine-Tech palette)
- **Geospatial Visualization**: Leaflet & React-Leaflet
- **Icons**: Lucide React

### Backend
- **Framework**: Python 3.10+ / FastAPI
- **Server**: Uvicorn (ASGI)
- **Validation**: Pydantic v2
- **Agent Orchestration**: LangGraph StateGraph
- **RAG & Vector Store**: LangChain + Chroma
- **Data Gateway**: In-Memory LRU Cache with configurable TTLs
- **Geospatial Engine**: Pure Python ray-casting & Haversine spatial math + PostGIS readiness

---

## 6. Phase 1 Features — Foundation & UI
- [x] **Futuristic Marine-Tech Dashboard**: Dark oceanic theme with glassmorphic panels and cyan accents.
- [x] **Interactive Marine GIS Map**:
  - Live Leaflet map with CartoDB Voyager tiles.
  - User location marker with pulsing accuracy perimeter.
  - Potential Fishing Zone (PFZ) markers with SST, chlorophyll, and suitability popups.
  - Caution and hazard zone polygons (high wave/storm sectors).
  - Restricted maritime zones (naval security fairways & marine sanctuaries).
  - Visual map legend.
- [x] **Marine Conversational Intelligence Panel**:
  - Domain-specific responses to fishing, weather, and safety questions.
  - One-click suggested query chips.
  - Clear "DEMO / MOCK DATA" tagging.
- [x] **Marine Status Cards**: Compact cards for Weather, Ocean, Fishing, and Safety.
- [x] **Oceanographic Conditions Panel**: Real-time telemetry for SST, Chlorophyll, Wave Height, Wind Speed, Sea State, and Visibility.
- [x] **Active Marine Alerts Section**: Categorized bulletins with severity badges (`HIGH`, `MEDIUM`, `LOW`).

---

## 7. Phase 2 Features — LangChain + RAG Pipeline
- [x] **Full RAG Ingestion Pipeline**:
  - Modular loaders for **PDF** (`pypdf`), **DOCX** (`python-docx`), and **TXT/MD** files.
  - Text splitting via `RecursiveCharacterTextSplitter` (`CHUNK_SIZE=1000`, `CHUNK_OVERLAP=150`).
  - Metadata preservation: source path, file name, page number, document type, and deterministic chunk ID hash.
- [x] **Local Vector Database (Chroma)**:
  - Persistent Chroma vector store located at `backend/storage/chroma`.
  - Duplicate prevention mechanism ensuring only new/modified documents are embedded.
- [x] **Pluggable Embeddings Abstraction**:
  - Supports Google Gemini / OpenAI embeddings via environment configuration.
  - Deterministic 384-dimensional local fallback embeddings for 100% offline, zero-key hackathon execution.
- [x] **Deterministic Query Routing & Grounded Citations**:
  - Automatic query classification (`KNOWLEDGE_BASE`, `LIVE_MARINE_DATA`, `MIXED`).
  - Responses cite specific document filenames and page numbers.
- [x] **Knowledge Base Management UI**:
  - "Knowledge Base" button in the top navigation with interactive modal to upload files and inspect index status.

---

## 8. Phase 3 Features — LangGraph Multi-Agent Orchestration
- [x] **LangGraph StateGraph Engine**:
  - Centralized shared state (`MarineAgentState`) tracking query, extracted entities, agent results, evidence, citations, and execution steps.
  - Dynamic conditional edge routing based on classified user intent.
- [x] **7 Specialized Collaborative Agents**:
  - **Planner Agent**: Classifies intent, extracts coastal location and temporal context, decomposes queries into sub-tasks.
  - **Weather Agent**: Evaluates wind speed, gust squalls, precipitation probability, and storm risk.
  - **Ocean Agent**: Analyzes sea surface temperature, chlorophyll thermal gradients, significant wave height, and swell period.
  - **Geospatial Agent**: Validates coordinates, evaluates distances to nearest ports, and checks navigation safety against marine protected areas and restricted fairways.
  - **Marine Knowledge Agent**: Connects directly to the Phase 2 Chroma vector store to retrieve safety SOPs and fishing regulations.
  - **Risk Assessment Agent**: Multi-factor reasoning synthesizing wave, wind, storm, and zone boundaries into an overall risk level (`LOW`, `MEDIUM`, `HIGH`).
  - **Response Synthesizer**: Formulates structured, actionable natural language recommendations.
- [x] **Frontend Multi-Agent Integration**:
  - Prominent risk level indicator badges (`LOW`, `MEDIUM`, `HIGH`).
  - Context badges for extracted location and time (e.g., `📍 Mumbai`, `⏱️ Tomorrow Morning`).
  - Multi-agent evidence & telemetry condition list.
  - Collapsible Agent Workflow Trace showing per-agent execution status and sub-task details.

---

## 9. Phase 4 Features — Real Marine Data + Geo-Spatial Intelligence
- [x] **MarineDataGateway**:
  - Centralized singleton managing all external requests and local spatial caches.
  - Configurable TTL caching (Weather: 600s, Ocean: 1800s, PFZ: 3600s, Geospatial: 86400s).
  - Normalized Pydantic models (`NormalizedWeather`, `NormalizedOcean`, `NormalizedPFZ`, `NormalizedGeospatial`).
  - Transparent data status tagging (`external`, `verified`, `demo`, `not_configured`, `unavailable`).
  - Resilient fallback chain with offline demo support (`MARINEX_DEMO_MODE=true`).
- [x] **Live Meteorological & Oceanographic Feeds**:
  - **Open-Meteo Weather API**: Current & hourly wind speed, wind gusts, precipitation, cloud cover.
  - **Open-Meteo Marine API**: Wave height, wave direction, wave period, swell height, swell period, SST.
  - Zero-key, rate-limit compliant public endpoints with live external connectivity.
- [x] **INCOIS Potential Fishing Zones (PFZ)**:
  - Sector models covering Mumbai, Alibaug, Chennai, Pulicat, and Kochi.
  - SST thermal fronts and Chlorophyll-a gradient evaluation.
  - GeoJSON FeatureCollection endpoint at `/api/data-sources/pfz`.
- [x] **ISRO MOSDAC Satellite EO Architecture**:
  - Dataset registry (`backend/config/datasets.yaml`) for Oceansat-3 OCM-3, SSTM, and INSAT-3D products.
  - Graceful guardrail: Transparently reports `not_configured` when credentials are omitted.
- [x] **Geo-Spatial Intelligence Engine**:
  - WGS84 GeoJSON layers for 10 major Indian ports, coastline, restricted naval zones, marine protected areas, and navigational hazards.
  - Pure Python spatial math: Great-circle Haversine distance, Ray-casting point-in-polygon geofencing, and proximity hazard buffers.
  - PostgreSQL / PostGIS migration readiness.
- [x] **Frontend Data Feeds & Map Controls**:
  - "Data Feeds" popover in the navigation header displaying live status and latency for all 6 data sources.
  - Interactive Leaflet layer toggles for PFZ zones, restricted boundaries, and hazard areas.
  - Multi-agent map data injection (`map_data` in `MarineAgentState`) for dynamic viewport synchronization.

---

## 10. Project Structure

```
SIH_57/
├── .env.example                     # Environment template (includes Phase 4 vars)
├── .gitignore                       # Git ignore rules
├── README.md                        # Project documentation
├── data/
│   ├── documents/                   # Marine documents corpus (.pdf, .docx, .txt)
│   └── geospatial/                  # Authoritative WGS84 GeoJSON layers
│       ├── ports.geojson            # Major Indian ports with depths and VHF
│       ├── coastline.geojson        # High-res peninsular coastline
│       ├── restricted_zones.geojson # Naval & offshore security perimeters
│       ├── protected_areas.geojson  # Marine Protected Areas & sanctuaries
│       └── hazard_zones.geojson     # Navigational shoals, reefs, wrecks
├── docs/
│   ├── architecture-phase-2.md      # Phase 2 RAG specification
│   ├── architecture-phase-3.md      # Phase 3 LangGraph multi-agent specification
│   ├── architecture-phase-4.md      # Phase 4 Real Data & Geospatial specification
│   ├── real-data-sources.md         # Data provider details & schemas
│   ├── marine-data-gateway.md       # Gateway, caching & fallback mechanics
│   ├── geospatial-architecture.md   # Spatial reasoning algorithms & PostGIS schema
│   └── phase-4-setup.md             # Phase 4 step-by-step setup guide
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI application entry point
│   │   ├── config.py                # Central configuration & settings
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── health.py        # /api/health
│   │   │       ├── chat.py          # /api/chat (LangGraph multi-agent)
│   │   │       ├── marine.py        # /api/marine/* (conditions, zones, alerts)
│   │   │       ├── rag.py           # /api/rag/* (status, ingest, query, upload)
│   │   │       ├── agent.py         # /api/agent/* (LangGraph multi-agent chat)
│   │   │       └── data_sources.py  # /api/data-sources/* (status, pfz, geospatial)
│   │   ├── marine_gateway/          # Centralized Ingestion & Cache Hub
│   │   │   ├── gateway.py           # MarineDataGateway singleton
│   │   │   ├── cache.py             # MarineCache with TTLs
│   │   │   ├── health.py            # Consolidated health check engine
│   │   │   └── models.py            # Normalized Pydantic models
│   │   ├── data_sources/            # Pluggable data provider modules
│   │   │   ├── base.py              # DataSource base class & DataStatus enum
│   │   │   ├── weather/             # Open-Meteo Weather integration
│   │   │   ├── ocean/               # Open-Meteo Marine integration
│   │   │   ├── pfz/                 # INCOIS PFZ sector models & GeoJSON
│   │   │   ├── satellite/           # ISRO MOSDAC architecture & guardrails
│   │   │   └── geospatial/          # Spatial reasoning & GeoJSON service
│   │   ├── graph/                   # LangGraph StateGraph engine
│   │   │   ├── state.py             # MarineAgentState with map_data
│   │   │   ├── nodes.py             # Agent node execution logic
│   │   │   ├── edges.py             # Conditional routing policy
│   │   │   └── workflow.py          # Compiled StateGraph workflow
│   │   ├── agents/                  # 7 specialized marine agents
│   │   ├── tools/                   # Agent tools (routed through gateway)
│   │   └── rag/                     # LangChain + Chroma RAG pipeline
│   ├── config/
│   │   └── datasets.yaml            # Earth Observation dataset registry
│   ├── storage/
│   │   └── chroma/                  # Persistent Chroma vector database
│   ├── tests/
│   │   ├── test_rag.py              # RAG pipeline tests
│   │   ├── test_agents.py           # Multi-agent unit tests
│   │   ├── test_graph.py            # LangGraph workflow integration tests
│   │   └── test_data_sources.py     # Phase 4 Gateway & Provider tests
│   └── requirements.txt             # Python dependencies
└── frontend/
    ├── package.json                 # Next.js dependencies & scripts
    ├── tsconfig.json                # TypeScript configuration
    ├── tailwind.config.ts           # Tailwind CSS marine-tech theme
    └── src/
        ├── app/
        │   ├── layout.tsx           # Root layout
        │   ├── page.tsx             # Main dashboard with Data Feeds & Map Controls
        │   └── globals.css          # Global styles & Leaflet overrides
        ├── components/
        │   ├── layout/Header.tsx    # Header with Data Feeds popover
        │   ├── map/MarineMap.tsx    # Leaflet map with PFZ/Restricted/Hazard layer toggles
        │   ├── chat/                # Chat with risk badges, evidence, trace, map sync
        │   └── ...
        ├── types/marine.ts          # TypeScript interfaces (including data feeds)
        └── services/api.ts          # API client with data-sources endpoints
```

---

## 11. Quick Start Guide

### Prerequisites
- **Node.js**: v18.0.0+ (Tested on Node v25.6.1)
- **Python**: 3.10+ (Tested on Python 3.13.15)
- **Git**

### 1. Setup Backend
```bash
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Setup Frontend
```bash
cd frontend
npm install
```

### 3. Run Application
In terminal 1 (Backend):
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

In terminal 2 (Frontend):
```bash
cd frontend
npm run dev
```

Open `http://localhost:3000` in your browser.

---

## 12. Automated Test Suite

MARINEX AI includes 28 comprehensive automated tests across all 4 phases:

```bash
cd backend
pytest tests/ -v
```

### Test Breakdown:
- **`tests/test_data_sources.py`**: Weather API live connection, Marine API live connection, PFZ sectors, MOSDAC guardrail, Geospatial proximity & geofencing, MarineDataGateway TTL caching, Health check aggregation.
- **`tests/test_agents.py`**: Unit tests for Planner, Weather, Ocean, Geospatial, Risk, and Synthesizer agents.
- **`tests/test_graph.py`**: LangGraph execution paths, conditional routing, and the official Mumbai fishing safety demo query.
- **`tests/test_rag.py`**: Document loaders, splitter, vector store, and grounded retrieval.

---

## 13. Roadmap

| Phase | Milestone | Status | Key Deliverables |
|---|---|---|---|
| **Phase 1** | **Foundation & UI** | ✅ Completed | Next.js + Leaflet dashboard, FastAPI skeleton, centralized mock data, marine UI components. |
| **Phase 2** | **LangChain + RAG** | ✅ Completed | Ingestion of marine advisories & guidelines, Chroma vector store, semantic retriever, source citations. |
| **Phase 3** | **LangGraph Multi-Agent** | ✅ Completed | LangGraph StateGraph, 7 collaborative agents, domain tools, conditional routing, risk assessment, execution trace UI. |
| **Phase 4** | **Real Marine Data + Geo-Spatial** | ✅ Completed | Open-Meteo Weather & Marine feeds, MarineDataGateway with TTL caching, INCOIS PFZ sectors, MOSDAC architecture, GeoJSON/PostGIS spatial engine, Data Feeds UI, layer controls. |
| **Phase 5** | **Advanced Geospatial & Optimization** | ⏳ Planned | Dynamic vessel route optimization, automated vernacular voice generation, satellite imagery overlays. |

---

## License
Licensed under the [MIT License](LICENSE). Built for the Smart India Hackathon (SIH 57) under problem statement **ORCA**.
