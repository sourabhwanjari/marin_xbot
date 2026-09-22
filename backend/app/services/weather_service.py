"""
Weather Service Abstraction Layer
Target Phase: Connects to IMD (India Meteorological Department) & ECMWF / GFS APIs.
Phase 1: Provides simulated marine meteorological data.
"""
from typing import Dict, Any

class WeatherService:
    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    async def get_marine_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Future implementation: Fetch numerical weather prediction (NWP) parameters
        including wind vectors, barometric pressure, precipitation, and convective storm indices.
        """
        return {
            "source": "simulated_imd_forecast",
            "lat": lat,
            "lon": lon,
            "air_temp_c": 29.5,
            "wind_speed_knots": 18.0,
            "wind_direction_deg": 65,
            "gusts_knots": 24.0,
            "convective_risk": "Moderate",
            "cloud_cover_percent": 45
        }

weather_service = WeatherService()
