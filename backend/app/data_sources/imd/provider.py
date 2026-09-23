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
from app.marine_models.domains import WeatherData

logger = logging.getLogger("marinex.datasources.imd")

class IMDWeatherProvider(BaseMarineProvider):
    """
    India Meteorological Department (IMD) Marine & Coastal Weather Provider adapter.
    Fetches real-time coastal Automatic Weather Stations (AWS), GFS/WRF forecasts,
    and cyclone/squall advisories when configured.
    Strictly returns NOT_CONFIGURED when API credentials/endpoints are absent.
    """
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        super().__init__(
            provider_name="IMD",
            capabilities=[ProviderCapability.WEATHER, ProviderCapability.HAZARDS]
        )
        self._api_key = api_key
        self._base_url = base_url

    @property
    def is_enabled(self) -> bool:
        return os.getenv("IMD_ENABLED", "false").lower() in ("true", "1", "yes")

    @property
    def is_configured(self) -> bool:
        if self._api_key is not None:
            return bool(self._api_key and (self._base_url or os.getenv("IMD_BASE_URL", "")))
        api_key = os.getenv("IMD_API_KEY", "").strip()
        base_url = os.getenv("IMD_BASE_URL", "").strip()
        return bool(api_key and base_url)

    def get_weather(
        self,
        location: Location,
        time_window: Optional[TimeWindow] = None
    ) -> MarineDataResponse:
        logger.info(f"[IMD Provider] get_weather requested for {location.name or 'Coastal'} ({location.latitude}, {location.longitude})")
        retrieved_at = datetime.now(timezone.utc).isoformat()

        if not self.is_enabled:
            return MarineDataResponse(
                status=DataStatus.NOT_CONFIGURED,
                provider="IMD",
                dataset="IMD-AWS-Coastal",
                parameter="weather_conditions",
                latitude=location.latitude,
                longitude=location.longitude,
                retrieved_at=retrieved_at,
                quality="UNAVAILABLE",
                location=location.to_dict(),
                data={"message": "IMD weather provider is disabled (IMD_ENABLED=false)."},
                evidence=[
                    MarineEvidence(
                        source="IMD",
                        provider="IMDWeatherProvider",
                        dataset="IMD-AWS-Coastal",
                        retrieved_at=retrieved_at,
                        quality="UNAVAILABLE",
                        status=DataStatus.NOT_CONFIGURED,
                        metadata={"reason": "Provider disabled in configuration."}
                    )
                ]
            )

        if not self.is_configured:
            logger.warning("[IMD Provider] Provider is not configured (missing IMD_API_KEY or IMD_BASE_URL)")
            return MarineDataResponse(
                status=DataStatus.NOT_CONFIGURED,
                provider="IMD",
                dataset="IMD-AWS-Coastal",
                parameter="weather_conditions",
                latitude=location.latitude,
                longitude=location.longitude,
                retrieved_at=retrieved_at,
                quality="UNAVAILABLE",
                location=location.to_dict(),
                data={
                    "message": "IMD API credentials not configured in environment (IMD_API_KEY / IMD_BASE_URL). Set credentials in .env to enable real-time IMD feeds."
                },
                evidence=[
                    MarineEvidence(
                        source="IMD",
                        provider="IMDWeatherProvider",
                        dataset="IMD-AWS-Coastal",
                        retrieved_at=retrieved_at,
                        quality="UNAVAILABLE",
                        status=DataStatus.NOT_CONFIGURED,
                        metadata={"missing_fields": ["IMD_API_KEY", "IMD_BASE_URL"]}
                    )
                ]
            )

        # If credentials are configured, execute external HTTP call to IMD API
        base_url = os.getenv("IMD_BASE_URL")
        api_key = os.getenv("IMD_API_KEY")
        try:
            import httpx
            # Query IMD coastal endpoint
            headers = {"Authorization": f"Bearer {api_key}"}
            with httpx.Client(timeout=6.0) as client:
                resp = client.get(
                    f"{base_url}/coastal/weather",
                    params={"lat": location.latitude, "lon": location.longitude},
                    headers=headers
                )
                if resp.status_code == 200:
                    raw = resp.json()
                    self.last_retrieved_at = retrieved_at
                    self.last_error = None
                    return MarineDataResponse(
                        status=DataStatus.EXTERNAL,
                        provider="IMD",
                        dataset="IMD-Coastal-AWS",
                        latitude=location.latitude,
                        longitude=location.longitude,
                        retrieved_at=retrieved_at,
                        quality="OPERATIONAL",
                        location=location.to_dict(),
                        data=raw,
                        evidence=[
                            MarineEvidence(
                                source="India Meteorological Department",
                                provider="IMDWeatherProvider",
                                dataset="IMD-Coastal-AWS",
                                retrieved_at=retrieved_at,
                                quality="HIGH",
                                status=DataStatus.EXTERNAL,
                                evidence_url=f"{base_url}/bulletins",
                                metadata={"station": location.name}
                            )
                        ]
                    )
                else:
                    self.last_error = f"IMD HTTP {resp.status_code}"
                    return MarineDataResponse(
                        status=DataStatus.UNAVAILABLE,
                        provider="IMD",
                        dataset="IMD-Coastal-AWS",
                        latitude=location.latitude,
                        longitude=location.longitude,
                        retrieved_at=retrieved_at,
                        quality="DEGRADED",
                        location=location.to_dict(),
                        data={"error": f"IMD responded with status {resp.status_code}"},
                        evidence=[]
                    )
        except Exception as e:
            logger.error(f"[IMD Provider] Connection failure: {e}")
            self.last_error = str(e)
            return MarineDataResponse(
                status=DataStatus.UNAVAILABLE,
                provider="IMD",
                dataset="IMD-Coastal-AWS",
                latitude=location.latitude,
                longitude=location.longitude,
                retrieved_at=retrieved_at,
                quality="ERROR",
                location=location.to_dict(),
                data={"error": f"Unable to reach IMD endpoint: {str(e)}"},
                evidence=[]
            )
