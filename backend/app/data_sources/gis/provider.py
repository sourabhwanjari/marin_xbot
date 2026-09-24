import os
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from app.data_sources.common.base_provider import BaseMarineProvider
from app.data_sources.common.models import ProviderCapability
from app.data_sources.common.provider_status import ProviderStatus
from app.marine_models.base import (
    Location,
    TimeWindow,
    MarineDataResponse,
    MarineEvidence,
    DataStatus,
)
from app.marine_models.domains import GeospatialData
from app.data_sources.geospatial.service import geospatial_service

logger = logging.getLogger("marinex.datasources.gis")

class GISProvider(BaseMarineProvider):
    """
    Maritime Geospatial & Navigation Boundary Provider adapter.
    Resolves coastal port proximities, commercial shipping fairways,
    restricted naval zones, Marine Protected Areas (MPAs), and navigational hazards.
    Phase 5B compliant: deterministic spatial computation (no LLM guessing of distances/boundaries),
    PostGIS integration when configured, or built-in verified GeoJSON spatial geometry engine.
    """
    def __init__(self):
        super().__init__(
            provider_name="GIS-Spatial-Engine",
            capabilities=[ProviderCapability.GEOSPATIAL, ProviderCapability.HAZARDS]
        )

    @property
    def is_enabled(self) -> bool:
        return True  # Built-in GeoJSON spatial engine is always active

    @property
    def is_configured(self) -> bool:
        postgis_enabled = os.getenv("POSTGIS_ENABLED", "false").lower() in ("true", "1", "yes")
        postgres_host = os.getenv("POSTGRES_HOST", "").strip()
        return bool(postgis_enabled and postgres_host)

    @property
    def status(self) -> ProviderStatus:
        # Spatial engine is operational (via PostGIS when configured or built-in GeoJSON engine)
        return ProviderStatus.CONNECTED

    def check_postgis_connection(self) -> bool:
        """Tests live PostGIS connectivity if database credentials are provided."""
        if not self.is_configured:
            return False
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=os.getenv("POSTGRES_HOST"),
                port=int(os.getenv("POSTGRES_PORT", "5432")),
                dbname=os.getenv("POSTGRES_DB", "marinex_db"),
                user=os.getenv("POSTGRES_USER"),
                password=os.getenv("POSTGRES_PASSWORD"),
                connect_timeout=3
            )
            conn.close()
            return True
        except Exception as e:
            logger.debug(f"[GIS Provider] PostGIS direct connection test: {e}")
            return False

    def get_geospatial_data(self, location: Location) -> MarineDataResponse:
        retrieved_at = datetime.now(timezone.utc).isoformat()
        logger.info(f"[GIS Provider] get_geospatial_data requested for {location.name or 'Coastal Sector'} ({location.latitude:.3f}, {location.longitude:.3f})")

        # Deterministic spatial computation (checks fairways, MPAs, nearest ports)
        summary = geospatial_service.get_geospatial_summary(
            location_name=location.name or "Coastal Sector",
            latitude=location.latitude,
            longitude=location.longitude
        )

        has_live_postgis = self.is_configured and self.check_postgis_connection()
        provider_name = "PostGIS-Engine" if has_live_postgis else "GeoJSON-Spatial-Engine"
        status = DataStatus.EXTERNAL if has_live_postgis else DataStatus.VERIFIED

        hazards = getattr(summary, "nearby_hazards", []) or []
        nearest_hazard = hazards[0].get("name") if (hazards and isinstance(hazards[0], dict)) else None

        geospatial_data = GeospatialData(
            location_name=summary.location_name,
            latitude=location.latitude,
            longitude=location.longitude,
            nearest_port=summary.nearest_port,
            restricted_zone=summary.restricted_zone,
            protected_zone=summary.protected_zone,
            distance_from_coast_km=summary.distance_from_coast_km,
            nearest_hazard=nearest_hazard,
            restriction_details=getattr(summary, "restricted_zone_details", None),
            map_data=getattr(summary, "map_data", None)
        )

        observed_time = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        return MarineDataResponse(
            status=status,
            provider=provider_name,
            dataset="Indian-Maritime-Boundaries-EEZ",
            parameter="maritime_geofencing",
            latitude=location.latitude,
            longitude=location.longitude,
            observed_at=observed_time,
            valid_from=observed_time,
            valid_until=None,
            retrieved_at=retrieved_at,
            quality="VERIFIED",
            location=location.to_dict(),
            data=geospatial_data.model_dump(),
            evidence=[
                MarineEvidence(
                    source="Ministry of Ports, Shipping and Waterways / Indian Coast Guard",
                    provider="GISProvider",
                    dataset="Indian-Maritime-Boundaries-EEZ",
                    observed_at=observed_time,
                    retrieved_at=retrieved_at,
                    quality="HIGH",
                    status=status,
                    evidence_url="https://natmo.gov.in/maritime_zones",
                    metadata={
                        "spatial_engine": provider_name,
                        "restricted_zone_found": summary.restricted_zone,
                        "nearest_port": summary.nearest_port.get("name"),
                        "computation": "DETERMINISTIC_SPATIAL_GEOMETRY"
                    }
                )
            ]
        )
