# MARINEX AI — Phase 4 Setup & Verification Guide

## Overview
This guide explains how to configure, run, and verify **Phase 4: Real Marine Data Integration + Geo-spatial Intelligence** on your local machine.

---

## 1. Environment Configuration

Copy `.env.example` to `.env` in the root directory (or in `backend/`):

```bash
cp .env.example .env
```

### Key Phase 4 Variables
```bash
# --- External Marine & Remote Sensing Data Providers ---
# Weather & Ocean (Open-Meteo): Works immediately without API keys.
WEATHER_CACHE_TTL=600       # 10 minutes cache for weather
OCEAN_CACHE_TTL=1800        # 30 minutes cache for ocean
PFZ_CACHE_TTL=3600          # 1 hour cache for PFZ advisories

# Satellite EO (ISRO MOSDAC)
# Leave blank to test graceful "not_configured" guardrail
MOSDAC_USERNAME=
MOSDAC_PASSWORD=

# Demo Mode Fallback
# Set to 'false' to use live Open-Meteo external APIs
# Set to 'true' to force offline synthetic data fallback
MARINEX_DEMO_MODE=false
```

---

## 2. Running Backend and Frontend

### Step 1: Start Backend (FastAPI)
From the project root:
```bash
cd backend
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

Verify backend health:
- `http://localhost:8000/api/health`
- `http://localhost:8000/api/data-sources/status`

### Step 2: Start Frontend (Next.js)
In a new terminal from the project root:
```bash
cd frontend
npm run dev
```

Open `http://localhost:3000` in your browser.

---

## 3. Verifying Phase 4 Features

### 1. Data Feeds Popover
- Click the **"Data Feeds"** button in the top navigation header.
- Verify status indicators:
  - **Weather (Open-Meteo)**: `LIVE` (Green pulse)
  - **Ocean (Open-Meteo)**: `LIVE` (Green pulse)
  - **PFZ (INCOIS)**: `AVAILABLE` (Cyan)
  - **Satellite (MOSDAC)**: `NOT CONFIGURED` (Amber)
  - **Geospatial (GeoJSON)**: `AVAILABLE` (Cyan)
  - **PostGIS**: `NOT CONFIGURED` (Amber)

### 2. Map Layer Toggles
- Locate the layer control panel on the top-right of the marine map.
- Toggle **PFZ Zones**: Notice green polygon zones along the Indian coast with SST and Chlorophyll popups.
- Toggle **Restricted Zones**: Notice red hatched naval and offshore perimeters.
- Toggle **Hazards**: Notice amber warning circles for reefs, shoals, and wrecks.

### 3. Real Multi-Agent Queries
Try these queries in the chat interface:
1. **Weather Query**:
   > *"What is the current wind and squall risk offshore Mumbai?"*
   - Verify that the Weather Agent fetches live Open-Meteo telemetry with `data_status: "external"`.
2. **Ocean Query**:
   > *"Check sea conditions and wave height near Chennai."*
   - Verify that the Ocean Agent reports live wave height, swell period, and sea-state classification.
3. **Safety & PFZ Multi-Agent Query**:
   > *"Can we go fishing 15 km off Kochi tomorrow morning? Are there any PFZ zones or restricted areas?"*
   - Verify that the Planner coordinates Weather, Ocean, Geospatial, and Risk agents, evaluates boundary intersections, and provides an actionable recommendation.

---

## 4. Running Automated Tests

Run the comprehensive test suite to verify all Phase 1–4 capabilities:

```bash
# Run Phase 4 Data Sources & Gateway tests
pytest tests/test_data_sources.py -v

# Run entire test suite (Phase 1, 2, 3, 4)
pytest tests/ -v
```

Expected result: **28 passed in ~15 seconds**.
