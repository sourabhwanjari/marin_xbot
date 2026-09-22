# MARINEX AI — Phase 4 Architecture: Real Marine Data Integration + Geo-Spatial Intelligence

## Overview
**MARINEX AI** (Problem Statement: *ORCA — Marine EcOsystem Reasoning with Collaborative Agents*) reaches **Phase 4**, introducing production-grade real marine data acquisition, normalized data gateway caching, geospatial intelligence, and transparent data provenance.

Phase 4 integrates live meteorological and oceanographic feeds, INCOIS Potential Fishing Zone (PFZ) models, ISRO MOSDAC satellite Earth Observation registry, and geospatial boundary intelligence into the LangGraph multi-agent orchestrator.

---

## 1. Phase 4 High-Level Architecture

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

## 2. Core Architectural Pillars

### Pillar 1: MarineDataGateway Pattern
All external communication flows strictly through `MarineDataGateway` (`backend/app/marine_gateway/gateway.py`):
- **Singleton Ingestion Point**: Eliminates direct API calls from individual agents or route handlers.
- **Normalized Pydantic Schemas**: Returns strongly typed models (`NormalizedWeather`, `NormalizedOcean`, `NormalizedPFZ`, `NormalizedGeospatial`).
- **Configurable TTL Caching**:
  - Weather: 10 minutes (600s)
  - Ocean: 30 minutes (1800s)
  - PFZ: 60 minutes (3600s)
  - Geospatial: 24 hours (86400s)
- **Transparent Data Status**: Every response is tagged with an immutable provenance label:
  - `external`: Real data fetched from a live public or authenticated API.
  - `verified`: Curated, authoritative baseline data (e.g., GeoJSON port coordinates, official marine boundaries).
  - `demo`: Synthetic fallback data utilized during offline mode or external API outages.
  - `not_configured`: Service requires credentials not yet supplied (e.g., MOSDAC).
  - `unavailable`: External provider returned an error or timed out.

### Pillar 2: Real Data Ingestion
- **Weather (`WeatherService`)**:
  - Provider: Open-Meteo Weather API (`https://api.open-meteo.com/v1/forecast`).
  - Capabilities: Hourly & current 10m wind speed, wind gusts, precipitation, cloud cover, air temperature.
  - Key-free, rate-limit compliant, high reliability.
- **Ocean (`OceanService`)**:
  - Provider: Open-Meteo Marine API (`https://marine-api.open-meteo.com/v1/marine`).
  - Capabilities: Significant wave height, wave direction, wave period, swell wave height, swell period, sea surface temperature.
- **PFZ (`PFZService`)**:
  - Structured after INCOIS Potential Fishing Zone advisories.
  - Evaluates SST thermal fronts (optimal: 26.5°C–29.5°C) and Chlorophyll-a gradients (0.35–1.2 mg/m³).
  - Provides geo-referenced zones for major Indian fishing sectors (Mumbai, Alibaug, Chennai, Pulicat, Kochi).
- **Satellite (`MosdacService`)**:
  - Architecture ready for ISRO MOSDAC Earth Observation products (Oceansat-3 OCM-3, INSAT-3D/3DR).
  - Guardrail: When credentials (`MOSDAC_USERNAME`, `MOSDAC_PASSWORD`) are not configured, returns clear status `not_configured` without failing or fabricating telemetry.

### Pillar 3: Geo-Spatial Intelligence Engine
- **Spatial Reasoning Engine (`GeospatialService`)**:
  - Haversine great-circle distance calculations.
  - Point-in-polygon ray-casting algorithm for custom geofencing.
  - Spatial buffer queries for port proximity, navigational hazards, and Marine Protected Areas (MPAs).
- **Authoritative GeoJSON Layers**:
  - Major Indian Ports: Mumbai, JNPT, Chennai, Kochi, Visakhapatnam, Paradip, Mormugao, Kandla, Tuticorin, Mangalore.
  - Indian Coastline vector geometry.
  - Restricted Security Zones (naval bases, shipping lanes).
  - Marine Protected Areas (Gulf of Mannar, Sundarbans, Gahirmatha).
  - Hazard Zones (shallow shoals, submerged wrecks, high-current reefs).
- **PostGIS Compatibility**: Fully compatible with PostgreSQL/PostGIS spatial SQL; operates autonomously via GeoJSON/shapely algorithms in standalone mode.

### Pillar 4: LangGraph Agent Integration
The Phase 3 multi-agent graph was enhanced to seamlessly utilize the Phase 4 gateway:
- **`WeatherAgent`**: Ingests `NormalizedWeather`, evaluates squall risks, and outputs structured evidence with provenance.
- **`OceanAgent`**: Ingests `NormalizedOcean`, checks sea-state roughness, swell hazard, and SST fronts.
- **`GeospatialAgent`**: Performs boundary intersection and proximity checks, injecting GeoJSON features into the state.
- **`MarineAgentState`**: Propagates `map_data` (GeoJSON FeatureCollections) directly to the frontend chat UI for dynamic map synchronization.

---

## 3. Data Integrity & Provenance Guarantee

MARINEX AI enforces zero-hallucination policies for marine data:
1. **Never Claim Mock Data is Live**: Synthetic data is explicitly tagged `data_status: "demo"`.
2. **Never Fabricate Credentials**: MOSDAC and PostGIS status is reported as `not_configured` when environment variables are omitted.
3. **No Frontend Secret Exposure**: API keys and credentials are strictly encapsulated within backend services.
4. **Resilient Offline Mode**: Setting `MARINEX_DEMO_MODE=true` activates deterministic, safe demo responses for demonstrations and CI/CD without network access.

---

## 4. Summary of Phase 4 Endpoints

| Endpoint | Method | Description | Data Status |
|---|---|---|---|
| `/api/data-sources/status` | `GET` | Health & connectivity across all 6 data providers | `external` / `verified` / `not_configured` |
| `/api/data-sources/pfz` | `GET` | GeoJSON FeatureCollection of active PFZ advisories | `verified` / `demo` |
| `/api/data-sources/geospatial` | `GET` | Layers for ports, restricted zones, MPAs, hazards | `verified` |
| `/api/agent/chat` | `POST` | LangGraph multi-agent decision support with map data | `external` / `verified` |
