import os
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from app.data_sources.common.base_provider import BaseMarineProvider
from app.data_sources.common.models import ProviderCapability
from app.data_sources.common.provider_status import ProviderStatus
from app.data_sources.common.exceptions import (
    ProviderNotConfiguredError,
    ProviderUnavailableError,
    MarineDataFormatError,
)
from app.data_sources.imd.client import IMDClient
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
    Phase 5B compliant: delegates to IMDClient, normalizes to WeatherData,
    includes freshness, and strictly returns NOT_CONFIGURED when unconfigured.
    """
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        super().__init__(
            provider_name="IMD",
            capabilities=[ProviderCapability.WEATHER, ProviderCapability.HAZARDS]
        )
        self.client = IMDClient(api_key=api_key, base_url=base_url)

    @property
    def is_enabled(self) -> bool:
        return os.getenv("IMD_ENABLED", "false").lower() in ("true", "1", "yes")

    @property
    def is_configured(self) -> bool:
        return self.client.is_configured

    @property
    def status(self) -> ProviderStatus:
        if not self.is_enabled or not self.is_configured:
            return ProviderStatus.NOT_CONFIGURED
        if self.last_error:
            if "unavailable" in self.last_error.lower() or "timeout" in self.last_error.lower():
                return ProviderStatus.UNAVAILABLE
            return ProviderStatus.ERROR
        return ProviderStatus.CONNECTED

    def get_weather(
        self,
        location: Location,
        time_window: Optional[TimeWindow] = None
    ) -> MarineDataResponse:
        logger.info(f"[IMD Provider] get_weather requested for {location.name or 'Coastal Sector'} ({location.latitude:.3f}, {location.longitude:.3f})")
        retrieved_at = datetime.now(timezone.utc).isoformat()

        if not self.is_enabled:
            return MarineDataResponse(
                status=DataStatus.NOT_CONFIGURED,
                provider="IMD",
                dataset="IMD-AWS-Coastal",
                parameter="weather_conditions",
                latitude=location.latitude,
                longitude=location.longitude,
                observed_at="UNAVAILABLE",
                valid_from=None,
                valid_until=None,
                retrieved_at=retrieved_at,
                quality="UNAVAILABLE",
                location=location.to_dict(),
                data={
                    "message": "IMD weather provider is disabled (IMD_ENABLED=false).",
                    "disclaimer": "IMD weather API is disabled or not configured in environment."
                },
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
            logger.info("[IMD Provider] IMD credentials missing (IMD_API_KEY / IMD_BASE_URL). Returning NOT_CONFIGURED.")
            return MarineDataResponse(
                status=DataStatus.NOT_CONFIGURED,
                provider="IMD",
                dataset="IMD-AWS-Coastal",
                parameter="weather_conditions",
                latitude=location.latitude,
                longitude=location.longitude,
                observed_at="UNAVAILABLE",
                valid_from=None,
                valid_until=None,
                retrieved_at=retrieved_at,
                quality="NOT_CONFIGURED",
                location=location.to_dict(),
                data={
                    "message": "IMD API credentials not configured in environment (IMD_API_KEY / IMD_BASE_URL). Set in .env to enable real-time IMD coastal telemetry.",
                    "disclaimer": "IMD API credentials not configured in environment (IMD_API_KEY / IMD_BASE_URL)."
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

        # Configured: invoke dedicated client
        try:
            obs = self.client.fetch_coastal_weather(
                latitude=location.latitude,
                longitude=location.longitude,
                station_id=location.port
            )
            self.last_retrieved_at = retrieved_at
            self.last_error = None

            warnings: List[str] = []
            if obs.cyclone_warning:
                warnings.append(f"CYCLONE ADVISORY: {obs.cyclone_warning}")
            if obs.squall_warning:
                warnings.append(f"SQUALL WARNING: {obs.squall_warning}")

            storm_risk = "low"
            if (obs.wind_speed_knots and obs.wind_speed_knots >= 25.0) or obs.cyclone_warning:
                storm_risk = "high"
            elif (obs.wind_speed_knots and obs.wind_speed_knots >= 17.0) or obs.squall_warning:
                storm_risk = "moderate"

            weather_data = WeatherData(
                temperature=obs.air_temperature_c,
                apparent_temperature=obs.air_temperature_c,
                wind_speed=obs.wind_speed_knots,
                wind_speed_knots=obs.wind_speed_knots,
                wind_direction=obs.wind_direction_text,
                wind_direction_deg=obs.wind_direction_deg,
                humidity=obs.relative_humidity_percent,
                rain_probability=obs.rain_probability_percent,
                precipitation_mm=obs.precipitation_mm,
                weather_condition=obs.weather_condition or "Coastal Marine Observation",
                storm_risk=storm_risk,
                visibility_km=obs.visibility_km,
                pressure_hpa=obs.pressure_hpa,
                warnings=warnings
            )

            observed_time = obs.observation_time or retrieved_at

            return MarineDataResponse(
                status=DataStatus.EXTERNAL,
                provider="IMD",
                dataset="IMD-Coastal-AWS",
                parameter="weather_conditions",
                latitude=location.latitude,
                longitude=location.longitude,
                observed_at=observed_time,
                valid_from=observed_time,
                valid_until=obs.valid_until,
                retrieved_at=retrieved_at,
                quality="HIGH",
                location=location.to_dict(),
                data=weather_data.model_dump(),
                evidence=[
                    MarineEvidence(
                        source="India Meteorological Department",
                        provider="IMDWeatherProvider",
                        dataset="IMD-Coastal-AWS",
                        observed_at=observed_time,
                        valid_until=obs.valid_until,
                        retrieved_at=retrieved_at,
                        quality="HIGH",
                        status=DataStatus.EXTERNAL,
                        evidence_url=f"{self.client.base_url}/bulletins",
                        metadata={
                            "station_name": obs.station_name,
                            "station_id": obs.station_id,
                            "source_reference": "IMD Operational Marine Bulletin"
                        }
                    )
                ]
            )
        except ProviderUnavailableError as e:
            logger.warning(f"[IMD Provider] IMD service unavailable: {e}")
            self.last_error = str(e)
            return MarineDataResponse(
                status=DataStatus.UNAVAILABLE,
                provider="IMD",
                dataset="IMD-Coastal-AWS",
                parameter="weather_conditions",
                latitude=location.latitude,
                longitude=location.longitude,
                observed_at="UNAVAILABLE",
                retrieved_at=retrieved_at,
                quality="DEGRADED",
                location=location.to_dict(),
                data={"error": f"IMD service temporarily unavailable: {str(e)}"},
                evidence=[
                    MarineEvidence(
                        source="IMD",
                        provider="IMDWeatherProvider",
                        dataset="IMD-Coastal-AWS",
                        retrieved_at=retrieved_at,
                        quality="UNAVAILABLE",
                        status=DataStatus.UNAVAILABLE,
                        metadata={"error": str(e)}
                    )
                ]
            )
        except Exception as e:
            logger.error(f"[IMD Provider] Unexpected error: {e}")
            self.last_error = str(e)
            return MarineDataResponse(
                status=DataStatus.ERROR,
                provider="IMD",
                dataset="IMD-Coastal-AWS",
                parameter="weather_conditions",
                latitude=location.latitude,
                longitude=location.longitude,
                observed_at="UNAVAILABLE",
                retrieved_at=retrieved_at,
                quality="ERROR",
                location=location.to_dict(),
                data={"error": f"IMD provider failure: {str(e)}"},
                evidence=[]
            )
