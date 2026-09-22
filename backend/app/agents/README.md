# Collaborative Agent Architecture (ORCA Vision)

## Overview
In the **ORCA** (*Marine EcOsystem Reasoning with Collaborative Agents*) paradigm, no single monolithic model attempts to solve end-to-end marine queries. Instead, a multi-agent hierarchy coordinates specialized agents to retrieve, process, reason over, and synthesize multi-modal marine data.

```
                  ┌──────────────────────┐
                  │     User Query       │
                  └──────────┬───────────┘
                             │
                  ┌──────────▼───────────┐
                  │   Intent Classifier  │
                  └──────────┬───────────┘
                             │
                  ┌──────────▼───────────┐
                  │ LangGraph Supervisor │
                  │   (Planner Agent)    │
                  └──────────┬───────────┘
                             │
     ┌───────────────┬───────┴───────┬───────────────┬───────────────┐
     │               │               │               │               │
┌────▼────┐    ┌─────▼───┐     ┌─────▼─────┐   ┌─────▼────┐    ┌─────▼────┐
│ Weather │    │  Ocean  │     │ Satellite │   │Geospatial│    │ Advisory │
│  Agent  │    │  Agent  │     │/PFZ Agent │   │  Agent   │    │  Agent   │
└────┬────┘    └─────┬───┘     └─────┬─────┘   └─────┬────┘    └─────┬────┘
     │               │               │               │               │
     └───────────────┼───────────────┴───────────────┼───────────────┘
                             │
                  ┌──────────▼───────────┐
                  │Risk Assessment Agent │
                  └──────────┬───────────┘
                             │
                  ┌──────────▼───────────┐
                  │  Response Synthesizer│
                  │   (Reporting Agent)  │
                  └──────────┬───────────┘
                             │
                  ┌──────────▼───────────┐
                  │ Final Actionable UI  │
                  │ (Text + Map Layers)  │
                  └──────────────────────┘
```

---

## 1. The 7 Specialized Agents

### 1. Weather Agent
- **Domain**: Marine meteorology, wind vector grids, squall lines, precipitation, and barometric trends.
- **Data Sources**: IMD (India Meteorological Department), ECMWF, GFS numerical weather forecasts.
- **Capabilities**: Predicts wind gusts, squalls, visibility hazards, and cyclonic progression.

### 2. Ocean Agent
- **Domain**: Ocean physics, hydrodynamic models, wave spectra, and tidal dynamics.
- **Data Sources**: INCOIS (Indian National Centre for Ocean Information Services), SWAN, WAVEWATCH III models.
- **Capabilities**: Evaluates significant wave heights, swell period, surface current drift, and tidal peak timing.

### 3. Satellite / PFZ Agent
- **Domain**: Earth Observation (EO) satellite telemetry.
- **Data Sources**: MOSDAC / ISRO (INSAT-3DR, Oceansat-3 OCM-3 / SSTM), Copernicus Sentinel-3.
- **Capabilities**: Computes Sea Surface Temperature (SST) gradients, thermal front delineation, Chlorophyll-a bloom detection, and Potential Fishing Zone (PFZ) bounding boxes.

### 4. Geospatial Agent
- **Domain**: Spatial-temporal GIS operations, distance calculations, coordinate projection, and geofencing.
- **Data Sources**: PostGIS, OGC WMS/WFS, OpenStreetMap coastlines, Bathymetric charts (GEBCO).
- **Capabilities**: Calculates nearest safe harbor, vessel transit distances, and intersects vessel tracks with Marine Protected Areas (MPAs) or restricted naval fairways.

### 5. Marine Advisory Agent
- **Domain**: Government advisories, regulatory notices, and NAVTEX emergency broadcasts.
- **Data Sources**: INCOIS Ocean State alerts, Disaster Management Authorities, Indian Coast Guard bulletins.
- **Capabilities**: Translates official regulatory warnings into clear, multi-lingual vernacular advisories for artisanal and commercial fishermen.

### 6. Risk Assessment Agent
- **Domain**: Multi-factor probabilistic risk synthesis.
- **Inputs**: Outputs from Weather, Ocean, Satellite, and Geospatial agents.
- **Capabilities**: Computes composite Marine Risk Index (e.g. LOW, MEDIUM, CRITICAL) based on vessel type, swell height, distance from shore, and thunderstorm proximity.

### 7. Response / Reporting Agent
- **Domain**: Natural language generation, structured payload formatting, and visual card assembly.
- **Capabilities**: Synthesizes intermediate evidence into clear, actionable advice (e.g., "Safe to operate until 14:00 within 12 NM"), generating map layer toggles and structured JSON for the frontend.

---

## Phase 1 Status
In Phase 1, all agent reasoning is simulated via `MockChatService` and `MockMarineService` to establish the API contracts and frontend UX. Real agent nodes will be instantiated using LangGraph in Phase 3.
