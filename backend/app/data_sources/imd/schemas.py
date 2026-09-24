from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class IMDWeatherRequest(BaseModel):
    """Query parameters for IMD coastal weather requests."""
    latitude: float
    longitude: float
    station_id: Optional[str] = None
    forecast_hours: int = 24

class IMDWeatherObservation(BaseModel):
    """Raw observation schema from IMD Automatic Weather Station / coastal bulletin."""
    station_name: Optional[str] = None
    station_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    observation_time: Optional[str] = None
    air_temperature_c: Optional[float] = None
    relative_humidity_percent: Optional[float] = None
    wind_speed_knots: Optional[float] = None
    wind_direction_deg: Optional[float] = None
    wind_direction_text: Optional[str] = None
    pressure_hpa: Optional[float] = None
    rain_probability_percent: Optional[int] = None
    precipitation_mm: Optional[float] = None
    visibility_km: Optional[float] = None
    weather_condition: Optional[str] = None
    cyclone_warning: Optional[str] = None
    squall_warning: Optional[str] = None
    valid_until: Optional[str] = None
    raw_payload: Dict[str, Any] = Field(default_factory=dict)
