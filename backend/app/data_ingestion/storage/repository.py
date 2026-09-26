import os
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

from sqlalchemy import create_engine, desc, func
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings
from app.data_ingestion.storage.db_models import (
    Base, DataSourceRunRecord, WeatherRecord, OceanRecord,
    PFZRecord, SatelliteRecord, MarineAdvisoryRecord
)
from app.data_ingestion.parsers.geo_parser import GeoSpatialParser

logger = logging.getLogger("marinex.ingestion.repository")

class IngestionRepository:
    """
    Persistence layer for official marine web ingestion.
    Supports PostgreSQL with PostGIS when configured, with seamless local SQLite fallback
    for zero-dependency offline and testing operation.
    """

    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or self._resolve_db_url()
        self.engine = None
        self.SessionLocal = None
        self.is_postgis = False
        self._initialize_engine()

    def _resolve_db_url(self) -> str:
        """Determines whether to connect to live PostgreSQL/PostGIS or local SQLite."""
        postgis_enabled = getattr(settings, "POSTGIS_ENABLED", False)
        postgres_host = getattr(settings, "POSTGRES_HOST", "").strip()

        if postgis_enabled and postgres_host:
            user = getattr(settings, "POSTGRES_USER", "postgres")
            pw = getattr(settings, "POSTGRES_PASSWORD", "")
            port = getattr(settings, "POSTGRES_PORT", 5432)
            db = getattr(settings, "POSTGRES_DB", "marinex_db")
            return f"postgresql://{user}:{pw}@{postgres_host}:{port}/{db}"

        # Local SQLite storage fallback
        data_dir = Path(__file__).resolve().parent.parent.parent.parent / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        sqlite_path = data_dir / "marine_ingestion.db"
        return f"sqlite:///{sqlite_path}"

    def _initialize_engine(self):
        """Initializes database engine and ensures all tables exist."""
        try:
            connect_args = {"check_same_thread": False} if "sqlite" in self.db_url else {}
            self.engine = create_engine(
                self.db_url,
                connect_args=connect_args,
                pool_pre_ping=True
            )
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            # Create tables
            Base.metadata.create_all(bind=self.engine)
            self.is_postgis = "postgresql" in self.db_url
            logger.info(f"[IngestionRepository] Connected to database: {'PostGIS' if self.is_postgis else 'SQLite'} ({self.db_url.split('@')[-1] if '@' in self.db_url else self.db_url})")
        except Exception as e:
            logger.warning(f"[IngestionRepository] Could not connect to primary DB '{self.db_url}': {e}. Falling back to SQLite.")
            data_dir = Path(__file__).resolve().parent.parent.parent.parent / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            sqlite_url = f"sqlite:///{data_dir / 'marine_ingestion.db'}"
            self.db_url = sqlite_url
            self.engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            Base.metadata.create_all(bind=self.engine)
            self.is_postgis = False

    def get_session(self) -> Session:
        return self.SessionLocal()

    # --- Run Audit Logging ---

    def record_run(
        self,
        scraper_name: str,
        source_name: str,
        status: str,
        records_ingested: int = 0,
        duration_ms: float = 0.0,
        error_message: Optional[str] = None,
        source_url: Optional[str] = None
    ) -> DataSourceRunRecord:
        """Records the execution of a scraper run."""
        session = self.get_session()
        try:
            run = DataSourceRunRecord(
                scraper_name=scraper_name,
                source_name=source_name,
                source_url=source_url,
                status=status,
                records_ingested=records_ingested,
                duration_ms=duration_ms,
                error_message=error_message,
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc)
            )
            session.add(run)
            session.commit()
            session.refresh(run)
            return run
        except Exception as e:
            session.rollback()
            logger.error(f"[IngestionRepository] Failed to record run: {e}")
            raise
        finally:
            session.close()

    def get_latest_run_for_scraper(self, scraper_name: str) -> Optional[DataSourceRunRecord]:
        """Returns the most recent ingestion run for a given scraper."""
        session = self.get_session()
        try:
            return session.query(DataSourceRunRecord).filter(
                DataSourceRunRecord.scraper_name == scraper_name
            ).order_by(desc(DataSourceRunRecord.completed_at)).first()
        finally:
            session.close()

    def get_latest_runs(self, limit: int = 10) -> List[DataSourceRunRecord]:
        session = self.get_session()
        try:
            return session.query(DataSourceRunRecord).order_by(desc(DataSourceRunRecord.completed_at)).limit(limit).all()
        finally:
            session.close()

    # --- Weather Observations ---

    def save_weather_observations(self, records: List[Dict[str, Any]]) -> int:
        if not records:
            return 0
        session = self.get_session()
        count = 0
        try:
            for r in records:
                rec = WeatherRecord(
                    source=r.get("source", "IMD"),
                    dataset=r.get("dataset", "IMD-Coastal-AWS"),
                    location_name=r.get("location_name", "Coastal Sector"),
                    latitude=float(r["latitude"]),
                    longitude=float(r["longitude"]),
                    temperature_c=r.get("temperature_c"),
                    apparent_temp_c=r.get("apparent_temp_c"),
                    wind_speed_knots=r.get("wind_speed_knots"),
                    wind_direction_deg=r.get("wind_direction_deg"),
                    wind_direction_text=r.get("wind_direction_text"),
                    relative_humidity=r.get("relative_humidity"),
                    pressure_hpa=r.get("pressure_hpa"),
                    rain_probability_pct=r.get("rain_probability_pct"),
                    precipitation_mm=r.get("precipitation_mm"),
                    visibility_km=r.get("visibility_km"),
                    weather_condition=r.get("weather_condition"),
                    storm_risk=r.get("storm_risk", "low"),
                    cyclone_warning=r.get("cyclone_warning"),
                    squall_warning=r.get("squall_warning"),
                    observed_at=r.get("observed_at"),
                    valid_from=r.get("valid_from"),
                    valid_until=r.get("valid_until"),
                    retrieved_at=r.get("retrieved_at", datetime.now(timezone.utc).isoformat()),
                    quality=r.get("quality", "OPERATIONAL"),
                    source_url=r.get("source_url"),
                    evidence_json=r.get("evidence_json", {})
                )
                session.add(rec)
                count += 1
            session.commit()
            return count
        except Exception as e:
            session.rollback()
            logger.error(f"[IngestionRepository] Failed to save weather records: {e}")
            raise
        finally:
            session.close()

    def get_latest_weather(self, lat: float, lon: float, max_distance_km: float = 100.0) -> Optional[WeatherRecord]:
        """Finds the most recent weather record within max_distance_km of requested coordinates."""
        session = self.get_session()
        try:
            records = session.query(WeatherRecord).order_by(desc(WeatherRecord.created_at)).limit(50).all()
            if not records:
                return None

            best_record = None
            min_dist = float("inf")

            for r in records:
                dist = GeoSpatialParser.haversine_distance_km(lat, lon, r.latitude, r.longitude)
                if dist <= max_distance_km and dist < min_dist:
                    min_dist = dist
                    best_record = r

            return best_record
        finally:
            session.close()

    # --- Ocean Observations ---

    def save_ocean_observations(self, records: List[Dict[str, Any]]) -> int:
        if not records:
            return 0
        session = self.get_session()
        count = 0
        try:
            for r in records:
                rec = OceanRecord(
                    source=r.get("source", "INCOIS"),
                    dataset=r.get("dataset", "INCOIS-Ocean-State-Forecast"),
                    sector_name=r.get("sector_name", "Coastal Sector"),
                    latitude=float(r["latitude"]),
                    longitude=float(r["longitude"]),
                    significant_wave_height_m=r.get("significant_wave_height_m"),
                    wave_period_s=r.get("wave_period_s"),
                    swell_height_m=r.get("swell_height_m"),
                    swell_period_s=r.get("swell_period_s"),
                    swell_direction_deg=r.get("swell_direction_deg"),
                    swell_direction_text=r.get("swell_direction_text"),
                    sea_surface_temp_c=r.get("sea_surface_temp_c"),
                    current_speed_knots=r.get("current_speed_knots"),
                    current_direction_deg=r.get("current_direction_deg"),
                    sea_state=r.get("sea_state"),
                    tide_status=r.get("tide_status"),
                    high_wave_alert=r.get("high_wave_alert"),
                    suitability=r.get("suitability", "Favorable"),
                    observed_at=r.get("observed_at"),
                    valid_from=r.get("valid_from"),
                    valid_until=r.get("valid_until"),
                    retrieved_at=r.get("retrieved_at", datetime.now(timezone.utc).isoformat()),
                    quality=r.get("quality", "OPERATIONAL"),
                    source_url=r.get("source_url"),
                    evidence_json=r.get("evidence_json", {})
                )
                session.add(rec)
                count += 1
            session.commit()
            return count
        except Exception as e:
            session.rollback()
            logger.error(f"[IngestionRepository] Failed to save ocean records: {e}")
            raise
        finally:
            session.close()

    def get_latest_ocean(self, lat: float, lon: float, max_distance_km: float = 120.0) -> Optional[OceanRecord]:
        """Finds the most recent ocean record within max_distance_km."""
        session = self.get_session()
        try:
            records = session.query(OceanRecord).order_by(desc(OceanRecord.created_at)).limit(50).all()
            if not records:
                return None

            best_record = None
            min_dist = float("inf")

            for r in records:
                dist = GeoSpatialParser.haversine_distance_km(lat, lon, r.latitude, r.longitude)
                if dist <= max_distance_km and dist < min_dist:
                    min_dist = dist
                    best_record = r

            return best_record
        finally:
            session.close()

    # --- PFZ Advisories ---

    def save_pfz_advisories(self, records: List[Dict[str, Any]]) -> int:
        if not records:
            return 0
        session = self.get_session()
        count = 0
        try:
            for r in records:
                rec = PFZRecord(
                    source=r.get("source", "INCOIS PFZ Mission"),
                    dataset=r.get("dataset", "INCOIS-PFZ-Advisory"),
                    zone_id=r["zone_id"],
                    zone_name=r.get("zone_name", "Fishing Zone"),
                    sector=r.get("sector", "Coastal Sector"),
                    latitude=float(r["latitude"]),
                    longitude=float(r["longitude"]),
                    distance_km=float(r.get("distance_km", 0.0)),
                    direction=r.get("direction", "NE"),
                    bearing_deg=r.get("bearing_deg"),
                    depth_meters=int(r.get("depth_meters", 40)),
                    sst_c=r.get("sst_c"),
                    chlorophyll=r.get("chlorophyll"),
                    suitability=r.get("suitability", "Favorable"),
                    dominant_species_json=r.get("dominant_species", []),
                    geojson=r.get("geojson", GeoSpatialParser.create_geojson_point(float(r["latitude"]), float(r["longitude"]))),
                    observed_at=r.get("observed_at"),
                    valid_from=r.get("valid_from"),
                    valid_until=r.get("valid_until"),
                    retrieved_at=r.get("retrieved_at", datetime.now(timezone.utc).isoformat()),
                    quality=r.get("quality", "HIGH"),
                    source_url=r.get("source_url"),
                    evidence_json=r.get("evidence_json", {})
                )
                session.add(rec)
                count += 1
            session.commit()
            return count
        except Exception as e:
            session.rollback()
            logger.error(f"[IngestionRepository] Failed to save PFZ records: {e}")
            raise
        finally:
            session.close()

    def get_active_pfz(self, lat: float, lon: float, radius_km: float = 200.0) -> List[PFZRecord]:
        """Returns active PFZ zones within radius_km sorted by proximity."""
        session = self.get_session()
        try:
            records = session.query(PFZRecord).order_by(desc(PFZRecord.created_at)).limit(100).all()
            matching = []
            for r in records:
                dist = GeoSpatialParser.haversine_distance_km(lat, lon, r.latitude, r.longitude)
                if dist <= radius_km:
                    matching.append((dist, r))

            matching.sort(key=lambda x: x[0])
            return [x[1] for x in matching]
        finally:
            session.close()

    # --- Satellite Granules ---

    def save_satellite_granules(self, records: List[Dict[str, Any]]) -> int:
        if not records:
            return 0
        session = self.get_session()
        count = 0
        try:
            for r in records:
                rec = SatelliteRecord(
                    source=r.get("source", "ISRO MOSDAC"),
                    dataset_id=r.get("dataset_id", "OS3_SST_L3"),
                    granule_id=r["granule_id"],
                    satellite_mission=r.get("satellite_mission", "ISRO Oceansat-3"),
                    sensor=r.get("sensor"),
                    product_name=r.get("product_name", "SST"),
                    pass_timestamp=r.get("pass_timestamp"),
                    latitude=r.get("latitude"),
                    longitude=r.get("longitude"),
                    spatial_resolution_km=float(r.get("spatial_resolution_km", 1.0)),
                    cloud_cover_percent=r.get("cloud_cover_percent"),
                    sst_c=r.get("sst_c"),
                    chlorophyll_mg_m3=r.get("chlorophyll_mg_m3"),
                    download_url=r.get("download_url"),
                    observed_at=r.get("observed_at"),
                    retrieved_at=r.get("retrieved_at", datetime.now(timezone.utc).isoformat()),
                    quality=r.get("quality", "OPERATIONAL"),
                    evidence_json=r.get("evidence_json", {})
                )
                session.add(rec)
                count += 1
            session.commit()
            return count
        except Exception as e:
            session.rollback()
            logger.error(f"[IngestionRepository] Failed to save satellite records: {e}")
            raise
        finally:
            session.close()

    def get_latest_satellite(self, product: str, lat: Optional[float] = None, lon: Optional[float] = None) -> Optional[SatelliteRecord]:
        session = self.get_session()
        try:
            q = session.query(SatelliteRecord).filter(
                SatelliteRecord.product_name.ilike(f"%{product}%")
            ).order_by(desc(SatelliteRecord.created_at))
            return q.first()
        finally:
            session.close()

    # --- Marine Advisories ---

    def save_marine_advisories(self, records: List[Dict[str, Any]]) -> int:
        if not records:
            return 0
        session = self.get_session()
        count = 0
        try:
            for r in records:
                rec = MarineAdvisoryRecord(
                    agency=r.get("agency", "IMD / INCOIS"),
                    alert_type=r.get("alert_type", "Marine Alert"),
                    severity=r.get("severity", "MEDIUM"),
                    location_name=r.get("location_name", "Coastal Sector"),
                    latitude=float(r["latitude"]) if r.get("latitude") is not None else None,
                    longitude=float(r["longitude"]) if r.get("longitude") is not None else None,
                    radius_km=float(r.get("radius_km", 50.0)),
                    headline=r.get("headline", "Marine Weather Advisory"),
                    advisory_text=r.get("advisory_text", ""),
                    issued_at=r.get("issued_at"),
                    valid_until=r.get("valid_until"),
                    retrieved_at=r.get("retrieved_at", datetime.now(timezone.utc).isoformat()),
                    source_url=r.get("source_url")
                )
                session.add(rec)
                count += 1
            session.commit()
            return count
        except Exception as e:
            session.rollback()
            logger.error(f"[IngestionRepository] Failed to save marine advisories: {e}")
            raise
        finally:
            session.close()

    def get_active_advisories(self, lat: Optional[float] = None, lon: Optional[float] = None, max_distance_km: float = 150.0) -> List[MarineAdvisoryRecord]:
        """Returns active advisories, optionally filtered by spatial proximity."""
        session = self.get_session()
        try:
            records = session.query(MarineAdvisoryRecord).order_by(desc(MarineAdvisoryRecord.created_at)).limit(50).all()
            if lat is None or lon is None:
                return records

            matching = []
            for r in records:
                if r.latitude is not None and r.longitude is not None:
                    dist = GeoSpatialParser.haversine_distance_km(lat, lon, r.latitude, r.longitude)
                    if dist <= max_distance_km:
                        matching.append(r)
                else:
                    matching.append(r)
            return matching
        finally:
            session.close()

    # --- Health & Diagnostics ---

    def get_database_status(self) -> Dict[str, Any]:
        """Reports connectivity, table sizes, and spatial status."""
        session = self.get_session()
        try:
            return {
                "db_engine": "PostGIS (PostgreSQL)" if self.is_postgis else "SQLite Local Fallback",
                "is_postgis": self.is_postgis,
                "status": "CONNECTED",
                "counts": {
                    "weather_records": session.query(func.count(WeatherRecord.id)).scalar() or 0,
                    "ocean_records": session.query(func.count(OceanRecord.id)).scalar() or 0,
                    "pfz_records": session.query(func.count(PFZRecord.id)).scalar() or 0,
                    "satellite_records": session.query(func.count(SatelliteRecord.id)).scalar() or 0,
                    "advisory_records": session.query(func.count(MarineAdvisoryRecord.id)).scalar() or 0,
                    "ingestion_runs": session.query(func.count(DataSourceRunRecord.id)).scalar() or 0
                }
            }
        except Exception as e:
            return {
                "db_engine": "Unknown",
                "status": "ERROR",
                "error": str(e)
            }
        finally:
            session.close()

ingestion_repository = IngestionRepository()

