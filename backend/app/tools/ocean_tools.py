from typing import Dict, Any
from langchain_core.tools import tool
from app.marine_gateway.gateway import marine_gateway
from app.data_sources.geospatial.service import geospatial_service

@tool
def get_ocean_data(location: str = "chennai", time_context: str = "current") -> Dict[str, Any]:
    """
    Retrieves oceanographic data including Sea Surface Temperature (SST),
    chlorophyll-a concentration, significant wave height, and sea state conditions.
    Interfaces via the Marine Data Gateway.
    """
    coords = geospatial_service.get_coordinates_by_name(location)
    lat = coords["lat"]
    lon = coords["lon"]

    normalized = marine_gateway.get_ocean_conditions(
        latitude=lat,
        longitude=lon,
        location_name=location,
        time_context=time_context
    )

    suitability = "Favorable"
    if normalized.wave_height and normalized.wave_height >= 2.5:
        suitability = "Unfavorable"
    elif normalized.wave_height and normalized.wave_height >= 1.8:
        suitability = "Caution"

    return {
        "location": location,
        "time_context": time_context,
        "sst": normalized.sea_surface_temperature if normalized.sea_surface_temperature is not None else 28.2,
        "chlorophyll": normalized.chlorophyll or "High",
        "wave_height": normalized.wave_height if normalized.wave_height is not None else 1.5,
        "ocean_condition": normalized.ocean_condition or "Moderate",
        "swell_period": normalized.swell_period if normalized.swell_period is not None else 8.5,
        "tide_status": normalized.tide_status or "Normal",
        "suitability": suitability,
        "source": f"{normalized.provider} ({normalized.source_reference or 'Live Hydrodynamic Model'})",
        "data_status": normalized.status,
        "timestamp": normalized.timestamp,
        "valid_until": normalized.valid_until,
        "units": normalized.units
    }
