import logging
from typing import Dict, Any
from langchain_core.tools import tool
from app.marine_gateway.gateway import marine_gateway
from app.data_sources.geospatial.service import geospatial_service

logger = logging.getLogger("marinex.tools.weather")

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

    logger.info(f"[GATEWAY] Invoking marine_gateway.get_weather for location='{location}' ({lat}, {lon}) [{time_context}]")

    normalized = marine_gateway.get_weather(
        latitude=lat,
        longitude=lon,
        location_name=location,
        time_context=time_context
    )

    status_str = normalized.status.value if hasattr(normalized.status, "value") else str(normalized.status)
    logger.info(f"[MARINE_DATA] Gateway get_weather returned provider='{normalized.provider}', status='{status_str}'")

    storm_risk = "low"
    if normalized.wind_speed is not None and normalized.wind_speed >= 22.0:
        storm_risk = "high"
    elif (normalized.wind_speed is not None and normalized.wind_speed >= 16.0) or (normalized.rain_probability is not None and normalized.rain_probability >= 40):
        storm_risk = "moderate"
    elif normalized.wind_speed is None:
        storm_risk = "unknown"

    desc = normalized.weather_condition
    if not desc:
        if status_str in ("not_configured", "unavailable"):
            desc = normalized.data.get("message") if isinstance(normalized.data, dict) else f"Weather provider is {status_str}"
        else:
            desc = "Marine weather conditions"

    return {
        "location": location,
        "time_context": time_context,
        "temperature": normalized.temperature,
        "wind_speed": normalized.wind_speed,
        "wind_direction": normalized.wind_direction,
        "rain_probability": normalized.rain_probability,
        "storm_risk": storm_risk,
        "description": desc,
        "warnings": normalized.warnings,
        "source": f"{normalized.provider} ({normalized.source_reference or 'Live Model'})",
        "data_status": status_str,
        "timestamp": normalized.timestamp,
        "valid_until": normalized.valid_until,
        "units": normalized.units
    }

