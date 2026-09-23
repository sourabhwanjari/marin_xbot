import os
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from app.data_sources.common.base_provider import BaseMarineProvider
from app.data_sources.common.models import ProviderCapability
from app.marine_models.base import (
    Location,
    TimeWindow,
    MarineDataResponse,
    MarineEvidence,
    DataStatus,
)
from app.data_sources.geospatial.service import geospatial_service

logger = logging.getLogger("marinex.datasources.gis")

class GISProvider(BaseMarineProvider):
    """
    Maritime Geospatial & Navigation Boundary Provider adapter.
    Resolves coastal port proximities, commercial shipping fairways,
    restricted naval zones, Marine Protected Areas (MPAs), and navigational hazards.
    Interfaces with PostGIS when configured or built-in verified GeoJSON spatial geometry engine.
    """
    def __init__(self):
        super().__init__(
            provider_name="GIS-Spatial-Engine",
            capabilities=[ProviderCapability.GEOSPATIAL, ProviderCapability.HAZARDS]
        )

    @property
    def is_enabled(self) -> bool:
        return True  # Built-in GeoJSON spatial engine is always available

    @property
    def is_configured(self) -> bool:
        # Check if production PostGIS database is active
        postgis_enabled = os.getenv("POSTGIS_ENABLED", "false").lower() in ("true", "1", "yes")
        postgres_host = os.getenv("POSTGRES_HOST", "").strip()
        return bool(postgis_enabled and postgres_host)

    def get_geospatial_data(self, location: Location) -> MarineDataResponse:
        retrieved_at = datetime.now(timezone.utc).isoformat()
        logger.info(f"[GIS Provider] get_geospatial_data requested for {location.name or 'Sector'} ({location.latitude}, {location.longitude})")

        # Query spatial engine (checks fairways, MPAs, nearest ports)
        summary = geospatial_service.get_geospatial_summary(
            location_name=location.name or "Coastal Sector",
            latitude=location.latitude,
            longitude=location.longitude
        )

        provider_name = "PostGIS-Engine" if self.is_configured else "GeoJSON-Spatial-Engine"
        status = DataStatus.EXTERNAL if self.is_configured else DataStatus.VERIFIED

        hazards = getattr(summary, "nearby_hazards", []) or []
        nearest_hazard = hazards[0].get("name") if (hazards and isinstance(hazards[0], dict)) else None
        data = {
            "location_name": summary.location_name,
            "coordinates": summary.coordinates,
            "nearest_port": summary.nearest_port,
            "distance_from_coast_km": summary.distance_from_coast_km,
            "restricted_zone": summary.restricted_zone,
            "protected_zone": summary.protected_zone,
            "nearest_hazard": nearest_hazard,
            "nearby_hazards": hazards,
            "restriction_details": getattr(summary, "restricted_zone_details", None),
            "map_data": getattr(summary, "map_data", None)
        }

        return MarineDataResponse(
            status=status,
            provider=provider_name,
            dataset="Indian-Maritime-Boundaries-EEZ",
            parameter="maritime_geofencing",
            latitude=location.latitude,
            longitude=location.longitude,
            retrieved_at=retrieved_at,
            quality="VERIFIED",
            location=location.to_dict(),
            data=data,
            evidence=[
                MarineEvidence(
                    source="Ministry of Ports, Shipping and Waterways / Indian Coast Guard",
                    provider="GISProvider",
                    dataset="Indian-Maritime-Boundaries-EEZ",
                    retrieved_at=retrieved_at,
                    quality="HIGH",
                    status=status,
                    evidence_url="https://natmo.gov.in/maritime_zones",
                    metadata={
                        "spatial_engine": provider_name,
                        "restricted_zone_found": summary.restricted_zone,
                        "nearest_port": summary.nearest_port.get("name")
                    }
                )
            ]
        )
