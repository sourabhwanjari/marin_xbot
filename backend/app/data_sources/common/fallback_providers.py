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
from app.data_sources.weather.service import weather_service
from app.data_sources.ocean.service import ocean_service

logger = logging.getLogger("marinex.datasources.fallback")

class OpenMeteoWeatherProvider(BaseMarineProvider):
    """
    Open-Meteo Global Marine Weather Provider.
    Acts as a verified global atmospheric model provider and demo fallback.
    """
    def __init__(self):
        super().__init__(
            provider_name="Open-Meteo",
            capabilities=[ProviderCapability.WEATHER]
        )

    @property
    def is_enabled(self) -> bool:
        return True

    @property
    def is_configured(self) -> bool:
        return True  # Open-Meteo open tier requires no API key

    def get_weather(
        self,
        location: Location,
        time_window: Optional[TimeWindow] = None
    ) -> MarineDataResponse:
        retrieved_at = datetime.now(timezone.utc).isoformat()
        ctx = time_window.context if time_window else "current"

        res = weather_service.get_weather(
            latitude=location.latitude,
            longitude=location.longitude,
            location_name=location.name or "Coastal Sector",
            time_context=ctx
        )

        status = DataStatus.EXTERNAL if res.status == "external" else DataStatus.DEMO
        data = {
            "temperature": res.temperature,
            "wind_speed": res.wind_speed,
            "wind_direction": res.wind_direction,
            "rain_probability": res.rain_probability,
            "storm_risk": "high" if (res.wind_speed or 0) > 22 else ("moderate" if (res.wind_speed or 0) > 16 else "low"),
            "weather_condition": res.weather_condition,
            "warnings": res.warnings,
            "units": res.units
        }

        return MarineDataResponse(
            status=status,
            provider="Open-Meteo",
            dataset="Open-Meteo-Global-Weather",
            parameter="weather_conditions",
            latitude=location.latitude,
            longitude=location.longitude,
            observed_at=retrieved_at,
            retrieved_at=retrieved_at,
            quality="OPERATIONAL" if status == DataStatus.EXTERNAL else "SIMULATED",
            location=location.to_dict(),
            data=data,
            evidence=[
                MarineEvidence(
                    source="Open-Meteo Meteorological Telemetry",
                    provider="OpenMeteoWeatherProvider",
                    dataset="Open-Meteo-Global-Weather",
                    retrieved_at=retrieved_at,
                    quality="OPERATIONAL" if status == DataStatus.EXTERNAL else "SIMULATED",
                    status=status,
                    evidence_url="https://open-meteo.com/en/docs",
                    metadata={"source_reference": res.source_reference}
                )
            ]
        )

class OpenMeteoOceanProvider(BaseMarineProvider):
    """
    Open-Meteo Marine / Copernicus Marine Wave Model Provider.
    Acts as a verified global hydrodynamic ocean model provider and demo fallback.
    """
    def __init__(self):
        super().__init__(
            provider_name="Open-Meteo-Marine",
            capabilities=[ProviderCapability.OCEAN]
        )

    @property
    def is_enabled(self) -> bool:
        return True

    @property
    def is_configured(self) -> bool:
        return True

    def get_ocean_conditions(
        self,
        location: Location,
        time_window: Optional[TimeWindow] = None
    ) -> MarineDataResponse:
        retrieved_at = datetime.now(timezone.utc).isoformat()
        ctx = time_window.context if time_window else "current"

        res = ocean_service.get_ocean_conditions(
            latitude=location.latitude,
            longitude=location.longitude,
            location_name=location.name or "Coastal Sector",
            time_context=ctx
        )

        status = DataStatus.EXTERNAL if res.status == "external" else DataStatus.DEMO
        data = {
            "sst": res.sea_surface_temperature,
            "chlorophyll": res.chlorophyll,
            "wave_height": res.wave_height,
            "swell_period": res.swell_period,
            "ocean_condition": res.ocean_condition,
            "tide_status": res.tide_status,
            "units": res.units
        }

        return MarineDataResponse(
            status=status,
            provider="Open-Meteo-Marine",
            dataset="Copernicus-Marine-Hydrodynamics",
            parameter="ocean_state",
            latitude=location.latitude,
            longitude=location.longitude,
            observed_at=retrieved_at,
            retrieved_at=retrieved_at,
            quality="OPERATIONAL" if status == DataStatus.EXTERNAL else "SIMULATED",
            location=location.to_dict(),
            data=data,
            evidence=[
                MarineEvidence(
                    source="Copernicus Marine / Open-Meteo Wave Service",
                    provider="OpenMeteoOceanProvider",
                    dataset="Copernicus-Marine-Hydrodynamics",
                    retrieved_at=retrieved_at,
                    quality="OPERATIONAL" if status == DataStatus.EXTERNAL else "SIMULATED",
                    status=status,
                    evidence_url="https://open-meteo.com/en/docs/marine-weather-api",
                    metadata={"source_reference": res.source_reference}
                )
            ]
        )
