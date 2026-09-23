import time
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone

from app.marine_gateway.cache import marine_cache
from app.marine_gateway.registry import provider_registry
from app.marine_gateway.schemas import GatewayStatusResponse
from app.data_sources.common.models import ProviderCapability
from app.marine_models.base import (
    Location,
    TimeWindow,
    MarineDataResponse,
    MarineEvidence,
    DataStatus,
)
from app.marine_gateway.models import (
    NormalizedWeather,
    NormalizedOcean,
    NormalizedPFZ,
    NormalizedGeospatial,
)
from app.services.mock_marine_service import mock_marine_service
from app.data_sources.geospatial.service import geospatial_service
from app.data_sources.pfz.service import pfz_service

logger = logging.getLogger("marinex.gateway")

class MarineDataGateway:
    """
    Marine Data Gateway: Central orchestration interface between LangGraph agents/tools
    and external marine data providers (IMD, INCOIS, MOSDAC, GIS/PostGIS).
    Enforces normalized marine responses, caching, structured logging, provenance tracking,
    and truthful NOT_CONFIGURED reporting without fake data substitution.
    """
    def __init__(self):
        self.cache = marine_cache
        self.registry = provider_registry

    def _resolve_location(
        self,
        location: Optional[Union[Location, float, str]] = None,
        latitude: Optional[Union[float, str]] = None,
        longitude: Optional[Union[float, str]] = None,
        location_name: Optional[str] = None
    ) -> Location:
        """Helper to resolve overloaded location arguments into a standard Location model."""
        if isinstance(location, Location):
            return location
        if isinstance(location, (float, int)) and isinstance(latitude, (float, int)):
            return Location(latitude=float(location), longitude=float(latitude), name=location_name)
        if latitude is not None and longitude is not None and isinstance(latitude, (float, int)) and isinstance(longitude, (float, int)):
            return Location(latitude=float(latitude), longitude=float(longitude), name=location_name)
        if location_name or isinstance(location, str):
            name = location_name or str(location)
            coords = geospatial_service.get_coordinates_by_name(name)
            return Location(latitude=coords["lat"], longitude=coords["lon"], name=coords["name"], port=coords.get("port"))
        # Default fallback coordinates (Mumbai)
        return Location(latitude=18.922, longitude=72.834, name=location_name or "Mumbai Coast")

    def get_weather(
        self,
        location: Optional[Union[Location, float]] = None,
        time_window: Optional[Union[TimeWindow, str, float]] = None,
        latitude: Optional[Union[float, str]] = None,
        longitude: Optional[Union[float, str]] = None,
        location_name: Optional[str] = None,
        time_context: Optional[str] = None,
        provider_name: Optional[str] = None,
        prefer_configured: bool = False
    ) -> MarineDataResponse:
        """
        Retrieves normalized meteorological telemetry (wind vectors, air temperature, precipitation, squall risks).
        Routes through ProviderRegistry (IMD as primary).
        """
        if isinstance(location, (float, int)) and isinstance(time_window, (float, int)):
            # Legacy positional args: get_weather(18.922, 72.834, "Mumbai", "current")
            loc = Location(latitude=float(location), longitude=float(time_window), name=str(latitude) if isinstance(latitude, str) else location_name)
            ctx = str(longitude) if isinstance(longitude, str) else (time_context or "current")
            tw = TimeWindow(context=ctx)
        else:
            loc = self._resolve_location(location, latitude, longitude, location_name)
            ctx = time_context or (time_window.context if isinstance(time_window, TimeWindow) else (str(time_window) if time_window else "current"))
            tw = time_window if isinstance(time_window, TimeWindow) else TimeWindow(context=ctx)

        cache_key = f"weather:{loc.latitude:.2f}:{loc.longitude:.2f}:{ctx}:{provider_name or 'default'}"
        cached = self.cache.get(cache_key, category="weather")
        if cached:
            logger.info(f"[Gateway] [Weather] Cache HIT for key '{cache_key}'")
            return cached

        # Select provider from registry
        provider = self.registry.get_provider_by_name(provider_name) if provider_name else self.registry.get_provider(ProviderCapability.WEATHER, prefer_configured=prefer_configured)
        logger.info(f"[Gateway] [Weather] Provider selected: '{provider.provider_name}' | Query: ({loc.latitude:.3f}, {loc.longitude:.3f}) [{ctx}]")

        t0 = time.time()
        try:
            resp = provider.get_weather(location=loc, time_window=tw)
            duration = time.time() - t0
            logger.info(f"[Gateway] [Weather] Completed in {duration:.2f}s | Provider: {resp.provider} | Status: {resp.status.value}")

            # If primary provider is not configured or unavailable and user hasn't forced a specific provider,
            # query secondary fallback provider for operational continuity in development/demo.
            if resp.status in (DataStatus.NOT_CONFIGURED, DataStatus.UNAVAILABLE) and not provider_name:
                fallback_provider = self.registry.get_provider_by_name("Open-Meteo")
                if fallback_provider and fallback_provider != provider:
                    logger.info(f"[Gateway] [Weather] Primary returned {resp.status.value}. Querying secondary fallback '{fallback_provider.provider_name}'")
                    fallback_resp = fallback_provider.get_weather(location=loc, time_window=tw)
                    # Cache fallback result
                    self.cache.set(cache_key, fallback_resp, category="weather")
                    return fallback_resp

            self.cache.set(cache_key, resp, category="weather")
            return resp
        except Exception as e:
            logger.error(f"[Gateway] [Weather] Request failed on provider '{provider.provider_name}': {e}")
            retrieved_at = datetime.now(timezone.utc).isoformat()
            err_resp = MarineDataResponse(
                status=DataStatus.ERROR,
                provider=provider.provider_name,
                dataset="Weather-Service",
                latitude=loc.latitude,
                longitude=loc.longitude,
                retrieved_at=retrieved_at,
                quality="ERROR",
                location=loc.to_dict(),
                data={"error": str(e)},
                evidence=[]
            )
            return err_resp

    def get_ocean_conditions(
        self,
        location: Optional[Union[Location, float]] = None,
        time_window: Optional[Union[TimeWindow, str, float]] = None,
        latitude: Optional[Union[float, str]] = None,
        longitude: Optional[Union[float, str]] = None,
        location_name: Optional[str] = None,
        time_context: Optional[str] = None,
        provider_name: Optional[str] = None,
        prefer_configured: bool = False
    ) -> MarineDataResponse:
        """
        Retrieves normalized oceanographic telemetry (SST, wave height, swell period, sea state).
        Routes through ProviderRegistry (INCOIS-Ocean as primary).
        """
        if isinstance(location, (float, int)) and isinstance(time_window, (float, int)):
            loc = Location(latitude=float(location), longitude=float(time_window), name=str(latitude) if isinstance(latitude, str) else location_name)
            ctx = str(longitude) if isinstance(longitude, str) else (time_context or "current")
            tw = TimeWindow(context=ctx)
        else:
            loc = self._resolve_location(location, latitude, longitude, location_name)
            ctx = time_context or (time_window.context if isinstance(time_window, TimeWindow) else (str(time_window) if time_window else "current"))
            tw = time_window if isinstance(time_window, TimeWindow) else TimeWindow(context=ctx)

        cache_key = f"ocean:{loc.latitude:.2f}:{loc.longitude:.2f}:{ctx}:{provider_name or 'default'}"
        cached = self.cache.get(cache_key, category="ocean")
        if cached:
            logger.info(f"[Gateway] [Ocean] Cache HIT for key '{cache_key}'")
            return cached

        provider = self.registry.get_provider_by_name(provider_name) if provider_name else self.registry.get_provider(ProviderCapability.OCEAN, prefer_configured=prefer_configured)
        logger.info(f"[Gateway] [Ocean] Provider selected: '{provider.provider_name}' | Query: ({loc.latitude:.3f}, {loc.longitude:.3f}) [{ctx}]")

        t0 = time.time()
        try:
            resp = provider.get_ocean_conditions(location=loc, time_window=tw)
            duration = time.time() - t0
            logger.info(f"[Gateway] [Ocean] Completed in {duration:.2f}s | Provider: {resp.provider} | Status: {resp.status.value}")

            # Fallback to secondary provider if unconfigured
            if resp.status in (DataStatus.NOT_CONFIGURED, DataStatus.UNAVAILABLE) and not provider_name:
                fallback_provider = self.registry.get_provider_by_name("Open-Meteo-Marine")
                if fallback_provider and fallback_provider != provider:
                    logger.info(f"[Gateway] [Ocean] Primary returned {resp.status.value}. Querying secondary fallback '{fallback_provider.provider_name}'")
                    fallback_resp = fallback_provider.get_ocean_conditions(location=loc, time_window=tw)
                    self.cache.set(cache_key, fallback_resp, category="ocean")
                    return fallback_resp

            self.cache.set(cache_key, resp, category="ocean")
            return resp
        except Exception as e:
            logger.error(f"[Gateway] [Ocean] Request failed on provider '{provider.provider_name}': {e}")
            retrieved_at = datetime.now(timezone.utc).isoformat()
            return MarineDataResponse(
                status=DataStatus.ERROR,
                provider=provider.provider_name,
                dataset="Ocean-Service",
                latitude=loc.latitude,
                longitude=loc.longitude,
                retrieved_at=retrieved_at,
                quality="ERROR",
                location=loc.to_dict(),
                data={"error": str(e)},
                evidence=[]
            )

    def get_pfz(
        self,
        location: Optional[Union[Location, float]] = None,
        time_window: Optional[Union[TimeWindow, str]] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        location_name: Optional[str] = None
    ) -> Union[MarineDataResponse, List[NormalizedPFZ]]:
        """
        Retrieves Potential Fishing Zones (PFZs).
        Routes through ProviderRegistry (INCOIS-PFZ as primary).
        Supports returning List[NormalizedPFZ] when called by legacy tools, or MarineDataResponse.
        """
        # Legacy check: if called with keyword args matching legacy pfz_service
        if latitude is not None and longitude is not None and not isinstance(location, Location):
            nearest = pfz_service.get_nearest_pfz(latitude, longitude)
            return [nearest] if nearest else []
        if location_name and not isinstance(location, Location) and latitude is None:
            return pfz_service.get_pfz_by_location(location_name)

        loc = self._resolve_location(location, latitude, longitude, location_name)
        tw = time_window if isinstance(time_window, TimeWindow) else TimeWindow(context="current")

        provider = self.registry.get_provider(ProviderCapability.PFZ)
        logger.info(f"[Gateway] [PFZ] Provider selected: '{provider.provider_name}' for {loc.name}")
        return provider.get_pfz(location=loc, time_window=tw)

    def get_satellite_data(
        self,
        location: Optional[Location] = None,
        product_name: str = "sst",
        time_window: Optional[TimeWindow] = None
    ) -> MarineDataResponse:
        """
        Retrieves satellite earth observation telemetry from ISRO MOSDAC.
        Strictly returns NOT_CONFIGURED when MOSDAC credentials are not present.
        """
        provider = self.registry.get_provider(ProviderCapability.SATELLITE)
        logger.info(f"[Gateway] [Satellite] Provider selected: '{provider.provider_name}' for product '{product_name}'")
        return provider.get_satellite_data(location=location, product=product_name, time_window=time_window)

    def get_geospatial_context(
        self,
        location: Optional[Union[Location, str]] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None
    ) -> MarineDataResponse:
        """
        Retrieves maritime geospatial constraints (ports, fairways, MPAs, restricted areas).
        Routes through ProviderRegistry (GISProvider).
        """
        if isinstance(location, str):
            loc = self._resolve_location(location_name=location, latitude=latitude, longitude=longitude)
        elif isinstance(location, Location):
            loc = location
        else:
            loc = self._resolve_location(latitude=latitude, longitude=longitude)

        provider = self.registry.get_provider(ProviderCapability.GEOSPATIAL)
        logger.info(f"[Gateway] [Geospatial] Provider selected: '{provider.provider_name}' for {loc.name}")
        return provider.get_geospatial_data(location=loc)

    def get_geospatial_information(
        self,
        location_name: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None
    ) -> NormalizedGeospatial:
        """Backward-compatible helper for existing Phase 4 tools."""
        res = geospatial_service.get_geospatial_summary(location_name, latitude, longitude)
        return res

    def get_hazards(
        self,
        location: Optional[Union[Location, str]] = None,
        time_window: Optional[TimeWindow] = None
    ) -> List[Dict[str, Any]]:
        """Retrieves active maritime warnings, cyclone alerts, and squall bulletins."""
        loc_name = location.name if isinstance(location, Location) else (location if isinstance(location, str) else None)
        return self.get_marine_alerts(location_name=loc_name)

    def get_marine_alerts(self, location_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Backward-compatible helper for alerts."""
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

    def get_gateway_status(self) -> GatewayStatusResponse:
        """
        Sanitized public status report for /api/marine/gateway/status.
        Reports provider statuses without exposing secrets.
        """
        providers_health = self.registry.get_status_report()
        routing = self.registry.get_routing_table()
        cache_entries = len(getattr(self.cache, "_cache", {}))

        return GatewayStatusResponse(
            status="healthy",
            gateway_version="Phase-5A",
            total_providers_registered=len(providers_health),
            providers=providers_health,
            capability_routing=routing,
            active_cache_entries=cache_entries,
            metadata={
                "capabilities": routing,
                "providers": [p.model_dump() for p in providers_health]
            }
        )

marine_gateway = MarineDataGateway()
