import abc
import logging
from typing import List, Optional, Dict, Any
from app.marine_models.base import Location, TimeWindow, MarineDataResponse, DataStatus
from app.data_sources.common.models import ProviderCapability, ProviderHealth
from app.data_sources.common.exceptions import ProviderNotConfiguredError, MarineProviderError

logger = logging.getLogger("marinex.datasources.base")

class BaseMarineProvider(abc.ABC):
    """
    Abstract Base Class for all external and simulated marine data provider adapters.
    Ensures uniform interfaces, error handling, health reporting, and normalization.
    """
    def __init__(self, provider_name: str, capabilities: List[ProviderCapability]):
        self.provider_name = provider_name
        self.capabilities = capabilities
        self.last_retrieved_at: Optional[str] = None
        self.last_error: Optional[str] = None

    @property
    def provider_id(self) -> str:
        return self.provider_name.lower().replace("-", "_").replace(" ", "_")

    def fetch(self, *args, **kwargs) -> MarineDataResponse:
        """Generic dispatch helper."""
        if ProviderCapability.WEATHER in self.capabilities:
            return self.get_weather(*args, **kwargs)
        elif ProviderCapability.OCEAN in self.capabilities:
            return self.get_ocean_conditions(*args, **kwargs)
        elif ProviderCapability.PFZ in self.capabilities:
            return self.get_pfz(*args, **kwargs)
        elif ProviderCapability.SATELLITE in self.capabilities:
            return self.get_satellite_data(*args, **kwargs)
        elif ProviderCapability.GEOSPATIAL in self.capabilities:
            return self.get_geospatial_data(*args, **kwargs)
        raise NotImplementedError(f"Provider '{self.provider_name}' does not implement fetch()")

    @property
    @abc.abstractmethod
    def is_enabled(self) -> bool:
        """Indicates whether this provider has been toggled active in configuration."""
        pass

    @property
    @abc.abstractmethod
    def is_configured(self) -> bool:
        """Indicates whether all necessary credentials and endpoints are present."""
        pass

    def get_weather(self, location: Location, time_window: Optional[TimeWindow] = None) -> MarineDataResponse:
        raise NotImplementedError(f"Provider '{self.provider_name}' does not implement get_weather()")

    def get_ocean_conditions(self, location: Location, time_window: Optional[TimeWindow] = None) -> MarineDataResponse:
        raise NotImplementedError(f"Provider '{self.provider_name}' does not implement get_ocean_conditions()")

    def get_pfz(self, location: Optional[Location] = None, time_window: Optional[TimeWindow] = None) -> MarineDataResponse:
        raise NotImplementedError(f"Provider '{self.provider_name}' does not implement get_pfz()")

    def get_satellite_data(self, location: Optional[Location] = None, product: str = "sst", time_window: Optional[TimeWindow] = None) -> MarineDataResponse:
        raise NotImplementedError(f"Provider '{self.provider_name}' does not implement get_satellite_data()")

    def get_geospatial_data(self, location: Location) -> MarineDataResponse:
        raise NotImplementedError(f"Provider '{self.provider_name}' does not implement get_geospatial_data()")

    def get_health(self) -> ProviderHealth:
        """Returns sanitized public connectivity and health status."""
        connection = "not_configured"
        if not self.is_configured:
            connection = "not_configured"
        elif not self.is_enabled:
            connection = "disabled"
        elif self.last_error:
            connection = "error"
        else:
            connection = "online"

        return ProviderHealth(
            provider_name=self.provider_name,
            capabilities=self.capabilities,
            enabled=self.is_enabled,
            configured=self.is_configured,
            connection_status=connection,
            last_successful_retrieval=self.last_retrieved_at,
            error_message=self.last_error,
            telemetry_type="external" if self.is_configured else "not_configured"
        )
