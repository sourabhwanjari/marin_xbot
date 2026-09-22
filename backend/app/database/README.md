# MarineX AI Database Architecture

## Overview
Phase 1 runs purely in-memory using centralized mock data so developers can inspect and test without configuring database servers.
In subsequent phases, MARINEX AI will leverage **PostgreSQL 16+** augmented with two extensions:
1. **PostGIS**: For geospatial indexing, geodesic distance, polygon containment, and spatial-temporal reasoning.
2. **pgvector**: For high-dimensional vector embeddings supporting hybrid semantic retrieval in the RAG pipeline.

---

## Target Database Schema & Entities

### 1. `users`
- `id` (UUID, Primary Key)
- `name` (VARCHAR)
- `role` (ENUM: 'fisherman', 'researcher', 'coastal_authority', 'operator')
- `preferred_language` (VARCHAR: 'en', 'hi', 'ta', 'te', 'ml', 'bn')
- `home_port_location` (GEOMETRY(Point, 4326))
- `created_at` (TIMESTAMP WITH TIME ZONE)

### 2. `marine_conditions`
- `id` (BIGSERIAL, Primary Key)
- `location` (GEOMETRY(Point, 4326), Spatial Index)
- `sea_surface_temp_c` (FLOAT)
- `chlorophyll_category` (VARCHAR)
- `wave_height_m` (FLOAT)
- `wind_speed_knots` (FLOAT)
- `wind_direction_deg` (INT)
- `sea_state` (VARCHAR)
- `visibility_nm` (FLOAT)
- `recorded_at` (TIMESTAMP WITH TIME ZONE)

### 3. `fishing_zones`
- `id` (UUID, Primary Key)
- `name` (VARCHAR)
- `geom` (GEOMETRY(Polygon, 4326), Spatial Index)
- `centroid` (GEOMETRY(Point, 4326))
- `sst_c` (FLOAT)
- `chlorophyll_level` (VARCHAR)
- `suitability` (ENUM: 'Favorable', 'Caution', 'Hazard')
- `dominant_species` (TEXT[])
- `valid_from` (TIMESTAMP WITH TIME ZONE)
- `valid_until` (TIMESTAMP WITH TIME ZONE)

### 4. `marine_alerts`
- `id` (UUID, Primary Key)
- `type` (VARCHAR: 'High Wave', 'Cyclone', 'Lightning', 'Strong Wind', 'Restricted Area')
- `severity` (ENUM: 'LOW', 'MEDIUM', 'HIGH')
- `area` (GEOMETRY(MultiPolygon, 4326))
- `description` (TEXT)
- `advisory` (TEXT)
- `issued_at` (TIMESTAMP WITH TIME ZONE)
- `expires_at` (TIMESTAMP WITH TIME ZONE)

### 5. `marine_advisories`
- `id` (UUID, Primary Key)
- `agency` (VARCHAR: 'INCOIS', 'IMD', 'Coast Guard')
- `headline` (TEXT)
- `content` (TEXT)
- `affected_sectors` (GEOMETRY(MultiPolygon, 4326))
- `published_at` (TIMESTAMP WITH TIME ZONE)

### 6. `geospatial_zones`
- `id` (UUID, Primary Key)
- `name` (VARCHAR)
- `category` (ENUM: 'MPA', 'NAVAL_SECURITY', 'INTERNATIONAL_BORDER', 'ANCHORAGE')
- `boundary` (GEOMETRY(Polygon, 4326))
- `restriction_rules` (JSONB)

### 7. `documents`
- `id` (UUID, Primary Key)
- `title` (VARCHAR)
- `source_url` (VARCHAR)
- `document_type` (VARCHAR)
- `metadata` (JSONB)
- `uploaded_at` (TIMESTAMP WITH TIME ZONE)

### 8. `document_chunks`
- `id` (UUID, Primary Key)
- `document_id` (UUID, Foreign Key -> documents.id)
- `chunk_index` (INT)
- `content` (TEXT)
- `embedding` (VECTOR(1536)) -- pgvector index: HNSW with vector_cosine_ops
- `spatial_extent` (GEOMETRY(Polygon, 4326), Nullable)
