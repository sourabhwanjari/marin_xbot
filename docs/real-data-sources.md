# MARINEX AI — Real Marine Data Sources Specification

## Overview
Phase 4 connects **MARINEX AI** to real-world oceanographic, meteorological, and geospatial feeds while establishing an extensible architecture for satellite remote sensing and government marine data providers.

---

## 1. Open-Meteo Weather API (Live Meteorological Data)

### Provider Details
- **Provider**: Open-Meteo Free Weather API
- **Endpoint**: `https://api.open-meteo.com/v1/forecast`
- **Authentication**: Keyless, open-access, rate-limit compliant (10,000 requests/day).
- **Update Frequency**: Hourly numerical weather prediction (NWP) model runs.

### Queried Parameters
- `latitude`, `longitude`: Target coordinates (decimal degrees).
- `current`: `temperature_2m`, `relative_humidity_2m`, `precipitation`, `wind_speed_10m`, `wind_direction_10m`, `wind_gusts_10m`, `weather_code`, `cloud_cover`.
- `hourly`: `wind_speed_10m`, `wind_gusts_10m`, `precipitation_probability` (24-hour forecast).

### Normalization Pipeline
The raw JSON payload is parsed by `WeatherClient` and transformed into `NormalizedWeather`:
```json
{
  "location": "Mumbai",
  "latitude": 18.922,
  "longitude": 72.8347,
  "timestamp": "2026-09-22T08:00:00Z",
  "temperature_c": 28.4,
  "wind_speed_knots": 14.2,
  "wind_direction_deg": 240,
  "wind_gusts_knots": 18.5,
  "precipitation_mm": 0.0,
  "cloud_cover_pct": 35,
  "weather_description": "Partly cloudy",
  "data_status": "external",
  "source": "Open-Meteo Weather API",
  "cached": false
}
```

---

## 2. Open-Meteo Marine API (Live Ocean Dynamics)

### Provider Details
- **Provider**: Open-Meteo Marine API
- **Endpoint**: `https://marine-api.open-meteo.com/v1/marine`
- **Authentication**: Keyless, open-access.
- **Underlying Models**: ECMWF WAM, NOAA WaveWatch III.

### Queried Parameters
- `current`: `wave_height`, `wave_direction`, `wave_period`, `wind_wave_height`, `swell_wave_height`, `swell_wave_period`, `swell_wave_direction`, `sea_surface_temperature`.

### Normalization Pipeline
Transformed into `NormalizedOcean`:
```json
{
  "location": "Mumbai Offshore",
  "latitude": 18.922,
  "longitude": 72.8347,
  "timestamp": "2026-09-22T08:00:00Z",
  "wave_height_m": 1.2,
  "wave_period_s": 6.8,
  "wave_direction_deg": 250,
  "swell_wave_height_m": 0.9,
  "swell_period_s": 9.4,
  "sea_surface_temperature_c": 28.1,
  "sea_state": "moderate",
  "data_status": "external",
  "source": "Open-Meteo Marine API",
  "cached": false
}
```

---

## 3. INCOIS Potential Fishing Zone (PFZ) Advisories

### Background
The **Indian National Centre for Ocean Information Services (INCOIS)** generates Potential Fishing Zone (PFZ) advisories using multi-satellite data:
- **Sea Surface Temperature (SST)** from thermal infrared sensors (identifies oceanic fronts, eddies, and upwelling).
- **Ocean Color / Chlorophyll-a** from optical sensors (identifies phytoplankton blooms supporting fish trophic chains).

### Sector Registry
MARINEX AI maintains sector models across the Indian coastline:
1. **Mumbai Sector**: 18.85°N, 72.60°E (Depth: 35m, High confidence, target species: Mackerel, Sardine, Pomfret).
2. **Alibaug Offshore**: 18.60°N, 72.70°E (Depth: 28m, Medium confidence).
3. **Chennai Sector**: 13.15°N, 80.35°E (Depth: 45m, High confidence, target species: Tuna, Kingfish).
4. **Pulicat Reef**: 13.40°N, 80.40°E (Depth: 25m, Medium confidence).
5. **Kochi Sector**: 9.90°N, 76.10°E (Depth: 40m, High confidence, target species: Sardines, Squid).

### GeoJSON Output
Available at `/api/data-sources/pfz` as a standard GeoJSON `FeatureCollection` with polygon boundaries, center coordinates, bearing from port, distance (km), SST, chlorophyll, validity window, and confidence ratings.

---

## 4. ISRO MOSDAC Earth Observation Architecture

### Background
**Meteorological and Oceanographic Satellite Data Archival Centre (MOSDAC)** is ISRO's primary data portal for satellite Earth Observation data:
- **Oceansat-3 (EOS-06)**: Ocean Color Monitor (OCM-3), Sea Surface Temperature Monitor (SSTM), Ku-band Scatterometer.
- **INSAT-3D / INSAT-3DR**: Imager and sounder data for weather, cyclones, and atmospheric motion vectors.

### Guardrail Handling
- If `MOSDAC_USERNAME` or `MOSDAC_PASSWORD` environment variables are absent, the `MosdacService` returns:
```json
{
  "status": "not_configured",
  "message": "MOSDAC credentials not configured in environment (MOSDAC_USERNAME, MOSDAC_PASSWORD)",
  "provider": "ISRO MOSDAC",
  "datasets": [
    "Oceansat-3 OCM-3 Chlorophyll",
    "Oceansat-3 SSTM Sea Surface Temperature",
    "INSAT-3D Imager"
  ]
}
```
- This satisfies the strict hackathon guideline: **Never invent endpoints or credentials, never claim mock is live, and report `not_configured` transparently.**

---

## 5. Geo-Spatial Intelligence & Boundaries

### Static / Verified Layers (`backend/data/geospatial/`)
1. **`ports.geojson`**: Top 10 Indian ports with coordinates, operational depths, VHF radio channels, and contact information.
2. **`coastline.geojson`**: High-resolution Indian coastal boundary lines for distance-to-shore calculations.
3. **`restricted_zones.geojson`**: Naval security perimeters, offshore oil/gas installation zones, and separation schemes.
4. **`protected_areas.geojson`**: Marine Protected Areas (MPAs) such as the Gulf of Mannar Biosphere Reserve and Gahirmatha Marine Sanctuary.
5. **`hazard_zones.geojson`**: Navigational hazards including shallow shoals, historical shipwrecks, and submerged reefs.

### Spatial Analysis Engine
The `GeospatialService` performs:
- `find_nearest_port(lat, lon)`: Returns closest port and nautical distance.
- `check_restricted_zones(lat, lon)`: Ray-casting intersection check returning breach alerts and buffer margins.
- `check_hazards_proximity(lat, lon, buffer_km)`: Distance-filtered search for navigational dangers.
