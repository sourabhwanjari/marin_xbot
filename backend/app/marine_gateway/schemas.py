from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from app.marine_models.base import DataStatus, Location, TimeWindow, MarineDataResponse
from app.data_sources.common.models import ProviderHealth, ProviderCapability

class GatewayQueryFilter(BaseModel):
    """Filter parameters accepted by Marine Data Gateway endpoints."""
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    radius_km: Optional[float] = Field(50.0, ge=1.0, le=500.0)
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    location_name: Optional[str] = None
    time_context: str = "current"
    prefer_live: bool = True

class GatewayStatusResponse(BaseModel):
    """Sanitized public status report returned by /api/marine/gateway/status. Never exposes credentials."""
    status: str = "healthy"
    gateway_version: str = "Phase-5A"
    total_providers_registered: int
    providers: List[ProviderHealth] = Field(default_factory=list)
    capability_routing: Dict[str, str] = Field(default_factory=dict)
    active_cache_entries: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)
