from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class INCOISOceanObservation(BaseModel):
    """Raw oceanographic observation from INCOIS hydrodynamic wave model / buoy network."""
    sector_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    observation_time: Optional[str] = None
    valid_until: Optional[str] = None
    sea_surface_temperature_c: Optional[float] = None
    significant_wave_height_m: Optional[float] = None
    swell_wave_period_s: Optional[float] = None
    swell_wave_direction_deg: Optional[float] = None
    swell_direction_text: Optional[str] = None
    sea_state: Optional[str] = None
    current_speed_m_s: Optional[float] = None
    tide_status: Optional[str] = None
    high_wave_alert: Optional[str] = None
    suitability: str = "Favorable"
    raw_payload: Dict[str, Any] = Field(default_factory=dict)

class INCOISPFZRecord(BaseModel):
    """Individual PFZ sector advisory returned by INCOIS mission."""
    zone_id: str
    name: str
    latitude: float
    longitude: float
    sector: str
    distance_km: float
    direction: str
    sst_c: float
    chlorophyll: str
    suitability: str = "Favorable"
    dominant_species: List[str] = Field(default_factory=list)
    depth_meters: int = 40
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None

class INCOISPFZResponse(BaseModel):
    """Collection of PFZ advisories for an oceanic sector."""
    advisory_id: Optional[str] = None
    advisory_date: Optional[str] = None
    valid_until: Optional[str] = None
    total_active_zones: int = 0
    zones: List[INCOISPFZRecord] = Field(default_factory=list)
    nearest_zone: Optional[INCOISPFZRecord] = None
    raw_payload: Dict[str, Any] = Field(default_factory=dict)
