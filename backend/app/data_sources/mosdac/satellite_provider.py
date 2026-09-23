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

logger = logging.getLogger("marinex.datasources.mosdac")

class MOSDACSatelliteProvider(BaseMarineProvider):
    """
    ISRO Meteorological and Oceanographic Satellite Data Archival Centre (MOSDAC) Provider.
    Interfaces Oceansat-3, INSAT-3D, and SCATSAT ocean wind vectors, Sea Surface Temperature (SST),
    and ocean color data.
    Strictly returns NOT_CONFIGURED when user/pass/dataset credentials are not present.
    """
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        super().__init__(
            provider_name="MOSDAC",
            capabilities=[ProviderCapability.SATELLITE]
        )
        self._api_key = api_key
        self._base_url = base_url

    @property
    def is_enabled(self) -> bool:
        return os.getenv("MOSDAC_ENABLED", "false").lower() in ("true", "1", "yes")

    @property
    def is_configured(self) -> bool:
        if self._api_key is not None:
            return bool(self._api_key)
        username = os.getenv("MOSDAC_USERNAME", "").strip()
        password = os.getenv("MOSDAC_PASSWORD", "").strip()
        return bool(username and password)

    def get_satellite_data(
        self,
        location: Optional[Location] = None,
        product: str = "sst",
        time_window: Optional[TimeWindow] = None
    ) -> MarineDataResponse:
        retrieved_at = datetime.now(timezone.utc).isoformat()
        lat = location.latitude if location else 18.922
        lon = location.longitude if location else 72.834

        logger.info(f"[MOSDAC Provider] get_satellite_data requested for product '{product}' at ({lat}, {lon})")

        # Guardrail: Without credentials, strictly return NOT_CONFIGURED
        if not self.is_configured or not self.is_enabled:
            logger.info("[MOSDAC Provider] MOSDAC credentials not configured. Returning NOT_CONFIGURED status.")
            return MarineDataResponse(
                status=DataStatus.NOT_CONFIGURED,
                provider="MOSDAC",
                dataset="ISRO-Oceansat-3/INSAT-3D",
                parameter=product,
                latitude=lat,
                longitude=lon,
                retrieved_at=retrieved_at,
                quality="NOT_CONFIGURED",
                location=location.to_dict() if location else {"latitude": lat, "longitude": lon},
                data={
                    "message": "ISRO MOSDAC satellite API is not configured. Missing credentials (MOSDAC_USERNAME, MOSDAC_PASSWORD, MOSDAC_DATASET_ID). Set in environment to enable live earth observation passes.",
                    "product": product,
                    "satellite_mission": "ISRO Oceansat-3",
                    "available_products": ["sst", "chlorophyll", "ocean_winds", "altimetry"]
                },
                evidence=[
                    MarineEvidence(
                        source="ISRO MOSDAC",
                        provider="MOSDACSatelliteProvider",
                        dataset="ISRO-Oceansat-3",
                        retrieved_at=retrieved_at,
                        quality="UNAVAILABLE",
                        status=DataStatus.NOT_CONFIGURED,
                        evidence_url="https://www.mosdac.gov.in",
                        metadata={"missing_fields": ["MOSDAC_USERNAME", "MOSDAC_PASSWORD"]}
                    )
                ]
            )

        # If configured, attempt authenticated request to MOSDAC API
        base_url = os.getenv("MOSDAC_BASE_URL", "https://api.mosdac.gov.in")
        username = os.getenv("MOSDAC_USERNAME")
        password = os.getenv("MOSDAC_PASSWORD")
        dataset_id = os.getenv("MOSDAC_DATASET_ID", "OS3_SST_L3")

        try:
            import httpx
            with httpx.Client(timeout=8.0) as client:
                resp = client.get(
                    f"{base_url}/catalog/granules",
                    params={"dataset": dataset_id, "lat": lat, "lon": lon, "product": product},
                    auth=(username, password)
                )
                if resp.status_code == 200:
                    raw = resp.json()
                    self.last_retrieved_at = retrieved_at
                    self.last_error = None
                    return MarineDataResponse(
                        status=DataStatus.EXTERNAL,
                        provider="MOSDAC",
                        dataset=dataset_id,
                        parameter=product,
                        latitude=lat,
                        longitude=lon,
                        retrieved_at=retrieved_at,
                        quality="OPERATIONAL",
                        location=location.to_dict() if location else {},
                        data=raw,
                        evidence=[
                            MarineEvidence(
                                source="ISRO MOSDAC",
                                provider="MOSDACSatelliteProvider",
                                dataset=dataset_id,
                                retrieved_at=retrieved_at,
                                quality="HIGH",
                                status=DataStatus.EXTERNAL,
                                evidence_url=f"{base_url}/granule/{raw.get('granule_id', 'recent')}"
                            )
                        ]
                    )
                else:
                    self.last_error = f"MOSDAC HTTP {resp.status_code}"
                    return MarineDataResponse(
                        status=DataStatus.UNAVAILABLE,
                        provider="MOSDAC",
                        dataset=dataset_id,
                        parameter=product,
                        latitude=lat,
                        longitude=lon,
                        retrieved_at=retrieved_at,
                        quality="DEGRADED",
                        location=location.to_dict() if location else {},
                        data={"error": f"MOSDAC API returned status {resp.status_code}"},
                        evidence=[]
                    )
        except Exception as e:
            logger.error(f"[MOSDAC Provider] Live connection failure: {e}")
            self.last_error = str(e)
            return MarineDataResponse(
                status=DataStatus.UNAVAILABLE,
                provider="MOSDAC",
                dataset=dataset_id,
                parameter=product,
                latitude=lat,
                longitude=lon,
                retrieved_at=retrieved_at,
                quality="ERROR",
                location=location.to_dict() if location else {},
                data={"error": f"Unable to reach MOSDAC service: {str(e)}"},
                evidence=[]
            )
