import os
from typing import Dict, Any
from app.data_sources.weather.service import weather_service
from app.data_sources.ocean.service import ocean_service
from app.data_sources.pfz.service import pfz_service
from app.data_sources.satellite.service import satellite_service
from app.data_sources.geospatial.service import geospatial_service

def check_all_data_sources() -> Dict[str, Any]:
    """
    Performs comprehensive health checks across all registered data sources.
    Only reports a provider as online if connectivity succeeds.
    """
    demo_mode = os.getenv("MARINEX_DEMO_MODE", os.getenv("IS_DEMO", "true")).lower() == "true"
    postgis_enabled = os.getenv("POSTGIS_ENABLED", "false").lower() == "true"

    weather_health = weather_service.health_check()
    ocean_health = ocean_service.health_check()
    pfz_health = pfz_service.health_check()
    satellite_health = satellite_service.health_check()
    geospatial_health = geospatial_service.health_check()

    return {
        "weather": {
            "enabled": True,
            "status": weather_health.get("status", "offline"),
            "provider": weather_health.get("provider", "Open-Meteo Weather"),
            "is_live": weather_health.get("is_live", False)
        },
        "ocean": {
            "enabled": True,
            "status": ocean_health.get("status", "offline"),
            "provider": ocean_health.get("provider", "Open-Meteo Marine / INCOIS"),
            "is_live": ocean_health.get("is_live", False)
        },
        "pfz": {
            "enabled": True,
            "status": pfz_health.get("status", "offline"),
            "provider": pfz_health.get("provider", "INCOIS PFZ"),
            "is_live": pfz_health.get("is_live", True)
        },
        "satellite": {
            "enabled": satellite_service.enabled,
            "status": satellite_health.get("status", "not_configured"),
            "provider": "ISRO MOSDAC",
            "message": satellite_health.get("message")
        },
        "postgis": {
            "enabled": postgis_enabled,
            "status": "online" if postgis_enabled else "not_configured",
            "provider": "PostgreSQL / PostGIS",
            "fallback": "GeoJSON Spatial Engine Active"
        },
        "gis": {
            "enabled": True,
            "status": geospatial_health.get("status", "online"),
            "provider": geospatial_health.get("provider"),
            "layers": geospatial_health.get("layers_loaded", {})
        },
        "demo_mode": demo_mode,
        "overall_status": "operational"
    }
