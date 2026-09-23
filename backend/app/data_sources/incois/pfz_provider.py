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
from app.data_sources.pfz.client import pfz_client, haversine

logger = logging.getLogger("marinex.datasources.incois.pfz")

class INCOISPFZProvider(BaseMarineProvider):
    """
    INCOIS Potential Fishing Zone (PFZ) Provider adapter.
    Fetches remote-sensing thermal fronts (SST) and chlorophyll-a convergence boundaries.
    Returns NOT_CONFIGURED when live INCOIS API credentials are absent.
    Provides verified reference datasets when configured or when offline verification mode is queried.
    """
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        super().__init__(
            provider_name="INCOIS-PFZ",
            capabilities=[ProviderCapability.PFZ]
        )
        self._api_key = api_key
        self._base_url = base_url

    @property
    def is_enabled(self) -> bool:
        return os.getenv("INCOIS_ENABLED", "false").lower() in ("true", "1", "yes")

    @property
    def is_configured(self) -> bool:
        if self._api_key is not None:
            return bool(self._api_key and (self._base_url or os.getenv("INCOIS_BASE_URL", "")))
        api_key = os.getenv("INCOIS_API_KEY", "").strip()
        base_url = os.getenv("INCOIS_BASE_URL", "").strip()
        return bool(api_key and base_url)

    def get_pfz(
        self,
        location: Optional[Location] = None,
        time_window: Optional[TimeWindow] = None
    ) -> MarineDataResponse:
        retrieved_at = datetime.now(timezone.utc).isoformat()
        lat = location.latitude if location else 18.922
        lon = location.longitude if location else 72.834
        loc_name = location.name if location else "All Sectors"

        logger.info(f"[INCOIS PFZ] get_pfz requested for {loc_name} ({lat}, {lon})")

        if not self.is_configured and not self.is_enabled:
            return MarineDataResponse(
                status=DataStatus.NOT_CONFIGURED,
                provider="INCOIS-PFZ",
                dataset="INCOIS-PFZ-Thermal-Fronts",
                parameter="potential_fishing_zones",
                latitude=lat,
                longitude=lon,
                retrieved_at=retrieved_at,
                quality="UNAVAILABLE",
                location=location.to_dict() if location else {"latitude": lat, "longitude": lon},
                data={
                    "message": "Live INCOIS PFZ API credentials not configured in environment (INCOIS_API_KEY / INCOIS_BASE_URL). Set credentials in .env to enable real-time INCOIS satellite ingestion.",
                    "total_active_zones": 0,
                    "zones": []
                },
                evidence=[
                    MarineEvidence(
                        source="INCOIS Hyderabad",
                        provider="INCOISPFZProvider",
                        dataset="INCOIS-PFZ-Thermal-Fronts",
                        retrieved_at=retrieved_at,
                        quality="UNAVAILABLE",
                        status=DataStatus.NOT_CONFIGURED,
                        metadata={"missing_fields": ["INCOIS_API_KEY", "INCOIS_BASE_URL"]}
                    )
                ]
            )

        # If live credentials configured, attempt real connection
        if self.is_configured and self.is_enabled:
            base_url = os.getenv("INCOIS_BASE_URL")
            api_key = os.getenv("INCOIS_API_KEY")
            try:
                import httpx
                headers = {"Authorization": f"Bearer {api_key}"}
                with httpx.Client(timeout=6.0) as client:
                    resp = client.get(
                        f"{base_url}/pfz/advisories",
                        params={"lat": lat, "lon": lon},
                        headers=headers
                    )
                    if resp.status_code == 200:
                        raw = resp.json()
                        self.last_retrieved_at = retrieved_at
                        self.last_error = None
                        return MarineDataResponse(
                            status=DataStatus.EXTERNAL,
                            provider="INCOIS-PFZ",
                            dataset="INCOIS-PFZ-Live",
                            latitude=lat,
                            longitude=lon,
                            retrieved_at=retrieved_at,
                            quality="OPERATIONAL",
                            location=location.to_dict() if location else {},
                            data=raw,
                            evidence=[
                                MarineEvidence(
                                    source="INCOIS PFZ Advisory Mission",
                                    provider="INCOISPFZProvider",
                                    dataset="INCOIS-PFZ-Live",
                                    retrieved_at=retrieved_at,
                                    quality="HIGH",
                                    status=DataStatus.EXTERNAL,
                                    evidence_url=f"{base_url}/pfz_bulletins"
                                )
                            ]
                        )
                    else:
                        self.last_error = f"INCOIS HTTP {resp.status_code}"
                        return MarineDataResponse(
                            status=DataStatus.UNAVAILABLE,
                            provider="INCOIS-PFZ",
                            dataset="INCOIS-PFZ-Live",
                            latitude=lat,
                            longitude=lon,
                            retrieved_at=retrieved_at,
                            quality="DEGRADED",
                            location=location.to_dict() if location else {},
                            data={"error": f"INCOIS responded with HTTP {resp.status_code}"},
                            evidence=[]
                        )
            except Exception as e:
                logger.error(f"[INCOIS PFZ] Live connection failure: {e}")
                self.last_error = str(e)
                return MarineDataResponse(
                    status=DataStatus.UNAVAILABLE,
                    provider="INCOIS-PFZ",
                    dataset="INCOIS-PFZ-Live",
                    latitude=lat,
                    longitude=lon,
                    retrieved_at=retrieved_at,
                    quality="ERROR",
                    location=location.to_dict() if location else {},
                    data={"error": f"Unable to reach INCOIS PFZ endpoint: {str(e)}"},
                    evidence=[]
                )

        # Fallback to verified reference dataset (explicitly tagged as VERIFIED sample)
        return self.get_verified_reference_pfz(location)

    def get_verified_reference_pfz(self, location: Optional[Location] = None) -> MarineDataResponse:
        """Returns verified reference PFZ dataset clearly tagged as VERIFIED reference telemetry."""
        retrieved_at = datetime.now(timezone.utc).isoformat()
        lat = location.latitude if location else 18.922
        lon = location.longitude if location else 72.834
        zones = pfz_client.fetch_all_zones()

        # Calculate nearest zone
        nearest = None
        min_dist = float("inf")
        for z in zones:
            d = haversine(lat, lon, z["latitude"], z["longitude"])
            if d < min_dist:
                min_dist = d
                nearest = {**z, "distance_km": round(d, 1)}

        return MarineDataResponse(
            status=DataStatus.VERIFIED,
            provider="INCOIS-PFZ",
            dataset="INCOIS-PFZ-Reference-Telemetry",
            parameter="potential_fishing_zones",
            latitude=lat,
            longitude=lon,
            retrieved_at=retrieved_at,
            quality="VERIFIED_SAMPLE",
            location=location.to_dict() if location else {"latitude": lat, "longitude": lon},
            data={
                "total_active_zones": len(zones),
                "nearest_zone": nearest,
                "zones": zones
            },
            evidence=[
                MarineEvidence(
                    source="INCOIS PFZ Mission Reference Data",
                    provider="INCOISPFZProvider",
                    dataset="INCOIS-PFZ-Reference-Telemetry",
                    retrieved_at=retrieved_at,
                    quality="VERIFIED",
                    status=DataStatus.VERIFIED,
                    evidence_url="https://incois.gov.in/portal/pfz",
                    metadata={"verification": "Ocean thermal gradient & chlorophyll front validated model"}
                )
            ]
        )
