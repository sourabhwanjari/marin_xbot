from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Optional

class DataStatus(str, Enum):
    DEMO = "demo"
    SIMULATED = "simulated"
    EXTERNAL = "external"
    VERIFIED = "verified"
    UNAVAILABLE = "unavailable"
    NOT_CONFIGURED = "not_configured"
    ERROR = "error"

class DataSource(ABC):
    """
    Common abstraction for all external marine and geospatial data sources.
    Isolates provider-specific protocols, network calls, and credentials.
    """
    name: str = "base_source"
    enabled: bool = True
    status: DataStatus = DataStatus.DEMO

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """
        Performs a lightweight connectivity check.
        Returns a dictionary with status, latency, and operational details.
        """
        pass

    @abstractmethod
    def fetch(self, **kwargs) -> Any:
        """
        Fetches raw or normalized data from the provider.
        """
        pass
