from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class PFZZoneModel(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float
    sector: str
    advisory_date: str
    valid_until: str
    distance_km: float
    direction: str
    sea_surface_temperature: float
    chlorophyll: str
    suitability: str
    status: str
    dominant_species: List[str] = Field(default_factory=list)
    depth_meters: int = 45
    provider: str = "INCOIS PFZ Mission"
    data_status: str = "verified_sample"
    source_reference: Optional[str] = None
