import time
import logging
from typing import Dict, Any, List, Optional
from app.marine_gateway.cache import marine_cache
from app.marine_gateway.models import (
    NormalizedWeather,
    NormalizedOcean,
    NormalizedPFZ,
    NormalizedGeospatial,
    MarineEvidence,
)
from app.data_sources.weather.service import weather_service
from app.data_sources.ocean.service import ocean_service
from app.data_sources.pfz.service import pfz_service
from app.data_sources.satellite.service import satellite_service
from app.data_sources.geospatial.service import geospatial_service
from app.services.mock_marine_service import mock_marine_service

logger = logging.getLogger("marinex.gateway")

class MarineDataGateway:
    """
    Marine Data Gateway: Central interface between LangGraph agents/tools
    and external marine data providers. Manages caching, normalization,
    provenance, and resilient demo fallback.
    """
    def __init__(self):
        self.cache = marine_cache

    def get_weather(
        self,
        latitude: float,
        longitude: float,
        location_name: str = "Coastal Sector",
        time_context: str = "current"
    ) -> NormalizedWeather:
        cache_key = f"weather:{latitude:.2f}:{longitude:.2f}:{time_context}"
        cached = self.cache.get(cache_key, category="weather")
        if cached:
            return cached

        t0 = time.time()
        logger.info(f"[Gateway] [Weather] Request started for {location_name} ({latitude}, {longitude})")
        res = weather_service.get_weather(latitude, longitude, location_name, time_context)
        duration = time.time() - t0
        logger.info(f"[Gateway] [Weather] Finished in {duration:.2f}s (Status: {res.status})")

        self.cache.set(cache_key, res, category="weather")
        return res

    def get_ocean_conditions(
        self,
        latitude: float,
        longitude: float,
        location_name: str = "Coastal Sector",
        time_context: str = "current"
    ) -> NormalizedOcean:
        cache_key = f"ocean:{latitude:.2f}:{longitude:.2f}:{time_context}"
        cached = self.cache.get(cache_key, category="ocean")
        if cached:
            return cached

        t0 = time.time()
        logger.info(f"[Gateway] [Ocean] Request started for {location_name} ({latitude}, {longitude})")
        res = ocean_service.get_ocean_conditions(latitude, longitude, location_name, time_context)
        duration = time.time() - t0
        logger.info(f"[Gateway] [Ocean] Finished in {duration:.2f}s (Status: {res.status})")

        self.cache.set(cache_key, res, category="ocean")
        return res

    def get_pfz(
        self,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        location_name: Optional[str] = None
    ) -> List[NormalizedPFZ]:
        cache_key = f"pfz:{latitude}:{longitude}:{location_name}"
        cached = self.cache.get(cache_key, category="pfz")
        if cached:
            return cached

        t0 = time.time()
        logger.info(f"[Gateway] [PFZ] Request started for {location_name or 'All Sectors'}")
        if latitude is not None and longitude is not None:
            nearest = pfz_service.get_nearest_pfz(latitude, longitude)
            res = [nearest] if nearest else []
        elif location_name:
            res = pfz_service.get_pfz_by_location(location_name)
        else:
            res = pfz_service.get_pfz_zones()
        duration = time.time() - t0
        logger.info(f"[Gateway] [PFZ] Finished in {duration:.2f}s (Found {len(res)} zones)")

        self.cache.set(cache_key, res, category="pfz")
        return res

    def get_satellite_data(self, product_name: str = "sst") -> Dict[str, Any]:
        logger.info(f"[Gateway] [Satellite] Request started for product '{product_name}'")
        res = satellite_service.get_satellite_product(product_name)
        return res.model_dump()

    def get_marine_alerts(self, location_name: Optional[str] = None) -> List[Dict[str, Any]]:
        logger.info(f"[Gateway] [Alerts] Fetching marine advisories for {location_name or 'All'}")
        alerts = mock_marine_service.get_alerts()
        return [
            {
                "id": a.id,
                "type": a.type,
                "severity": a.severity.value,
                "location": a.location,
                "time": a.time,
                "short_description": a.short_description,
                "advisory": a.advisory,
                "provider": "IMD / Coast Guard Marine Safety Alert",
                "data_status": "demo"
            }
            for a in alerts
        ]

    def get_geospatial_information(
        self,
        location_name: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None
    ) -> NormalizedGeospatial:
        cache_key = f"geospatial:{location_name}:{latitude}:{longitude}"
        cached = self.cache.get(cache_key, category="geospatial")
        if cached:
            return cached

        t0 = time.time()
        logger.info(f"[Gateway] [Geospatial] Request started for {location_name}")
        res = geospatial_service.get_geospatial_summary(location_name, latitude, longitude)
        duration = time.time() - t0
        logger.info(f"[Gateway] [Geospatial] Finished in {duration:.2f}s (Port: {res.nearest_port.get('name')})")

        self.cache.set(cache_key, res, category="geospatial")
        return res

marine_gateway = MarineDataGateway()
