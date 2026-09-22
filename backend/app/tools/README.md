# Specialized Agent Tools Architecture

## Overview
Agents in the MARINEX AI ecosystem interact with databases, external APIs, and spatial models through strongly-typed tools equipped with Pydantic schemas.

---

## Tool Catalog

### 1. `get_incois_wave_forecast(lat: float, lon: float, hours_ahead: int = 24)`
- **Agent**: Ocean Agent
- **Description**: Queries significant wave heights, swell direction, and wave periods from INCOIS numerical ocean forecast models.

### 2. `get_mosdac_pfz_contours(bbox: List[float], min_confidence: float = 0.7)`
- **Agent**: Satellite / PFZ Agent
- **Description**: Extracts SST thermal front lines and chlorophyll-a high-concentration convergence zones from ISRO MOSDAC daily products.

### 3. `check_postgis_geofence(latitude: float, longitude: float)`
- **Agent**: Geospatial Agent
- **Description**: Executes `ST_Intersects` on maritime boundary layers (MPAs, international boundaries, port security fairways).

### 4. `query_marine_rag(query: str, coastal_region: str, top_k: int = 4)`
- **Agent**: Marine Advisory Agent
- **Description**: Searches embedded marine advisories, disaster guidelines, and fisheries regulations using pgvector hybrid search.

### 5. `compute_navigation_route(origin: Coordinate, destination: Coordinate, avoid_hazards: bool = True)`
- **Agent**: Geospatial & Risk Agents
- **Description**: Calculates maritime waypoint route avoiding shallow shoals, severe wave hazards, and restricted zones.
