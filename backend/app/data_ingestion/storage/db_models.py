import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Float, Integer, Boolean, DateTime, Text, JSON
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()

def get_utc_now():
    return datetime.now(timezone.utc)

class DataSourceRunRecord(Base):
    """Ingestion audit trail tracking scraper runs, durations, records, and errors."""
    __tablename__ = "data_source_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scraper_name = Column(String(64), nullable=False, index=True)
    source_name = Column(String(128), nullable=False)
    source_url = Column(String(512), nullable=True)
    status = Column(String(32), nullable=False, index=True)  # SUCCESS, UNAVAILABLE, ERROR, etc.
    records_ingested = Column(Integer, default=0)
    duration_ms = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), default=get_utc_now)
    completed_at = Column(DateTime(timezone=True), default=get_utc_now)


    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "scraper_name": self.scraper_name,
            "source_name": self.source_name,
            "source_url": self.source_url,
            "status": self.status,
            "records_ingested": self.records_ingested,
            "duration_ms": self.duration_ms,
            "error_message": self.error_message,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class WeatherRecord(Base):
    """Normalized weather observations and coastal forecasts from official sources (e.g. IMD)."""
    __tablename__ = "weather_data"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source = Column(String(128), nullable=False, index=True)  # e.g. "India Meteorological Department"
    dataset = Column(String(128), nullable=False)             # e.g. "IMD-Coastal-AWS-Observations"
    location_name = Column(String(128), nullable=False, index=True)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    temperature_c = Column(Float, nullable=True)
    apparent_temp_c = Column(Float, nullable=True)
    wind_speed_knots = Column(Float, nullable=True)
    wind_direction_deg = Column(Float, nullable=True)
    wind_direction_text = Column(String(32), nullable=True)
    relative_humidity = Column(Float, nullable=True)
    pressure_hpa = Column(Float, nullable=True)
    rain_probability_pct = Column(Integer, nullable=True)
    precipitation_mm = Column(Float, nullable=True)
    visibility_km = Column(Float, nullable=True)
    weather_condition = Column(String(128), nullable=True)
    storm_risk = Column(String(32), default="low")
    cyclone_warning = Column(Text, nullable=True)
    squall_warning = Column(Text, nullable=True)
    observed_at = Column(String(64), nullable=True)
    valid_from = Column(String(64), nullable=True)
    valid_until = Column(String(64), nullable=True)
    retrieved_at = Column(String(64), nullable=False)
    quality = Column(String(32), default="OPERATIONAL")
    source_url = Column(String(512), nullable=True)
    evidence_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source": self.source,
            "dataset": self.dataset,
            "location_name": self.location_name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "temperature_c": self.temperature_c,
            "apparent_temp_c": self.apparent_temp_c,
            "wind_speed_knots": self.wind_speed_knots,
            "wind_direction_deg": self.wind_direction_deg,
            "wind_direction_text": self.wind_direction_text,
            "relative_humidity": self.relative_humidity,
            "pressure_hpa": self.pressure_hpa,
            "rain_probability_pct": self.rain_probability_pct,
            "precipitation_mm": self.precipitation_mm,
            "visibility_km": self.visibility_km,
            "weather_condition": self.weather_condition,
            "storm_risk": self.storm_risk,
            "cyclone_warning": self.cyclone_warning,
            "squall_warning": self.squall_warning,
            "observed_at": self.observed_at,
            "valid_from": self.valid_from,
            "valid_until": self.valid_until,
            "retrieved_at": self.retrieved_at,
            "quality": self.quality,
            "source_url": self.source_url,
            "evidence_json": self.evidence_json or {}
        }


class OceanRecord(Base):
    """Normalized oceanographic and hydrodynamic telemetry from official sources (e.g. INCOIS)."""
    __tablename__ = "ocean_data"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source = Column(String(128), nullable=False, index=True)  # e.g. "INCOIS Hyderabad"
    dataset = Column(String(128), nullable=False)             # e.g. "INCOIS-Ocean-State-Forecast"
    sector_name = Column(String(128), nullable=False, index=True)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    significant_wave_height_m = Column(Float, nullable=True)
    wave_period_s = Column(Float, nullable=True)
    swell_height_m = Column(Float, nullable=True)
    swell_period_s = Column(Float, nullable=True)
    swell_direction_deg = Column(Float, nullable=True)
    swell_direction_text = Column(String(32), nullable=True)
    sea_surface_temp_c = Column(Float, nullable=True)
    current_speed_knots = Column(Float, nullable=True)
    current_direction_deg = Column(Float, nullable=True)
    sea_state = Column(String(64), nullable=True)
    tide_status = Column(String(64), nullable=True)
    high_wave_alert = Column(Text, nullable=True)
    suitability = Column(String(32), default="Favorable")
    observed_at = Column(String(64), nullable=True)
    valid_from = Column(String(64), nullable=True)
    valid_until = Column(String(64), nullable=True)
    retrieved_at = Column(String(64), nullable=False)
    quality = Column(String(32), default="OPERATIONAL")
    source_url = Column(String(512), nullable=True)
    evidence_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source": self.source,
            "dataset": self.dataset,
            "sector_name": self.sector_name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "significant_wave_height_m": self.significant_wave_height_m,
            "wave_period_s": self.wave_period_s,
            "swell_height_m": self.swell_height_m,
            "swell_period_s": self.swell_period_s,
            "swell_direction_deg": self.swell_direction_deg,
            "swell_direction_text": self.swell_direction_text,
            "sea_surface_temp_c": self.sea_surface_temp_c,
            "current_speed_knots": self.current_speed_knots,
            "current_direction_deg": self.current_direction_deg,
            "sea_state": self.sea_state,
            "tide_status": self.tide_status,
            "high_wave_alert": self.high_wave_alert,
            "suitability": self.suitability,
            "observed_at": self.observed_at,
            "valid_from": self.valid_from,
            "valid_until": self.valid_until,
            "retrieved_at": self.retrieved_at,
            "quality": self.quality,
            "source_url": self.source_url,
            "evidence_json": self.evidence_json or {}
        }


