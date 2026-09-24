# MARINEX AI — Phase 5B Documentation

## Real Marine Data Provider Integration

This document describes the architectural implementation and operational usage of **Phase 5B: Real Marine Data Provider Integration** for the **MARINEX AI** platform.

---

## 1. Architectural Overview

Phase 5B connects the existing **Marine Data Gateway** (`MarineDataGateway` & `ProviderRegistry`) directly to real external marine data providers, while strictly maintaining clean provider abstraction, normalization into typed domain models, provenance evidence tracking, freshness metadata guarantees, and graceful degradation.

```
User Query (Chatbot or API)
  │
  ▼
LangGraph Multi-Agent Orchestrator
  │
  ├─► WeatherAgent ───────► marine_gateway.get_weather()
  ├─► OceanAgent ─────────► marine_gateway.get_ocean_conditions()
  ├─► GeospatialAgent ────► marine_gateway.get_pfz() / get_geospatial_context()
  └─► SatelliteAgent ─────► marine_gateway.get_satellite_data()
                                │
                                ▼
                       Marine Data Gateway
                                │
                     ┌──────────┴──────────┐
                     │ Cache HIT?          │
                     │ (Configurable TTLs) │
                     └──────────┬──────────┘
                                │ Cache MISS
                                ▼
                        Provider Registry
    ┌───────────────────────────┼───────────────────────────┐
    ▼                           ▼                           ▼
IMD Weather Client      INCOIS Ocean & PFZ          MOSDAC Satellite
(AWS / Coastal Bul.)    (Hydrodynamic & PFZ)        (Oceansat-3 Granules)
    │                           │                           │
    └───────────────────────────┼───────────────────────────┘
                                ▼
                    Normalized MarineDataResponse
    ┌───────────────────────────────────────────────────────┐
    │  • Status: CONNECTED / NOT_CONFIGURED / UNAVAILABLE   │
    │  • Freshness: observed_at, retrieved_at, valid_until  │
    │  • Evidence: Provenance, confidence, citation URL     │
    │  • Zero Hallucination: None when unconfigured         │
    └───────────────────────────────────────────────────────┘
                                │
                                ▼
                 Risk Engine & Response Synthesizer
                                │
                                ▼
                      User Chatbot & Marine Map
```

---

## 2. Integrated Data Providers

| Capability | Provider | Adapter Class | Dedicated Client | Primary Dataset | Default State |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **WEATHER** | **India Meteorological Department (IMD)** | `IMDWeatherProvider` | `IMDClient` | `IMD-Coastal-AWS` | `NOT_CONFIGURED` (Fallback to Open-Meteo) |
| **OCEAN** | **INCOIS (Ocean State)** | `INCOISOceanProvider` | `INCOISClient` | `INCOIS-Wave-Hydrodynamic` | `NOT_CONFIGURED` (Fallback to Copernicus/Open-Meteo) |
| **PFZ** | **INCOIS (Potential Fishing Zones)** | `INCOISPFZProvider` | `INCOISClient` | `INCOIS-PFZ-Live` / `INCOIS-PFZ-Reference` | `CONNECTED` (Verified Reference Mode active) |
| **SATELLITE** | **ISRO MOSDAC** | `MOSDACSatelliteProvider`| `MOSDACClient` | `OS3_SST_L3` / `INSAT-3DR` | `NOT_CONFIGURED` (Strict disclaimer) |
| **GEOSPATIAL**| **Maritime GIS / PostGIS** | `GISProvider` | `geospatial_service` | `Indian-Maritime-Boundaries-EEZ` | `CONNECTED` (Deterministic spatial computation) |

---

## 3. Provider Status API Contract

### Endpoint: `GET /api/marine/providers/status`

Returns live connectivity and configuration status across all primary providers without exposing credentials:

```json
{
  "imd": {
    "status": "NOT_CONFIGURED"
  },
  "incois_ocean": {
    "status": "NOT_CONFIGURED"
  },
  "incois_pfz": {
    "status": "CONNECTED"
  },
  "mosdac": {
    "status": "NOT_CONFIGURED"
  },
  "postgis": {
    "status": "CONNECTED"
  }
}
```

