from pydantic import BaseModel
from typing import Dict, Any, List, Optional

class PortInfo(BaseModel):
    id: str
    name: str
    type: str
    state: str
    latitude: float
    longitude: float
    distance_km: float

class RestrictedZoneCheckResult(BaseModel):
    is_restricted: bool
    zone_name: Optional[str] = None
    restriction: Optional[str] = None
    distance_km: Optional[float] = None

class ProtectedAreaCheckResult(BaseModel):
    is_protected: bool
    area_name: Optional[str] = None
    restriction: Optional[str] = None
    distance_km: Optional[float] = None