class PFZRecord(Base):
    """Potential Fishing Zone advisory records with spatial coordinates and target pelagics."""
    __tablename__ = "pfz_data"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source = Column(String(128), nullable=False, index=True)  # e.g. "INCOIS PFZ Mission"
    dataset = Column(String(128), nullable=False)
    zone_id = Column(String(64), nullable=False, index=True)
    zone_name = Column(String(128), nullable=False)
    sector = Column(String(128), nullable=False, index=True)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    distance_km = Column(Float, nullable=False)
    direction = Column(String(32), nullable=False)
    bearing_deg = Column(Float, nullable=True)
    depth_meters = Column(Integer, default=40)
    sst_c = Column(Float, nullable=True)
    chlorophyll = Column(String(64), nullable=True)
    suitability = Column(String(32), default="Favorable")
    dominant_species_json = Column(JSON, nullable=True)
    geojson = Column(JSON, nullable=True)
    observed_at = Column(String(64), nullable=True)
    valid_from = Column(String(64), nullable=True)
    valid_until = Column(String(64), nullable=True)
    retrieved_at = Column(String(64), nullable=False)
    quality = Column(String(32), default="HIGH")
    source_url = Column(String(512), nullable=True)
    evidence_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source": self.source,
            "dataset": self.dataset,
            "zone_id": self.zone_id,
            "zone_name": self.zone_name,
            "sector": self.sector,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "distance_km": self.distance_km,
            "direction": self.direction,
            "bearing_deg": self.bearing_deg,
            "depth_meters": self.depth_meters,
            "sst_c": self.sst_c,
            "chlorophyll": self.chlorophyll,
            "suitability": self.suitability,
            "dominant_species": self.dominant_species_json or [],
            "dominant_species_json": self.dominant_species_json or [],
            "geojson": self.geojson,
            "observed_at": self.observed_at,
            "valid_from": self.valid_from,
            "valid_until": self.valid_until,
            "retrieved_at": self.retrieved_at,
            "quality": self.quality,
            "source_url": self.source_url,
            "evidence_json": self.evidence_json or {}
        }


class SatelliteRecord(Base):
    """Satellite earth observation granules from official public catalogs (e.g. MOSDAC)."""
    __tablename__ = "satellite_data"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source = Column(String(128), nullable=False, index=True)  # e.g. "ISRO MOSDAC"
    dataset_id = Column(String(128), nullable=False)          # e.g. "OS3_SST_L3"
    granule_id = Column(String(128), nullable=False, index=True)
    satellite_mission = Column(String(128), default="ISRO Oceansat-3")
    sensor = Column(String(64), nullable=True)
    product_name = Column(String(128), nullable=False)
    pass_timestamp = Column(String(64), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    spatial_resolution_km = Column(Float, default=1.0)
    cloud_cover_percent = Column(Float, nullable=True)
    sst_c = Column(Float, nullable=True)
    chlorophyll_mg_m3 = Column(Float, nullable=True)
    download_url = Column(String(512), nullable=True)
    observed_at = Column(String(64), nullable=True)
    retrieved_at = Column(String(64), nullable=False)
    quality = Column(String(32), default="OPERATIONAL")
    evidence_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source": self.source,
            "dataset_id": self.dataset_id,
            "granule_id": self.granule_id,
            "satellite_mission": self.satellite_mission,
            "sensor": self.sensor,
            "product_name": self.product_name,
            "pass_timestamp": self.pass_timestamp,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "spatial_resolution_km": self.spatial_resolution_km,
            "cloud_cover_percent": self.cloud_cover_percent,
            "sst_c": self.sst_c,
            "chlorophyll_mg_m3": self.chlorophyll_mg_m3,
            "download_url": self.download_url,
            "observed_at": self.observed_at,
            "retrieved_at": self.retrieved_at,
            "quality": self.quality,
            "evidence_json": self.evidence_json or {}
        }


class MarineAdvisoryRecord(Base):
    """Official marine weather, high wave, and navigational advisories."""
    __tablename__ = "marine_advisories"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agency = Column(String(128), nullable=False, index=True)   # "IMD", "INCOIS", "Coast Guard"
    alert_type = Column(String(64), nullable=False)           # "High Wave", "Squall", "Cyclone", "Rough Sea"
    severity = Column(String(32), default="MEDIUM")           # "LOW", "MEDIUM", "HIGH"
    location_name = Column(String(128), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    radius_km = Column(Float, default=50.0)
    headline = Column(String(256), nullable=False)
    advisory_text = Column(Text, nullable=False)
    issued_at = Column(String(64), nullable=True)
    valid_until = Column(String(64), nullable=True)
    retrieved_at = Column(String(64), nullable=False)
    source_url = Column(String(512), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "agency": self.agency,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "location_name": self.location_name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "radius_km": self.radius_km,
            "headline": self.headline,
            "advisory_text": self.advisory_text,
            "issued_at": self.issued_at,
            "valid_until": self.valid_until,
            "retrieved_at": self.retrieved_at,
            "source_url": self.source_url
        }

