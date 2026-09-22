import json
import logging
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

logger = logging.getLogger("marinex.datasources.weather.client")

WMO_WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail"
}

def degrees_to_cardinal(d: Optional[float]) -> str:
    if d is None:
        return "Variable"
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    ix = round(d / (360.0 / len(dirs))) % len(dirs)
    return f"{dirs[ix]} ({int(d)}°)"

class WeatherClient:
    """
    Client for Open-Meteo Meteorological Forecast API.
    Provides open access marine weather and wind vectors without requiring API keys.
    """
    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    def __init__(self, timeout_seconds: int = 5):
        self.timeout = timeout_seconds

    def fetch_weather(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        params = (
            f"latitude={lat:.4f}&longitude={lon:.4f}"
            f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,weather_code"
            f"&hourly=precipitation_probability,wind_gusts_10m"
            f"&forecast_days=2&wind_speed_unit=kn"
        )
        url = f"{self.BASE_URL}?{params}"
        logger.info(f"[WeatherClient] Requesting meteorological data for Lat: {lat:.3f}, Lon: {lon:.3f}")

        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "MarineX-AI/1.4.0 (ORCA Marine Decision Platform)"}
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    return data
                else:
                    logger.warning(f"[WeatherClient] Open-Meteo returned status {resp.status}")
                    return None
        except urllib.error.URLError as e:
            logger.warning(f"[WeatherClient] Network error connecting to Open-Meteo: {e.reason}")
            return None
        except Exception as e:
            logger.error(f"[WeatherClient] Unexpected error: {e}")
            return None

weather_client = WeatherClient()
