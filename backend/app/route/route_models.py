from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone

class RoutePoint(BaseModel):
    """Geographic point representing an origin, destination, or waypoint."""
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    name: Optional[str] = None
    port: Optional[str] = None

    def to_tuple(self) -> Tuple[float, float]:
        return (self.latitude, self.longitude)

class RouteWaypoint(BaseModel):
    """Individual navigational waypoint along a marine route."""
    order: int
    latitude: float
    longitude: float
    name: Optional[str] = None
    segment_distance_km: float = 0.0
    notes: Optional[str] = None

class RouteConditions(BaseModel):
    """Meteorological and oceanographic conditions observed along the route."""
    avg_wind_speed_knots: Optional[float] = None
    max_wave_height_m: Optional[float] = None
    sea_surface_temp_c: Optional[float] = None
    sea_state: Optional[str] = None
    weather_summary: Optional[str] = None
    tide_status: Optional[str] = None
    advisory_active: bool = False
    squall_warning: Optional[str] = None

class RouteRequest(BaseModel):
    """Standardized request for calculating a marine route."""
    origin: RoutePoint
    destination: RoutePoint
    departure_time: Optional[str] = "current"
    vessel_type: str = Field("fishing_boat", description="Vessel type: artisanal_boat, fishing_boat, trawler, cargo, vessel")
    vessel_speed_knots: float = Field(10.0, ge=1.0, le=40.0, description="Cruising speed in knots")
    route_preference: str = Field("balanced", description="Preference: safest, shortest, balanced")
    avoid_zones: List[str] = Field(default_factory=list, description="Specific zone IDs to explicitly avoid")

class RouteCandidate(BaseModel):
    """Evaluated route candidate option."""
    id: str
    name: str
    description: str
    waypoints: List[List[float]]  # [[lat, lon], ...]
    distance_km: float
    estimated_duration_hours: float
    costs: Dict[str, float] = Field(default_factory=dict)
    total_cost: float = 0.0
    safety_score: int = 80  # 0 to 100
    risk_level: str = "MODERATE"  # LOW, MODERATE, HIGH, UNAVAILABLE
    is_valid: bool = True
    restricted_violations: List[str] = Field(default_factory=list)
    hazards_intersected: List[str] = Field(default_factory=list)

class RouteResponse(BaseModel):
    """Standardized response schema for marine route recommendations."""
    route_id: str
    origin: RoutePoint
    destination: RoutePoint
    route_geometry: Dict[str, Any] = Field(default_factory=dict, description="GeoJSON LineString")
    waypoints: List[List[float]] = Field(default_factory=list, description="List of [lat, lon] coordinates")
    distance_km: float
    estimated_duration_hours: float
    estimated_duration_text: str
    safety_score: int
    risk_level: str  # LOW, MODERATE, HIGH, UNAVAILABLE
    route_conditions: RouteConditions
    hazards_avoided: List[str] = Field(default_factory=list)
    avoided_zones: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    calculated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    explanation: str
    status: str = "SUCCESS"  # SUCCESS, UNAVAILABLE, ERROR
    alternative_routes: List[Dict[str, Any]] = Field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()
