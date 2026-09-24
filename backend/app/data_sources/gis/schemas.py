from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class GISLocationQuery(BaseModel):
    """Geospatial context query parameters."""
    latitude: float
    longitude: float
    location_name: Optional[str] = None
    search_radius_km: float = 50.0

class NearestPortInfo(BaseModel):
    """Details of nearest marine port or fish landing center."""
    name: str
    latitude: float
    longitude: float
    distance_km: float
    port_type: str = "Major Port"

class MaritimeGeofenceConstraint(BaseModel):
    """Navigational restriction, fairway, or protected marine sanctuary."""
    zone_id: str
    name: str
    zone_type: str  # "Naval Range", "Marine Sanctuary", "Commercial Fairway", "Restricted Area"
    is_restricted: bool = True
    restriction_level: str = "PROHIBITED"
    advisory: str
    distance_km: float = 0.0

class GISContextResponse(BaseModel):
    """Complete spatial context for coastal coordinates."""
    location_name: str
    latitude: float
    longitude: float
    nearest_port: NearestPortInfo
    restricted_zone: bool = False
    protected_zone: bool = False
    distance_from_coast_km: float = 0.0
    active_constraints: List[MaritimeGeofenceConstraint] = Field(default_factory=list)
    raw_payload: Dict[str, Any] = Field(default_factory=dict)
