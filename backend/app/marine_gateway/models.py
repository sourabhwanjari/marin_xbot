from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from app.data_sources.base import DataStatus

class LocationPoint(BaseModel):
    latitude: float
    longitude: float
    name: Optional[str] = None

class MarineEvidence(BaseModel):
    provider: str
    dataset: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    valid_until: Optional[str] = None
    location: Dict[str, Any] = Field(default_factory=dict)
    source_reference: Optional[str] = None
    data_status: str = "demo"
    summary: str = ""

class NormalizedWeather(BaseModel):
    temperature: Optional[float] = None
    wind_speed: Optional[float] = None
    wind_direction: Optional[str] = None
    wind_direction_deg: Optional[float] = None
    rain_probability: Optional[int] = None
    weather_condition: Optional[str] = None
    visibility: Optional[float] = None
    warnings: List[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    provider: str = "Open-Meteo"
    status: str = "external"
    source_reference: Optional[str] = None
    units: Dict[str, str] = Field(default_factory=lambda: {
        "temperature": "°C",
        "wind_speed": "knots",
        "rain_probability": "%",
        "visibility": "NM"
    })

class NormalizedOcean(BaseModel):
    wave_height: Optional[float] = None
    wave_period: Optional[float] = None
    swell_height: Optional[float] = None
    swell_period: Optional[float] = None
    swell_direction: Optional[str] = None
    surface_current_speed: Optional[float] = None
    sea_surface_temperature: Optional[float] = None
    chlorophyll: Optional[str] = None
    ocean_condition: Optional[str] = None
    tide_status: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    provider: str = "Open-Meteo Marine / INCOIS"
    status: str = "external"
    source_reference: Optional[str] = None
    units: Dict[str, str] = Field(default_factory=lambda: {
        "wave_height": "m",
        "wave_period": "s",
        "swell_height": "m",
        "swell_period": "s",
        "sea_surface_temperature": "°C"
    })

class NormalizedPFZ(BaseModel):
    zone_id: str
    name: str
    latitude: float
    longitude: float
    sector: str
    advisory_date: str
    valid_until: str
    distance_km: Optional[float] = None
    direction: Optional[str] = None
    sea_surface_temperature: Optional[float] = None
    chlorophyll: Optional[str] = None
    suitability: str = "Favorable"
    status: str = "Favorable"
    dominant_species: List[str] = Field(default_factory=list)
    depth_meters: Optional[int] = 45
    provider: str = "INCOIS PFZ Advisory"
    data_status: str = "verified"
    source_reference: Optional[str] = None

class NormalizedGeospatial(BaseModel):
    coordinates: Dict[str, float]
    location_name: str
    nearest_port: Dict[str, Any] = Field(default_factory=dict)
    restricted_zone: bool = False
    restricted_zone_details: Optional[Dict[str, Any]] = None
    protected_zone: bool = False
    protected_zone_details: Optional[Dict[str, Any]] = None
    distance_from_coast_km: float = 0.0
    nearby_hazards: List[Dict[str, Any]] = Field(default_factory=list)
    provider: str = "PostGIS / GeoJSON Spatial Engine"
    status: str = "verified"
