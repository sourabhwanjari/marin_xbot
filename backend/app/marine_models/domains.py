from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from app.marine_models.base import MarineDataResponse, DataStatus

class WeatherData(BaseModel):
    """Meteorological marine conditions."""
    temperature: Optional[float] = Field(None, description="Air temperature in Celsius")
    apparent_temperature: Optional[float] = Field(None, description="Feels-like temperature in Celsius")
    wind_speed: Optional[float] = Field(None, description="Wind speed in knots")
    wind_speed_knots: Optional[float] = Field(None, description="Wind speed in knots")
    wind_direction: Optional[str] = Field(None, description="Wind direction (e.g. ENE, 65°)")
    wind_direction_deg: Optional[float] = Field(None, description="Wind direction in meteorological degrees")
    humidity: Optional[float] = Field(None, description="Relative humidity percentage")
    wind_gust: Optional[float] = Field(None, description="Peak wind gust in knots")
    rain_probability: Optional[int] = Field(None, description="Precipitation probability 0-100%")
    precipitation_mm: Optional[float] = Field(None, description="Precipitation accumulation in mm")
    weather_code: Optional[int] = Field(None, description="WMO weather interpretation code")
    condition_text: Optional[str] = Field(None, description="Human readable condition synopsis")
    storm_risk: str = Field("low", description="Storm or squall risk: low, moderate, high")
    weather_condition: Optional[str] = Field(None, description="Brief synopsis")
    visibility_km: Optional[float] = Field(None, description="Horizontal visibility in km")
    pressure_hpa: Optional[float] = Field(None, description="Atmospheric sea level pressure in hPa")
    warnings: List[str] = Field(default_factory=list)

    def __init__(self, **data):
        if "wind_speed_knots" in data and "wind_speed" not in data:
            data["wind_speed"] = data["wind_speed_knots"]
        if "wind_speed" in data and "wind_speed_knots" not in data:
            data["wind_speed_knots"] = data["wind_speed"]
        if "condition_text" in data and "weather_condition" not in data:
            data["weather_condition"] = data["condition_text"]
        super().__init__(**data)

class OceanData(BaseModel):
    """Hydrodynamic and oceanographic telemetry."""
    sst: Optional[float] = Field(None, description="Sea Surface Temperature in Celsius")
    chlorophyll: Optional[str] = Field(None, description="Chlorophyll-a category or mg/m³")
    wave_height: Optional[float] = Field(None, description="Significant wave height in meters")
    swell_period: Optional[float] = Field(None, description="Dominant swell wave period in seconds")
    swell_direction: Optional[str] = Field(None, description="Swell wave propagation direction")
    ocean_condition: Optional[str] = Field(None, description="Sea condition: calm, slight, moderate, rough")
    tide_status: Optional[str] = Field(None, description="Tidal status and upcoming high/low phase")
    suitability: str = Field("Favorable", description="Voyage/fishing suitability")

class PFZFeature(BaseModel):
    """Individual Potential Fishing Zone delineated feature."""
    zone_id: str
    name: str
    latitude: float
    longitude: float
    sector: str
    distance_km: float
    direction: str
    sst: float
    chlorophyll: str
    suitability: str
    status: str = "Favorable"
    dominant_species: List[str] = Field(default_factory=list)
    depth_meters: int = 40
    advisory_date: Optional[str] = None
    valid_until: Optional[str] = None

class PFZData(BaseModel):
    """PFZ advisory collection."""
    zones: List[PFZFeature] = Field(default_factory=list)
    nearest_zone: Optional[PFZFeature] = None
    total_active_zones: int = 0
    advisory_date: Optional[str] = None
    geojson: Optional[Dict[str, Any]] = None

class SatelliteData(BaseModel):
    """Satellite earth observation metadata and granule references."""
    product_name: str
    satellite_mission: str = "ISRO Oceansat / INSAT-3D"
    sensor: Optional[str] = None
    spatial_resolution_km: float = 1.0
    pass_time: Optional[str] = None
    granule_id: Optional[str] = None
    cloud_cover_percent: Optional[float] = None
    status: DataStatus = DataStatus.NOT_CONFIGURED
    message: str = "Satellite earth observation service"

class GeospatialData(BaseModel):
    """Maritime boundaries, fairways, ports, and navigational constraints."""
    location_name: str
    latitude: float
    longitude: float
    nearest_port: Dict[str, Any] = Field(default_factory=dict)
    restricted_zone: bool = False
    protected_zone: bool = False
    distance_from_coast_km: float = 0.0
    nearest_hazard: Optional[str] = None
    restriction_details: Optional[str] = None
    map_data: Optional[Dict[str, Any]] = None

class HazardData(BaseModel):
    """Marine weather hazards, squalls, cyclone alerts, and wave advisories."""
    alert_id: str
    hazard_type: str
    severity: str  # "LOW", "MEDIUM", "HIGH"
    location_name: str
    latitude: float
    longitude: float
    radius_km: float
    description: str
    advisory: str
    effective_time: str
    expires_time: Optional[str] = None
    issuing_authority: str = "IMD / Coast Guard"
