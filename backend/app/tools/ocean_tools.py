import logging
from typing import Dict, Any
from langchain_core.tools import tool
from app.marine_gateway.gateway import marine_gateway
from app.data_sources.geospatial.service import geospatial_service

logger = logging.getLogger("marinex.tools.ocean")

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

    logger.info(f"[GATEWAY] Invoking marine_gateway.get_ocean_conditions for location='{location}' ({lat}, {lon}) [{time_context}]")

    normalized = marine_gateway.get_ocean_conditions(
        latitude=lat,
        longitude=lon,
        location_name=location,
        time_context=time_context
    )

    status_str = normalized.status.value if hasattr(normalized.status, "value") else str(normalized.status)
    logger.info(f"[MARINE_DATA] Gateway get_ocean_conditions returned provider='{normalized.provider}', status='{status_str}'")

    suitability = "Favorable"
    if normalized.wave_height is not None:
        if normalized.wave_height >= 2.5:
            suitability = "Unfavorable"
        elif normalized.wave_height >= 1.8:
            suitability = "Caution"
    else:
        suitability = "Unknown" if status_str in ("not_configured", "unavailable") else "Favorable"

    return {
        "location": location,
        "time_context": time_context,
        "sst": normalized.sea_surface_temperature,
        "chlorophyll": normalized.chlorophyll,
        "wave_height": normalized.wave_height,
        "ocean_condition": normalized.ocean_condition,
        "swell_period": normalized.swell_period,
        "tide_status": normalized.tide_status,
        "suitability": suitability,
        "source": f"{normalized.provider} ({normalized.source_reference or 'Hydrodynamic Model'})",
        "data_status": status_str,
        "timestamp": normalized.timestamp,
        "valid_until": normalized.valid_until,
        "units": normalized.units
    }

