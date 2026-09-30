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

logger = logging.getLogger("marinex.datasources.rapidapi.marineweather")


class RapidAPIMarineWeatherProvider(BaseMarineProvider):
    """
    RapidAPI Marine Weather Provider (ApiVerve).
    Queries 'marine-weather-api-apiverve.p.rapidapi.com/v1/marineweather' for specialized offshore and coastal
    meteorological conditions: surface wind velocity, air temperature extremes, precipitation accumulation,
    humidity, visibility, and marine astronomical/tidal context (sun/moon ephemeris).
    """
    def __init__(self):
        super().__init__(
            provider_name="RapidAPI-MarineWeather-ApiVerve",
            capabilities=[ProviderCapability.WEATHER, ProviderCapability.HAZARDS]
        )
        self.api_key = (
            os.getenv("RAPIDAPI_MARINE_WEATHER_KEY")
            or os.getenv("RAPIDAPI_KEY")
            or "e5f367a1d1mshceae8e687637286p187d55jsnab86f1cf2552"
        )
        self.api_host = (
            os.getenv("RAPIDAPI_MARINE_WEATHER_HOST")
            or "marine-weather-api-apiverve.p.rapidapi.com"
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
        Retrieves live marine meteorological forecast & ephemeris from ApiVerve Marine Weather API.
        """
        retrieved_at = datetime.now(timezone.utc).isoformat()
        headers = {
            "x-rapidapi-host": self.api_host,
            "x-rapidapi-key": self.api_key,
            "Accept": "application/json"
        }

        url = f"https://{self.api_host}/v1/marineweather?lat={location.latitude:.4f}&lon={location.longitude:.4f}"
        logger.info(f"[RapidAPI-MarineWeather] Fetching marine weather for '{location.name}' ({location.latitude:.3f}, {location.longitude:.3f})")

        try:
            resp = requests.get(url, headers=headers, timeout=8)
            if resp.status_code == 200:
                json_data = resp.json()
                weather = json_data.get("data", {}).get("weather", {}) if isinstance(json_data.get("data"), dict) else {}

                condition = weather.get("condition") or "Marine Weather"
                avg_temp = weather.get("avgtempc")
                max_temp = weather.get("maxtempc")
                min_temp = weather.get("mintempc")
                max_wind_kph = weather.get("maxwindkph")
                wind_kts = round(max_wind_kph / 1.852, 1) if max_wind_kph is not None else None
                precip_mm = weather.get("totalprecipmm")
                humidity = weather.get("avghumidity")
                visibility_km = weather.get("avgviskm")
                uv_index = weather.get("uv")
                sunrise = weather.get("sunrise")
                sunset = weather.get("sunset")
                moon_phase = weather.get("moonphase")
                moon_illum = weather.get("moonillumination")

                # Convective storm & sea state risk calculation
                cond_lower = condition.lower()
                if (
                    (wind_kts is not None and wind_kts >= 22.0)
                    or "thunderstorm" in cond_lower
                    or "squall" in cond_lower
                    or (precip_mm is not None and precip_mm >= 25.0)
                ):
                    storm_risk = "high"
                elif (
                    (wind_kts is not None and wind_kts >= 16.0)
                    or "rain" in cond_lower
                    or (precip_mm is not None and precip_mm >= 5.0)
                ):
                    storm_risk = "moderate"
                elif wind_kts is not None:
                    storm_risk = "low"
                else:
                    storm_risk = "unknown"

                warnings = []
                if storm_risk == "high":
                    warnings.append(f"ADVISORY: Severe marine weather conditions ({condition}) forecast near {location.name}.")
                if wind_kts is not None and wind_kts >= 20.0:
                    warnings.append(f"GALE ADVISORY: Surface gusts up to {wind_kts} knots.")

                data = {
                    "temperature": avg_temp,
                    "max_temperature": max_temp,
                    "min_temperature": min_temp,
                    "wind_speed": wind_kts,
                    "wind_direction": "VRB",
                    "rain_probability": min(100, int((precip_mm or 0) * 15)) if precip_mm else 0,
                    "precipitation_mm": precip_mm,
                    "relative_humidity": humidity,
                    "visibility_km": visibility_km,
                    "uv_index": uv_index,
                    "storm_risk": storm_risk,
                    "weather_condition": condition,
                    "astronomical": {
                        "sunrise": sunrise,
                        "sunset": sunset,
                        "moon_phase": moon_phase,
                        "moon_illumination": moon_illum
                    },
                    "warnings": warnings,
                    "source": f"RapidAPI Marine Weather ({self.api_host})",
                    "units": {
                        "temperature": "°C",
                        "wind_speed": "knots",
                        "precipitation": "mm"
                    }
                }

                self.last_retrieved_at = retrieved_at
                self.last_error = None

                return MarineDataResponse(
                    status=DataStatus.VERIFIED,
                    provider="RapidAPI-MarineWeather-ApiVerve",
                    dataset="ApiVerve-Marine-Weather-Live",
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
                            source=f"RapidAPI Marine Weather ApiVerve ({self.api_host})",
                            provider="RapidAPI-MarineWeather-ApiVerve",
                            dataset="ApiVerve-Marine-Weather-Live",
                            parameter="Surface Wind, Precipitation & Oceanic Meteorology",
                            observed_at=retrieved_at,
                            retrieved_at=retrieved_at,
                            quality="OPERATIONAL"
                        ),
                        MarineEvidence(
                            source="ApiVerve Marine Astronomical Diagnostics",
                            provider="RapidAPI-MarineWeather-ApiVerve",
                            dataset="Offshore Ephemeris & Solar/Lunar Data",
                            parameter="Marine Ephemeris & Illumination",
                            observed_at=retrieved_at,
                            retrieved_at=retrieved_at,
                            quality="OPERATIONAL"
                        )
                    ]
                )
            else:
                logger.warning(f"[RapidAPI-MarineWeather] {self.api_host} returned HTTP {resp.status_code}: {resp.text[:120]}")
        except Exception as e:
            logger.error(f"[RapidAPI-MarineWeather] Request exception for {location.name}: {e}")
            self.last_error = str(e)

        # Resilient fallback: Try RapidAPI Weather338 or Open-Meteo
        logger.info(f"[RapidAPI-MarineWeather] Falling back to secondary meteorological stream for '{location.name}'")
        try:
            from app.data_sources.rapidapi.weather_provider import RapidAPIWeatherProvider
            w338 = RapidAPIWeatherProvider()
            if w338.is_configured:
                res = w338.get_weather(location=location, time_window=time_window)
                if res and res.status in (DataStatus.VERIFIED, DataStatus.EXTERNAL):
                    return res
        except Exception as e:
            logger.warning(f"[RapidAPI-MarineWeather] RapidAPI Weather338 delegation failed: {e}")

        # Secondary fallback: Open-Meteo
        res = weather_service.get_weather(
            latitude=location.latitude,
            longitude=location.longitude,
            location_name=location.name or "Coastal Sector",
            time_context=time_window.context if time_window else "current"
        )
        return MarineDataResponse(
            status=DataStatus.EXTERNAL,
            provider="RapidAPI-MarineWeather-ApiVerve",
            dataset="Global-Marine-Fallback",
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
                    source="RapidAPI Marine Weather (Fallback Model)",
                    provider="RapidAPI-MarineWeather-ApiVerve",
                    dataset="Global-Atmospheric-Observation",
                    parameter="Surface Wind & Temperature",
                    observed_at=retrieved_at,
                    retrieved_at=retrieved_at,
                    quality="OPERATIONAL"
                )
            ]
        )