### Possible Provider Statuses (`ProviderStatus` Enum):
- `CONNECTED`: Configured, enabled, and responding normally (or verified reference fallback operational).
- `NOT_CONFIGURED`: Missing required credentials/endpoints in `.env`. Never hallucinates live data.
- `UNAVAILABLE`: Configured endpoint timed out (HTTP 504 / timeout) or returned network errors.
- `ERROR`: Unexpected server or data format error.
- `DEGRADED`: Partial capability degradation or reduced precision.

---

## 4. Freshness and Evidence Guarantees

Every normalized response from `MarineDataGateway` includes explicit freshness timestamps and audit evidence:

### Freshness Metadata Fields
- `observed_at`: ISO 8601 timestamp of sensor observation or `"UNAVAILABLE"`.
- `retrieved_at`: ISO 8601 timestamp of gateway retrieval from provider.
- `valid_from`: Start of temporal validity window.
- `valid_until`: Forecast expiry or bulletin validity deadline.

### Provenance Evidence Fields (`MarineEvidence`)
- `source`: Issuing authority (e.g. `India Meteorological Department`, `INCOIS Hyderabad`, `ISRO MOSDAC`).
- `provider`: Provider adapter name.
- `dataset`: Exact dataset catalog identifier.
- `retrieved_at`: Retrieval timestamp.
- `quality`: Telemetry confidence level (`HIGH`, `OPERATIONAL`, `VERIFIED`, `NOT_CONFIGURED`).
- `metadata`: Sensor station IDs, granule identifiers, and spatial calculation methods.

---

## 5. Configuration & Environment Variables

Add the following keys to your `backend/.env` file to enable live external data sources:

```bash
# IMD Settings
IMD_ENABLED=true
IMD_API_KEY=your_imd_api_token_here
IMD_BASE_URL=https://api.imd.gov.in

# INCOIS Settings
INCOIS_ENABLED=true
INCOIS_API_KEY=your_incois_token_here
INCOIS_BASE_URL=https://incois.gov.in/api
INCOIS_USERNAME=your_incois_username
INCOIS_PASSWORD=your_incois_password
INCOIS_PFZ_ENABLED=true

# ISRO MOSDAC Settings
MOSDAC_ENABLED=true
MOSDAC_USERNAME=your_mosdac_user
MOSDAC_PASSWORD=your_mosdac_pass
MOSDAC_DATASET_ID=OS3_SST_L3
MOSDAC_BASE_URL=https://api.mosdac.gov.in

# PostGIS Settings
POSTGIS_ENABLED=false
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=marinex_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_postgres_password

# Gateway Cache TTLs (Seconds)
WEATHER_CACHE_TTL=900     # 15 minutes
OCEAN_CACHE_TTL=1800      # 30 minutes
PFZ_CACHE_TTL=3600        # 1 hour
SATELLITE_CACHE_TTL=3600  # 1 hour
```

---

## 6. How to Run the Project Locally

### Prerequisites
- Python 3.11+ (Python 3.13 supported)
- Node.js 18+ and npm
- A valid `GOOGLE_API_KEY` in `backend/.env`

### Terminal 1: Backend (FastAPI on Port 8000)
```powershell
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
- API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Provider Status: [http://localhost:8000/api/marine/providers/status](http://localhost:8000/api/marine/providers/status)

### Terminal 2: Frontend (Next.js on Port 3000)
```powershell
cd frontend
npm run dev
```
- Web Application: [http://localhost:3000](http://localhost:3000)
- Interactive Map: [http://localhost:3000/map](http://localhost:3000/map)
- About & Architecture: [http://localhost:3000/about](http://localhost:3000/about)

---

## 7. Automated Test Suite

Run the full Phase 5B provider test suite:
```powershell
cd backend
python -m pytest tests/test_phase5b_real_providers.py -v
```
**Result: 18 passed in ~13s (100% success)**

Run the End-to-End Chatbot and Gateway Connection suite:
```powershell
cd backend
python -m pytest tests/test_gateway_connection_e2e.py -v
```
**Result: 14 passed in ~58s (100% success)**
