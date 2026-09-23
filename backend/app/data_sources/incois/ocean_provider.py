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
from app.marine_models.domains import OceanData

logger = logging.getLogger("marinex.datasources.incois.ocean")

class INCOISOceanProvider(BaseMarineProvider):
    """
    Indian National Centre for Ocean Information Services (INCOIS) Ocean Telemetry Provider.
    Retrieves operational wave models, swell direction, Sea Surface Temperature (SST),
    and ocean sea state forecasts when configured.
    Strictly returns NOT_CONFIGURED when API credentials/endpoints are absent.
    """
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        super().__init__(
            provider_name="INCOIS-Ocean",
            capabilities=[ProviderCapability.OCEAN]
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

    def get_ocean_conditions(
        self,
        location: Location,
        time_window: Optional[TimeWindow] = None
    ) -> MarineDataResponse:
        logger.info(f"[INCOIS Ocean] get_ocean_conditions requested for {location.name or 'Coastal'} ({location.latitude}, {location.longitude})")
        retrieved_at = datetime.now(timezone.utc).isoformat()

        if not self.is_enabled:
            return MarineDataResponse(
                status=DataStatus.NOT_CONFIGURED,
                provider="INCOIS-Ocean",
                dataset="INCOIS-Wave-Hydrodynamic",
                parameter="ocean_state",
                latitude=location.latitude,
                longitude=location.longitude,
                retrieved_at=retrieved_at,
                quality="UNAVAILABLE",
                location=location.to_dict(),
                data={"message": "INCOIS ocean provider is disabled (INCOIS_ENABLED=false)."},
                evidence=[
                    MarineEvidence(
                        source="INCOIS",
                        provider="INCOISOceanProvider",
                        dataset="INCOIS-Wave-Hydrodynamic",
                        retrieved_at=retrieved_at,
                        quality="UNAVAILABLE",
                        status=DataStatus.NOT_CONFIGURED,
                        metadata={"reason": "Provider disabled in configuration."}
                    )
                ]
            )

        if not self.is_configured:
            logger.warning("[INCOIS Ocean] Provider is not configured (missing INCOIS_API_KEY or INCOIS_BASE_URL)")
            return MarineDataResponse(
                status=DataStatus.NOT_CONFIGURED,
                provider="INCOIS-Ocean",
                dataset="INCOIS-Wave-Hydrodynamic",
                parameter="ocean_state",
                latitude=location.latitude,
                longitude=location.longitude,
                retrieved_at=retrieved_at,
                quality="UNAVAILABLE",
                location=location.to_dict(),
                data={
                    "message": "INCOIS API credentials not configured in environment (INCOIS_API_KEY / INCOIS_BASE_URL). Set credentials in .env to enable live INCOIS hydrodynamic ocean state feeds."
                },
                evidence=[
                    MarineEvidence(
                        source="INCOIS",
                        provider="INCOISOceanProvider",
                        dataset="INCOIS-Wave-Hydrodynamic",
                        retrieved_at=retrieved_at,
                        quality="UNAVAILABLE",
                        status=DataStatus.NOT_CONFIGURED,
                        metadata={"missing_fields": ["INCOIS_API_KEY", "INCOIS_BASE_URL"]}
                    )
                ]
            )

        # If credentials are configured, execute external HTTP call to INCOIS API
        base_url = os.getenv("INCOIS_BASE_URL")
        api_key = os.getenv("INCOIS_API_KEY")
        try:
            import httpx
            headers = {"Authorization": f"Bearer {api_key}"}
            with httpx.Client(timeout=6.0) as client:
                resp = client.get(
                    f"{base_url}/ocean/conditions",
                    params={"lat": location.latitude, "lon": location.longitude},
                    headers=headers
                )
                if resp.status_code == 200:
                    raw = resp.json()
                    self.last_retrieved_at = retrieved_at
                    self.last_error = None
                    return MarineDataResponse(
                        status=DataStatus.EXTERNAL,
                        provider="INCOIS-Ocean",
                        dataset="INCOIS-Wave-Hydrodynamic",
                        latitude=location.latitude,
                        longitude=location.longitude,
                        retrieved_at=retrieved_at,
                        quality="OPERATIONAL",
                        location=location.to_dict(),
                        data=raw,
                        evidence=[
                            MarineEvidence(
                                source="INCOIS Hyderabad",
                                provider="INCOISOceanProvider",
                                dataset="INCOIS-Wave-Hydrodynamic",
                                retrieved_at=retrieved_at,
                                quality="HIGH",
                                status=DataStatus.EXTERNAL,
                                evidence_url=f"{base_url}/marine_forecast",
                                metadata={"sector": location.name}
                            )
                        ]
                    )
                else:
                    self.last_error = f"INCOIS HTTP {resp.status_code}"
                    return MarineDataResponse(
                        status=DataStatus.UNAVAILABLE,
                        provider="INCOIS-Ocean",
                        dataset="INCOIS-Wave-Hydrodynamic",
                        latitude=location.latitude,
                        longitude=location.longitude,
                        retrieved_at=retrieved_at,
                        quality="DEGRADED",
                        location=location.to_dict(),
                        data={"error": f"INCOIS responded with status {resp.status_code}"},
                        evidence=[]
                    )
        except Exception as e:
            logger.error(f"[INCOIS Ocean] Connection failure: {e}")
            self.last_error = str(e)
            return MarineDataResponse(
                status=DataStatus.UNAVAILABLE,
                provider="INCOIS-Ocean",
                dataset="INCOIS-Wave-Hydrodynamic",
                latitude=location.latitude,
                longitude=location.longitude,
                retrieved_at=retrieved_at,
                quality="ERROR",
                location=location.to_dict(),
                data={"error": f"Unable to reach INCOIS endpoint: {str(e)}"},
                evidence=[]
            )
