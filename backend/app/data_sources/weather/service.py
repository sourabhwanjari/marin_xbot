import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from app.data_sources.base import DataSource, DataStatus
from app.data_sources.weather.client import weather_client, WMO_WEATHER_CODES, degrees_to_cardinal
from app.marine_gateway.models import NormalizedWeather

logger = logging.getLogger("marinex.datasources.weather.service")

class WeatherService(DataSource):
    """
    Weather Service providing normalized meteorological telemetry.
    Supports Open-Meteo live data with fallback to realistic demo profiles.
    """
    name: str = "weather"
    enabled: bool = True

    def __init__(self):
        self.demo_mode = os.getenv("MARINEX_DEMO_MODE", os.getenv("IS_DEMO", "true")).lower() == "true"

    def health_check(self) -> Dict[str, Any]:
        """Checks connectivity by pinging Open-Meteo."""
        try:
            res = weather_client.fetch_weather(18.922, 72.834)
            if res and "current" in res:
                return {
                    "provider": "Open-Meteo Weather",
                    "status": "online",
                    "latency_ms": res.get("generationtime_ms", 50.0),
                    "is_live": True
                }
            return {
                "provider": "Open-Meteo Weather",
                "status": "degraded",
                "is_live": False,
                "fallback": "demo_available" if self.demo_mode else "none"
            }
        except Exception as e:
            return {
                "provider": "Open-Meteo Weather",
                "status": "offline",
                "error": str(e),
                "is_live": False
            }

    def fetch(self, **kwargs) -> NormalizedWeather:
        lat = kwargs.get("latitude", 18.922)
        lon = kwargs.get("longitude", 72.834)
        loc_name = kwargs.get("location_name", "Coastal Sector")
        time_context = kwargs.get("time_context", "current")
        return self.get_weather(lat, lon, loc_name, time_context)

    def get_weather(
        self,
        latitude: float,
        longitude: float,
        location_name: str = "Coastal Sector",
        time_context: str = "current"
    ) -> NormalizedWeather:
        logger.info(f"[WeatherService] Fetching weather for {location_name} ({latitude}, {longitude})")

        # 1. Try real external provider
        raw = weather_client.fetch_weather(latitude, longitude)
        if raw and "current" in raw:
            curr = raw["current"]
            hourly = raw.get("hourly", {})

            w_code = curr.get("weather_code", 0)
            condition = WMO_WEATHER_CODES.get(w_code, "Fair marine weather")

            # Extract precipitation probability
            rain_prob = 15
            if hourly and "precipitation_probability" in hourly:
                probs = hourly["precipitation_probability"]
                if probs and len(probs) > 0:
                    rain_prob = probs[0] or 15

            wind_spd = curr.get("wind_speed_10m")
            wind_deg = curr.get("wind_direction_10m")
            wind_dir_cardinal = degrees_to_cardinal(wind_deg)

            warnings = []
            if wind_spd and wind_spd >= 22.0:
                warnings.append(f"Gale Warning: Strong wind {wind_spd} kts detected")
            if w_code in [95, 96, 99]:
                warnings.append("Thunderstorm Squall Warning: Lightning/convective risk")

            now_iso = datetime.now(timezone.utc).isoformat()
            valid_until = (datetime.now(timezone.utc) + timedelta(hours=6)).isoformat()

            return NormalizedWeather(
                temperature=curr.get("temperature_2m"),
                wind_speed=wind_spd,
                wind_direction=wind_dir_cardinal,
                wind_direction_deg=wind_deg,
                rain_probability=rain_prob,
                weather_condition=condition,
                visibility=8.5,
                warnings=warnings,
                timestamp=now_iso,
                valid_from=now_iso,
                valid_until=valid_until,
                provider="Open-Meteo Live Weather",
                status="external",
                source_reference="Open-Meteo GFS/ECMWF Model Ensemble",
                units={"temperature": "°C", "wind_speed": "knots", "rain_probability": "%", "visibility": "NM"}
            )

        # 2. Fallback to Demo Mode if configured
        if self.demo_mode:
            logger.info(f"[WeatherService] Real provider unavailable, using demo profile for {location_name}")
            return self._get_demo_weather(latitude, longitude, location_name, time_context)

        # 3. Provider failed and demo mode disabled
        logger.warning(f"[WeatherService] Weather data unavailable for {location_name}")
        return NormalizedWeather(
            temperature=None,
            wind_speed=None,
            wind_direction=None,
            weather_condition="Service temporarily unavailable",
            warnings=["Weather provider unreachable"],
            provider="Open-Meteo Weather",
            status="unavailable",
            source_reference=None
        )

    def _get_demo_weather(self, lat: float, lon: float, loc_name: str, time_context: str) -> NormalizedWeather:
        # Realistic simulated values based on coastal region
        loc_lower = loc_name.lower()
        if "mumbai" in loc_lower:
            temp, wind, rain = 30.5, 18.0, 45
            cond = "Moderate chop with southwesterly sea breeze"
        elif "chennai" in loc_lower or "kasimedu" in loc_lower:
            temp, wind, rain = 29.5, 17.5, 30
            cond = "Partly cloudy with gentle to moderate easterly breeze"
        elif "kochi" in loc_lower or "cochin" in loc_lower:
            temp, wind, rain = 28.5, 14.0, 20
            cond = "Fair weather with calm morning sea state"
        else:
            temp, wind, rain = 29.0, 16.0, 25
            cond = "Typical coastal marine weather conditions"

        now_iso = datetime.now(timezone.utc).isoformat()
        valid_until = (datetime.now(timezone.utc) + timedelta(hours=4)).isoformat()

        return NormalizedWeather(
            temperature=temp,
            wind_speed=wind,
            wind_direction="WSW (245°)" if "mumbai" in loc_lower else "ENE (65°)",
            wind_direction_deg=245.0 if "mumbai" in loc_lower else 65.0,
            rain_probability=rain,
            weather_condition=cond,
            visibility=8.0,
            warnings=["Demo Advisory: Simulated IMD coastal weather data"],
            timestamp=now_iso,
            valid_from=now_iso,
            valid_until=valid_until,
            provider="Demo Weather Service (Simulated IMD/GFS)",
            status="demo",
            source_reference="Simulated IMD Regional Meteorological Bulletin",
            units={"temperature": "°C", "wind_speed": "knots", "rain_probability": "%", "visibility": "NM"}
        )

weather_service = WeatherService()
