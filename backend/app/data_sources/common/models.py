from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class ProviderCapability(str, Enum):
    """Specific telemetry and intelligence capabilities provided by marine sources."""
    WEATHER = "WEATHER"
    OCEAN = "OCEAN"
    PFZ = "PFZ"
    SATELLITE = "SATELLITE"
    GEOSPATIAL = "GEOSPATIAL"
    HAZARDS = "HAZARDS"

class ProviderHealth(BaseModel):
    """Sanitized public status report for a marine provider adapter. Never exposes credentials."""
    provider_name: str
    capabilities: List[ProviderCapability] = Field(default_factory=list)
    enabled: bool = False
    configured: bool = False
    connection_status: str = "offline"  # online, offline, error, not_configured, simulated
    last_successful_retrieval: Optional[str] = None
    error_message: Optional[str] = None
    telemetry_type: str = "external"  # external, verified, simulated, demo
