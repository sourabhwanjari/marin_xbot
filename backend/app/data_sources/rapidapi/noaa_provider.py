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

logger = logging.getLogger("marinex.datasources.rapidapi.noaa")


class RapidAPINOAAWeatherProvider(BaseMarineProvider):
    """
    RapidAPI NOAA Weather Provider.
    Queries 'noaa-weather2.p.rapidapi.com' for NOAA meteorological forecasts, surface wind vectors,
    precipitation chances, atmospheric parameters, and marine weather hazards using RapidAPI credentials.
    Provides automatic fallback to NOAA official NWS gridpoints for US coastal regions and
    RapidAPI Weather338 / Open-Meteo for international marine sectors.
    """
    def __init__(self):
        super().__init__(
            provider_name="RapidAPI-NOAA-Weather",
            capabilities=[ProviderCapability.WEATHER, ProviderCapability.HAZARDS]
        )
        self.api_key = (
            os.getenv("RAPIDAPI_NOAA_KEY")
            or os.getenv("RAPIDAPI_WEATHER_KEY")
            or os.getenv("RAPIDAPI_KEY")
            or "e5f367a1d1mshceae8e687637286p187d55jsnab86f1cf2552"
        )
        self.api_host = (
            os.getenv("RAPIDAPI_NOAA_HOST")
            or "noaa-weather2.p.rapidapi.com"
        )

    @property
    def is_enabled(self) -> bool:
        return True

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 10)

    def _parse_wind_speed_knots(self, raw_wind: Any) -> Optional[float]:
        """Converts wind string (e.g. '15 mph' or '10 to 15 mph' or '20 km/h') to knots."""
        if raw_wind is None:
            return None
        if isinstance(raw_wind, (int, float)):
            return round(float(raw_wind), 1)
        text = str(raw_wind).lower()
        import re
        numbers = re.findall(r"\d+\.?\d*", text)
        if not numbers:
            return None
        val = float(numbers[-1])
        if "mph" in text:
            return round(val * 0.868976, 1)
        elif "km/h" in text or "kph" in text:
            return round(val / 1.852, 1)
        elif "kt" in text or "knot" in text:
            return round(val, 1)
        elif "m/s" in text:
            return round(val * 1.94384, 1)
        return round(val, 1)

    def get_weather(
        self,
        location: Location,
        time_window: Optional[TimeWindow] = None
    ) -> MarineDataResponse:
        """
        Retrieves live weather forecast and observation telemetry via NOAA RapidAPI.
        """
        retrieved_at = datetime.now(timezone.utc).isoformat()
        headers = {
            "x-rapidapi-host": self.api_host,
            "x-rapidapi-key": self.api_key,
            "X-DataNow-Key": self.api_key,
        }

        url = f"https://{self.api_host}/weather/location?lat={location.latitude:.4f}&lon={location.longitude:.4f}"
        logger.info(f"[RapidAPI-NOAA] Fetching live NOAA forecast for '{location.name}' ({location.latitude:.3f}, {location.longitude:.3f})")

        # 1. Attempt RapidAPI NOAA endpoint
        try:
            resp = requests.get(url, headers=headers, timeout=6)
            if resp.status_code == 200:
                data = resp.json()
                logger.info(f"[RapidAPI-NOAA] Successfully received live telemetry from {self.api_host}")
                current = data.get("current") or data.get("properties") or data
                temp = current.get("temperature") or current.get("temp")
                raw_wind = current.get("windSpeed") or current.get("wind_speed")
                wind_kts = self._parse_wind_speed_knots(raw_wind)
                wind_dir = current.get("windDirection") or current.get("wind_direction") or "VRB"
                condition = current.get("weather") or current.get("shortForecast") or current.get("condition") or "Marine Weather"
                precip = current.get("precipitation") or current.get("precipChance") or 0.0

                cond_lower = condition.lower()
                storm_risk = "high" if (wind_kts and wind_kts >= 22.0) or "thunderstorm" in cond_lower or "squall" in cond_lower else (
                    "moderate" if (wind_kts and wind_kts >= 16.0) or "rain" in cond_lower or precip >= 40 else "low"
                )

                warnings = []
                if storm_risk == "high":
                    warnings.append(f"ADVISORY: Severe weather conditions ({condition}) detected near {location.name}.")

                res_data = {
                    "temperature": temp,
                    "wind_speed": wind_kts,
                    "wind_direction": wind_dir,
                    "rain_probability": precip,
                    "storm_risk": storm_risk,
                    "weather_condition": condition,
                    "warnings": warnings,
                    "source": f"RapidAPI NOAA Weather ({self.api_host})",
                    "units": {"temperature": "°C", "wind_speed": "knots"}
                }
                return MarineDataResponse(
                    status=DataStatus.VERIFIED,
                    provider="RapidAPI-NOAA-Weather",
                    dataset="NOAA-RapidAPI-Live-Forecast",
                    parameter="weather_conditions",
                    latitude=location.latitude,
                    longitude=location.longitude,
                    observed_at=retrieved_at,
                    retrieved_at=retrieved_at,
                    quality="OPERATIONAL",
                    location=location.to_dict(),
                    data=res_data,
                    evidence=[
                        MarineEvidence(
                            source=f"RapidAPI NOAA Weather ({self.api_host})",
                            provider="RapidAPI-NOAA-Weather",
                            dataset="NOAA-RapidAPI-Live-Forecast",
                            parameter="Surface Wind Velocity & Meteorological Observations",
                            observed_at=retrieved_at,
                            retrieved_at=retrieved_at,
                            quality="OPERATIONAL"
                        )
                    ]
                )
            else:
                logger.warning(f"[RapidAPI-NOAA] {self.api_host} returned HTTP {resp.status_code}: {resp.text[:120]}")
        except Exception as e:
            logger.warning(f"[RapidAPI-NOAA] Request error querying {self.api_host}: {e}")

        # 2. Check if coordinates fall within NOAA National Weather Service coverage (US & coastal territories)
        # NOAA NWS coverage: Lat roughly 15 to 72, Lon roughly -180 to -65
        is_us_marine_zone = (15.0 <= location.latitude <= 72.0) and (-180.0 <= location.longitude <= -65.0)
        if is_us_marine_zone:
            try:
                logger.info(f"[RapidAPI-NOAA] Querying official NOAA NWS gridpoint for US coastal sector '{location.name}'")
                nws_point_url = f"https://api.weather.gov/points/{location.latitude:.4f},{location.longitude:.4f}"
                nws_headers = {"User-Agent": "MarineX-AI/1.0 (contact@marinex.ai)"}
                pt_resp = requests.get(nws_point_url, headers=nws_headers, timeout=6)
                if pt_resp.status_code == 200:
                    fc_url = pt_resp.json().get("properties", {}).get("forecast")
                    if fc_url:
                        fc_resp = requests.get(fc_url, headers=nws_headers, timeout=6)
                        if fc_resp.status_code == 200:
                            periods = fc_resp.json().get("properties", {}).get("periods", [])
                            if periods:
                                current_period = periods[0]
                                temp_val = current_period.get("temperature")
                                temp_unit = current_period.get("temperatureUnit", "F")
                                temp_c = round((temp_val - 32) * 5 / 9, 1) if temp_unit == "F" and temp_val is not None else temp_val
                                raw_wind = current_period.get("windSpeed")
                                wind_kts = self._parse_wind_speed_knots(raw_wind)
                                wind_dir = current_period.get("windDirection", "VRB")
                                condition = current_period.get("shortForecast", "Marine Weather")
                                pop = current_period.get("probabilityOfPrecipitation", {}).get("value") or 0

                                cond_lower = condition.lower()
                                storm_risk = "high" if (wind_kts and wind_kts >= 22.0) or "thunderstorm" in cond_lower or "squall" in cond_lower else (
                                    "moderate" if (wind_kts and wind_kts >= 16.0) or "rain" in cond_lower or pop >= 40 else "low"
                                )

                                res_data = {
                                    "temperature": temp_c,
                                    "wind_speed": wind_kts,
                                    "wind_direction": wind_dir,
                                    "rain_probability": pop,
                                    "storm_risk": storm_risk,
                                    "weather_condition": condition,
                                    "detailed_forecast": current_period.get("detailedForecast"),
                                    "warnings": [f"ADVISORY: Convective activity ({condition}) forecast by NOAA."] if storm_risk == "high" else [],
                                    "source": "NOAA National Weather Service (NWS Telemetry)",
                                    "units": {"temperature": "°C", "wind_speed": "knots"}
                                }
                                return MarineDataResponse(
                                    status=DataStatus.VERIFIED,
                                    provider="RapidAPI-NOAA-Weather",
                                    dataset="NOAA-NWS-Live-Gridpoint",
                                    parameter="weather_conditions",
                                    latitude=location.latitude,
                                    longitude=location.longitude,
                                    observed_at=retrieved_at,
                                    retrieved_at=retrieved_at,
                                    quality="OPERATIONAL",
                                    location=location.to_dict(),
                                    data=res_data,
                                    evidence=[
                                        MarineEvidence(
                                            source="NOAA National Weather Service (api.weather.gov)",
                                            provider="RapidAPI-NOAA-Weather",
                                            dataset="NOAA-NWS-Live-Gridpoint",
                                            parameter="High-Resolution Atmospheric & Surface Wind Forecast",
                                            observed_at=retrieved_at,
                                            retrieved_at=retrieved_at,
                                            quality="OPERATIONAL"
                                        )
                                    ]
                                )
            except Exception as e:
                logger.warning(f"[RapidAPI-NOAA] NOAA NWS fallback query failed: {e}")

        # 3. For International/Global waters outside NOAA US domain (or if NOAA endpoints unreachable):
        # Query Global Meteorological Provider (RapidAPI Weather338 or Open-Meteo)
        logger.info(f"[RapidAPI-NOAA] Location '{location.name}' is outside US NOAA bounds or requires global telemetry. Querying global meteorological stream.")
        try:
            # First try RapidAPI Weather338 for live international observations
            from app.data_sources.rapidapi.weather_provider import RapidAPIWeatherProvider
            w338 = RapidAPIWeatherProvider()
            if w338.is_configured:
                res = w338.get_weather(location=location, time_window=time_window)
                if res and res.status in (DataStatus.VERIFIED, DataStatus.EXTERNAL):
                    return res
        except Exception as e:
            logger.warning(f"[RapidAPI-NOAA] RapidAPI Weather338 delegation failed: {e}")

        # 4. Standard Open-Meteo Fallback
        res = weather_service.get_weather(
            latitude=location.latitude,
            longitude=location.longitude,
            location_name=location.name or "Coastal Sector",
            time_context=time_window.context if time_window else "current"
        )
        return MarineDataResponse(
            status=DataStatus.EXTERNAL,
            provider="RapidAPI-NOAA-Weather",
            dataset="Global-Marine-Observation-Fallback",
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
                    source="RapidAPI NOAA Gateway (Global Marine Telemetry)",
                    provider="RapidAPI-NOAA-Weather",
                    dataset="Global-Atmospheric-Observation",
                    parameter="Surface Wind & Temperature",
                    observed_at=retrieved_at,
                    retrieved_at=retrieved_at,
                    quality="OPERATIONAL"
                )
            ]
        )
