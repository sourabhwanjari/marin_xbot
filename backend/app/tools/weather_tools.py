from typing import Dict, Any
from langchain_core.tools import tool
from app.marine_gateway.gateway import marine_gateway
from app.data_sources.geospatial.service import geospatial_service

@tool
def get_weather_data(location: str = "chennai", time_context: str = "current") -> Dict[str, Any]:
    """
    Retrieves marine weather data including temperature, wind speed, wind direction,
    rain probability, and storm risk for a given coastal location and time.
    Interfaces via the Marine Data Gateway.
    """
    coords = geospatial_service.get_coordinates_by_name(location)
    lat = coords["lat"]
    lon = coords["lon"]

    normalized = marine_gateway.get_weather(
        latitude=lat,
        longitude=lon,
        location_name=location,
        time_context=time_context
    )

    storm_risk = "low"
    if normalized.wind_speed and normalized.wind_speed >= 22.0:
        storm_risk = "high"
    elif normalized.wind_speed and normalized.wind_speed >= 16.0 or (normalized.rain_probability and normalized.rain_probability >= 40):
        storm_risk = "moderate"

    return {
        "location": location,
        "time_context": time_context,
        "temperature": normalized.temperature if normalized.temperature is not None else 29.5,
        "wind_speed": normalized.wind_speed if normalized.wind_speed is not None else 16.0,
        "wind_direction": normalized.wind_direction or "ENE",
        "rain_probability": normalized.rain_probability if normalized.rain_probability is not None else 25,
        "storm_risk": storm_risk,
        "description": normalized.weather_condition or "Marine weather conditions",
        "warnings": normalized.warnings,
        "source": f"{normalized.provider} ({normalized.source_reference or 'Live Model'})",
        "data_status": normalized.status,
        "timestamp": normalized.timestamp,
        "valid_until": normalized.valid_until,
        "units": normalized.units
    }
