import logging
from typing import Dict, List, Optional, Any
from app.data_sources.common.base_provider import BaseMarineProvider
from app.data_sources.common.models import ProviderCapability, ProviderHealth
from app.data_sources.common.exceptions import ProviderNotConfiguredError
from app.marine_gateway.exceptions import NoProviderAvailableError
from app.data_sources.imd.provider import IMDWeatherProvider
from app.data_sources.incois.ocean_provider import INCOISOceanProvider
from app.data_sources.incois.pfz_provider import INCOISPFZProvider
from app.data_sources.mosdac.satellite_provider import MOSDACSatelliteProvider
from app.data_sources.gis.provider import GISProvider
from app.data_sources.common.fallback_providers import OpenMeteoWeatherProvider, OpenMeteoOceanProvider

logger = logging.getLogger("marinex.gateway.registry")

class ProviderRegistry:
    """
    Central Registry for Marine Data Providers.
    Maps capabilities to primary and secondary providers:
      WEATHER    -> IMD (Primary) / Open-Meteo (Secondary/Fallback)
      OCEAN      -> INCOIS (Primary) / Open-Meteo Marine (Secondary/Fallback)
      PFZ        -> INCOIS (Primary)
      SATELLITE  -> MOSDAC (Primary)
      GEOSPATIAL -> GIS / PostGIS (Primary)
    Allows adding or replacing providers at runtime without altering LangGraph agent code.
    """
    def __init__(self):
        self._providers: Dict[str, BaseMarineProvider] = {}
        self._capability_map: Dict[ProviderCapability, List[str]] = {
            cap: [] for cap in ProviderCapability
        }
        self._bootstrap_default_providers()

    def _bootstrap_default_providers(self):
        """Initializes standard National and Global Marine data providers."""
        # 1. IMD (Weather)
        imd = IMDWeatherProvider()
        self.register_provider(imd, capabilities=[ProviderCapability.WEATHER, ProviderCapability.HAZARDS], is_primary=True)

        # 2. INCOIS Ocean (Wave, Sea State, SST)
        incois_ocean = INCOISOceanProvider()
        self.register_provider(incois_ocean, capabilities=[ProviderCapability.OCEAN], is_primary=True)

        # 3. INCOIS PFZ (Fishing Zones)
        incois_pfz = INCOISPFZProvider()
        self.register_provider(incois_pfz, capabilities=[ProviderCapability.PFZ], is_primary=True)

        # 4. MOSDAC (Satellite earth observation)
        mosdac = MOSDACSatelliteProvider()
        self.register_provider(mosdac, capabilities=[ProviderCapability.SATELLITE], is_primary=True)

        # 5. GIS (Navigational constraints, ports, geofencing)
        gis = GISProvider()
        self.register_provider(gis, capabilities=[ProviderCapability.GEOSPATIAL, ProviderCapability.HAZARDS], is_primary=True)

        # 6. Secondary / Open Fallback Providers (for resilient demo and development mode)
        om_weather = OpenMeteoWeatherProvider()
        self.register_provider(om_weather, capabilities=[ProviderCapability.WEATHER], is_primary=False)

        om_ocean = OpenMeteoOceanProvider()
        self.register_provider(om_ocean, capabilities=[ProviderCapability.OCEAN], is_primary=False)

    def register_provider(
        self,
        provider: BaseMarineProvider,
        capabilities: Optional[List[ProviderCapability]] = None,
        is_primary: bool = False
    ):
        """Registers a provider adapter and binds it to specified capabilities."""
        name = provider.provider_name
        self._providers[name] = provider
        caps = capabilities or provider.capabilities

        for cap in caps:
            if cap not in self._capability_map:
                self._capability_map[cap] = []
            if name in self._capability_map[cap]:
                self._capability_map[cap].remove(name)

            if is_primary:
                self._capability_map[cap].insert(0, name)
            else:
                self._capability_map[cap].append(name)

        logger.info(f"[Registry] Registered provider '{name}' for capabilities: {[c.value for c in caps]} (Primary={is_primary})")

    def get_provider(
        self,
        capability: ProviderCapability,
        prefer_configured: bool = False
    ) -> BaseMarineProvider:
        """
        Retrieves the appropriate provider for a requested capability.
        If prefer_configured is True, scans for the first configured provider before falling back.
        """
        names = self._capability_map.get(capability, [])
        if not names:
            raise NoProviderAvailableError(capability.value)

        if prefer_configured:
            for name in names:
                p = self._providers[name]
                if p.is_configured and p.is_enabled:
                    return p

        # Default to primary registered provider
        return self._providers[names[0]]

    def get_provider_by_name(self, name: str) -> Optional[BaseMarineProvider]:
        return self._providers.get(name)

    def get_all_providers(self) -> List[BaseMarineProvider]:
        return list(self._providers.values())

    def initialize_default_providers(self):
        """Re-initializes default providers."""
        self._bootstrap_default_providers()

    def get_primary_provider(self, capability: ProviderCapability) -> Optional[BaseMarineProvider]:
        """Returns the primary configured provider for a given capability."""
        return self.get_provider(capability, prefer_configured=False)

    def get_status_report(self) -> List[ProviderHealth]:
        """Returns health and configuration report without sensitive credentials."""
        return [p.get_health() for p in self._providers.values()]

    def get_routing_table(self) -> Dict[str, str]:
        """Returns mapping of capabilities to current primary provider."""
        return {
            cap.value: self._capability_map[cap][0] if self._capability_map.get(cap) else "None"
            for cap in ProviderCapability
        }

    def get_all_provider_statuses(self) -> Dict[str, Any]:
        """Returns capabilities routing map and sanitized provider health reports."""
        return {
            "capabilities": self.get_routing_table(),
            "providers": [p.get_health().model_dump() for p in self._providers.values()]
        }

provider_registry = ProviderRegistry()
