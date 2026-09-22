# MARINEX AI — Marine Data Gateway

## Overview
The **MarineDataGateway** (`backend/app/marine_gateway/gateway.py`) is the centralized data access and normalization layer for **MARINEX AI**. It provides an abstraction between external APIs (Open-Meteo, MOSDAC, INCOIS), localized geospatial files, in-memory caching, and downstream LangGraph AI agents.

---

## 1. Architectural Motivation

Prior to Phase 4, marine tools directly accessed mock services. In a production multi-agent system, multiple agents (Weather Agent, Ocean Agent, Geospatial Agent, Risk Agent) frequently request identical or overlapping spatial-temporal data points during a single workflow execution.

Direct external API calls from each agent introduce:
- Redundant network latency (300ms–1500ms per agent).
- Unnecessary rate-limit consumption on external providers.
- Inconsistent data states if conditions shift between agent steps.
- Fragile error handling if one provider experiences transient failures.

**MarineDataGateway resolves this through:**
1. **Single Entry Point**: All domain tools route through the gateway.
2. **Deterministic Normalization**: Standardized Pydantic schemas regardless of raw provider format.
3. **In-Memory Caching with TTL**: Sub-millisecond response times for subsequent queries.
4. **Resilient Fallback Hierarchy**: Live external $\rightarrow$ cached $\rightarrow$ demo fallback $\rightarrow$ error handling.
5. **Data Provenance Transparency**: Every record contains an explicit `data_status` tag.

---

## 2. In-Memory Cache with Configurable TTLs

The gateway utilizes `MarineCache` (`backend/app/marine_gateway/cache.py`), an in-memory dictionary-backed cache with millisecond timestamps and automatic TTL invalidation:

| Data Type | Cache Key Format | Default TTL | Rationale |
|---|---|---|---|
| **Weather** | `weather:{lat_2dec}:{lon_2dec}` | 600 seconds (10 min) | Rapidly shifting atmospheric and squall fronts. |
| **Ocean** | `ocean:{lat_2dec}:{lon_2dec}` | 1800 seconds (30 min) | Ocean swell and wave regimes change over hours. |
| **PFZ** | `pfz:all` / `pfz:{lat_2dec}:{lon_2dec}` | 3600 seconds (60 min) | Thermal fronts persist over multiple hours to days. |
| **Geospatial** | `geo:all` / `geo:ports` / ... | 86400 seconds (24 hr) | Navigational boundaries and port coordinates are static. |

*Coordinates are rounded to 2 decimal places (~1.1 km precision) to maximize cache hit rates for adjacent queries.*

---

## 3. Normalized Data Models

Defined in `backend/app/marine_gateway/models.py`:

```python
class NormalizedWeather(BaseModel):
    location: str
    latitude: float
    longitude: float
    timestamp: str
    temperature_c: float
    wind_speed_knots: float
    wind_direction_deg: float
    wind_gusts_knots: float
    precipitation_mm: float
    cloud_cover_pct: int
    weather_description: str
    data_status: DataStatus  # external | verified | demo | unavailable
    source: str
    cached: bool = False

class NormalizedOcean(BaseModel):
    location: str
    latitude: float
    longitude: float
    timestamp: str
    wave_height_m: float
    wave_period_s: float
    wave_direction_deg: float
    swell_wave_height_m: float
    swell_period_s: float
    sea_surface_temperature_c: float
    sea_state: str  # calm | smooth | slight | moderate | rough | very_rough
    data_status: DataStatus
    source: str
    cached: bool = False
```

---

## 4. Resilience and Fallback Chain

When an agent requests weather or ocean conditions:
1. **Cache Check**: If a non-expired entry exists in `MarineCache`, return it immediately with `cached: true`.
2. **Live External Fetch**: If cache misses and `MARINEX_DEMO_MODE=false`, query the live external API (e.g. Open-Meteo).
3. **Cache Ingestion**: On successful external fetch, store in cache with `data_status: "external"`.
4. **Demo Mode / Error Fallback**: If external call fails, times out, or `MARINEX_DEMO_MODE=true`:
   - Log warning.
   - Return deterministic fallback model with `data_status: "demo"`.
   - Never crash the agent workflow.

---

## 5. Health Check Aggregation

The gateway exposes a consolidated health check endpoint at `/api/data-sources/status`:

```json
{
  "timestamp": "2026-09-22T08:15:00Z",
  "demo_mode": false,
  "sources": {
    "weather": {
      "name": "Open-Meteo Weather API",
      "status": "external",
      "latency_ms": 284,
      "message": "Connected to Open-Meteo Weather API (external live data)"
    },
    "ocean": {
      "name": "Open-Meteo Marine API",
      "status": "external",
      "latency_ms": 312,
      "message": "Connected to Open-Meteo Marine API (external live data)"
    },
    "pfz": {
      "name": "INCOIS Potential Fishing Zones",
      "status": "verified",
      "latency_ms": 1,
      "message": "Loaded 5 PFZ sector advisories (verified baseline)"
    },
    "satellite": {
      "name": "ISRO MOSDAC Satellite EO",
      "status": "not_configured",
      "latency_ms": 0,
      "message": "MOSDAC credentials not configured (MOSDAC_USERNAME, MOSDAC_PASSWORD)"
    },
    "geospatial": {
      "name": "Local GeoJSON Spatial Data",
      "status": "verified",
      "latency_ms": 1,
      "message": "5 GeoJSON layers loaded (verified baseline)"
    },
    "postgis": {
      "name": "PostgreSQL / PostGIS",
      "status": "not_configured",
      "latency_ms": 0,
      "message": "PostGIS database not configured in DATABASE_URL"
    }
  }
}
```

---

## 6. Programmatic Gateway Usage

```python
from app.marine_gateway import get_marine_gateway

gateway = get_marine_gateway()

# Fetch normalized weather
weather = await gateway.get_weather(18.922, 72.8347, location_name="Mumbai")
print(f"Wind: {weather.wind_speed_knots} kts, Status: {weather.data_status}")

# Fetch normalized ocean
ocean = await gateway.get_ocean(18.922, 72.8347, location_name="Mumbai")
print(f"Wave Height: {ocean.wave_height_m} m, Status: {ocean.data_status}")

# Check restricted zones
geo = await gateway.check_restricted_zones(18.922, 72.8347)
print(f"In Restricted Zone: {geo['is_restricted']}")
```
