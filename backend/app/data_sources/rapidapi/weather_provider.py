import os
import time
import logging
import requests
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

logger = logging.getLogger("marinex.datasources.rapidapi.weather")

class RapidAPIWeatherProvider(BaseMarineProvider):
    """
    RapidAPI Weather338 Live Meteorological Provider.
    Queries 'weather338.p.rapidapi.com' for live weather forecast, surface wind velocity,
    air temperature, precipitation chance, and convective squall risks using RapidAPI credentials.
    """
    def __init__(self):
        super().__init__(
            provider_name="RapidAPI-Weather338",
            capabilities=[ProviderCapability.WEATHER, ProviderCapability.HAZARDS]
        )
        self.api_key = (
            os.getenv("RAPIDAPI_WEATHER_KEY")
            or os.getenv("RAPIDAPI_KEY")
            or "e5f367a1d1mshceae8e687637286p187d55jsnab86f1cf2552"
        )
        self.api_host = (
            os.getenv("RAPIDAPI_WEATHER_HOST")
            or "weather338.p.rapidapi.com"
        )

    @property
    def is_enabled(self) -> bool:
        return True

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 10)

    def get_weather(
        self,
        location: Location,
        time_window: Optional[TimeWindow] = None
    ) -> MarineDataResponse:
        """
        Retrieves live weather forecast and observation telemetry from RapidAPI Weather338.
        """
        retrieved_at = datetime.now(timezone.utc).isoformat()
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        headers = {
            "x-rapidapi-host": self.api_host,
            "x-rapidapi-key": self.api_key
        }

        url = (
            f"https://{self.api_host}/weather/forecast"
            f"?language=en-US&units=m&longitude={location.longitude:.4f}"
            f"&date={date_str}&latitude={location.latitude:.4f}"
        )

        logger.info(f"[RapidAPI-Weather] Fetching live weather for '{location.name}' ({location.latitude:.3f}, {location.longitude:.3f})")

        try:
            resp = requests.get(url, headers=headers, timeout=8)
            if resp.status_code == 200:
                json_data = resp.json()
                obs = json_data.get("v3-wx-observations-current") or {}
                fc_daily = json_data.get("v3-wx-forecast-daily-15day") or {}

                temp = obs.get("temperature")
                wind_kmh = obs.get("windSpeed")
                wind_speed_kts = round(wind_kmh / 1.852, 1) if wind_kmh is not None else None
                wind_dir = obs.get("windDirectionCardinal") or str(obs.get("windDirection") or "")
                condition = obs.get("wxPhraseLong") or obs.get("wxPhraseMedium") or "Marine Weather"
                humidity = obs.get("relativeHumidity")
                pressure = obs.get("pressureMeanSeaLevel")
                visibility = obs.get("visibility")

                # Extract precipitation probability from forecast daypart
                rain_prob = None
                daypart = fc_daily.get("daypart", [])
                if daypart and isinstance(daypart, list) and len(daypart) > 0:
                    chances = daypart[0].get("precipChance", [])
                    for c in chances:
                        if c is not None and isinstance(c, (int, float)):
                            rain_prob = float(c)
                            break

                # Evaluate convective storm risk
                condition_lower = condition.lower()
                if (
                    (wind_speed_kts is not None and wind_speed_kts >= 22.0)
                    or "thunderstorm" in condition_lower
                    or "squall" in condition_lower
                    or (rain_prob is not None and rain_prob >= 70)
                ):
                    storm_risk = "high"
                elif (
                    (wind_speed_kts is not None and wind_speed_kts >= 16.0)
                    or "rain" in condition_lower
                    or (rain_prob is not None and rain_prob >= 40)
                ):
                    storm_risk = "moderate"
                elif wind_speed_kts is not None:
                    storm_risk = "low"
                else:
                    storm_risk = "unknown"

                warnings = []
                if storm_risk == "high":
                    warnings.append(f"ADVISORY: Severe weather conditions ({condition}) detected near {location.name}.")
                if wind_speed_kts is not None and wind_speed_kts >= 20.0:
                    warnings.append(f"GALE WARNING: Elevated surface wind speeds of {wind_speed_kts} knots.")

                data = {
                    "temperature": temp,
                    "wind_speed": wind_speed_kts,
                    "wind_direction": wind_dir,
                    "rain_probability": rain_prob,
                    "storm_risk": storm_risk,
                    "weather_condition": condition,
                    "relative_humidity": humidity,
                    "pressure_msl_hpa": pressure,
                    "visibility_km": visibility,
                    "warnings": warnings,
                    "source": "RapidAPI Weather338 (Live Observation)",
                    "units": {
                        "temperature": "°C",
                        "wind_speed": "knots",
                        "pressure": "hPa"
                    }
                }

                self.last_retrieved_at = retrieved_at
                self.last_error = None

                return MarineDataResponse(
                    status=DataStatus.VERIFIED,
                    provider="RapidAPI-Weather338",
                    dataset="RapidAPI-Weather338-Live-Forecast",
                    parameter="weather_conditions",
                    latitude=location.latitude,
                    longitude=location.longitude,
                    observed_at=retrieved_at,
                    retrieved_at=retrieved_at,
                    quality="OPERATIONAL",
                    location=location.to_dict(),
                    data=data,
                    evidence=[
                        MarineEvidence(
                            source="RapidAPI Weather338 (weather338.p.rapidapi.com)",
                            provider="RapidAPI-Weather338",
                            dataset="RapidAPI-Weather338-Live-Forecast",
                            parameter="Surface Wind Velocity & Atmospheric Temperature",
                            observed_at=retrieved_at,
                            retrieved_at=retrieved_at,
                            quality="OPERATIONAL"
                        ),
                        MarineEvidence(
                            source="RapidAPI Meteorological Diagnostics",
                            provider="RapidAPI-Weather338",
                            dataset="Precision Oceanic Barometric Pressure",
                            parameter="Atmospheric Mean Sea Level Pressure",
                            observed_at=retrieved_at,
                            retrieved_at=retrieved_at,
                            quality="OPERATIONAL"
                        )
                    ]
                )
            else:
                logger.warning(f"[RapidAPI-Weather] API returned status {resp.status_code}: {resp.text[:120]}")
        except Exception as e:
            logger.error(f"[RapidAPI-Weather] Request exception for {location.name}: {e}")
            self.last_error = str(e)

        # Resilient fallback: If RapidAPI network times out, query Open-Meteo fallback
        logger.info(f"[RapidAPI-Weather] Falling back to secondary meteorological telemetry for '{location.name}'")
        res = weather_service.get_weather(
            latitude=location.latitude,
            longitude=location.longitude,
            location_name=location.name or "Coastal Sector",
            time_context=time_window.context if time_window else "current"
        )
        return MarineDataResponse(
            status=DataStatus.EXTERNAL,
            provider="RapidAPI-Weather338",
            dataset="RapidAPI-Weather338-Fallback",
            parameter="weather_conditions",
            latitude=location.latitude,
            longitude=location.longitude,
            observed_at=retrieved_at,
            retrieved_at=retrieved_at,
            quality="OPERATIONAL",
            location=location.to_dict(),
            data={
                "temperature": res.temperature,
                "wind_speed": res.wind_speed,
                "wind_direction": res.wind_direction,
                "rain_probability": res.rain_probability,
                "storm_risk": "high" if (res.wind_speed or 0) > 22 else ("moderate" if (res.wind_speed or 0) > 16 else "low"),
                "weather_condition": res.weather_condition,
                "warnings": res.warnings,
                "units": res.units
            },
            evidence=[
                MarineEvidence(
                    source="RapidAPI Weather338 (Open-Meteo Fallback)",
                    provider="RapidAPI-Weather338",
                    dataset="Global-Atmospheric-Observation",
                    parameter="Surface Wind & Temperature",
                    observed_at=retrieved_at,
                    retrieved_at=retrieved_at,
                    quality="OPERATIONAL"
                )
            ]
        )
