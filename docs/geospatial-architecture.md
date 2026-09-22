# MARINEX AI — Geo-Spatial Intelligence Architecture

## Overview
Phase 4 implements a dedicated **Geo-Spatial Intelligence Engine** (`backend/app/data_sources/geospatial/service.py`) for **MARINEX AI**. It provides spatial reasoning, boundary containment, port proximity detection, and safety corridor verification across the Indian maritime domain.

---

## 1. Spatial Reference System & Data Layers

All geospatial geometry adheres to **WGS 84 (EPSG:4326)** coordinates (`[longitude, latitude]`).

### Authoritative GeoJSON Datasets (`backend/data/geospatial/`)

| Dataset File | Geometry Type | Features | Description |
|---|---|---|---|
| `ports.geojson` | `Point` | 10 major Indian ports | Mumbai, JNPT, Chennai, Kochi, Visakhapatnam, Paradip, Mormugao, Deendayal/Kandla, VOC/Tuticorin, New Mangalore. Includes max draft, VHF channel, coordinates. |
| `coastline.geojson` | `LineString` / `MultiLineString` | Indian peninsular coastline | Used for distance-from-shore calculations and territorial sea verification. |
| `restricted_zones.geojson` | `Polygon` | Naval & critical infrastructure | Western Naval Command Mumbai, Eastern Naval Command Vizag, Bombay High offshore oil platform perimeter, Cochin Naval Base security zone. |
| `protected_areas.geojson` | `Polygon` | Marine Protected Areas (MPAs) | Gulf of Mannar Biosphere Reserve, Sundarbans Tiger Reserve Marine Buffer, Gahirmatha Olive Ridley Turtle Sanctuary. |
| `hazard_zones.geojson` | `Polygon` / `Point` | Navigational hazards | Prongs Reef shallow shoals, Pamban Pass submerged rocks, Angria Bank submerged coral pinnacle. |

---

## 2. Spatial Reasoning Engine Algorithms

The engine performs real-time spatial calculations without requiring a heavyweight GIS database:

### Great-Circle Distance (Haversine Formula)
Used for computing distances between vessel positions, ports, and navigational hazards:
\[
d = 2R \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right)}\right)
\]
Where \(\phi\) is latitude, \(\lambda\) is longitude, and \(R = 6371.0 \text{ km}\).

### Point-in-Polygon Geofencing (Ray-Casting Algorithm)
Determines whether a vessel's coordinates fall inside any restricted security corridor, marine sanctuary, or hazard polygon. The algorithm casts a horizontal ray from the vessel's coordinates and counts the number of intersections with polygon edges:
- **Odd number of intersections**: Vessel is inside the zone (Breach detected).
- **Even number of intersections**: Vessel is outside the zone.

### Proximity Buffer Queries
Calculates distances to the nearest boundary edge of protected zones and hazard zones, returning warnings if within a safety buffer (e.g., 5 km or 10 km).

---

## 3. Frontend Map Integration (Leaflet)

The geospatial layers are exposed via `/api/data-sources/geospatial` and `/api/data-sources/pfz`, and dynamically rendered on the frontend Leaflet map:

### Layer Controls
- **PFZ Layer Toggle**: Green semi-transparent polygons (`#10b981`) showing high-probability fishing zones with popups containing SST, Chlorophyll, and target species.
- **Restricted Zones Toggle**: Red hatched polygons (`#ef4444`) showing naval and offshore industrial exclusion zones.
- **Hazards Toggle**: Amber circles/polygons (`#f59e0b`) indicating reefs, shoals, and wrecks.

### Interactive Synchronization
When the user queries the conversational AI about a specific sector (e.g., *"Is it safe to fish 20km off Mumbai?"*), the `GeospatialAgent` injects relevant GeoJSON features into the response state (`map_data`), automatically panning and highlighting the zone on the user's map.

---

## 4. PostGIS Production Migration Path

While the current engine operates autonomously using pure Python and GeoJSON (for zero-dependency deployment), the architecture is 100% prepared for enterprise PostgreSQL / PostGIS:

### Recommended Schema
```sql
-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Ports Table
CREATE TABLE marine_ports (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    state VARCHAR(50),
    geom GEOMETRY(Point, 4326) NOT NULL,
    max_draft_m FLOAT,
    vhf_channel INT
);
CREATE INDEX idx_ports_geom ON marine_ports USING GIST (geom);

-- Restricted Zones Table
CREATE TABLE marine_restricted_zones (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    zone_type VARCHAR(50),
    authority VARCHAR(100),
    geom GEOMETRY(Polygon, 4326) NOT NULL
);
CREATE INDEX idx_restricted_geom ON marine_restricted_zones USING GIST (geom);

-- Spatial Query Example: Find nearest port
SELECT name, ST_Distance(geom::geography, ST_SetSRID(ST_MakePoint(72.8347, 18.922), 4326)::geography) / 1000 AS dist_km
FROM marine_ports
ORDER BY geom <-> ST_SetSRID(ST_MakePoint(72.8347, 18.922), 4326)
LIMIT 1;
```
