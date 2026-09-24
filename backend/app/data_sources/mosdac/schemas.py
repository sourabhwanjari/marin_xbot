from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class MOSDACGranuleRecord(BaseModel):
    """Satellite earth observation granule metadata from ISRO MOSDAC catalog."""
    granule_id: str
    dataset_id: str
    satellite_mission: str = "ISRO Oceansat-3"
    sensor: Optional[str] = None
    product_name: str
    pass_timestamp: Optional[str] = None
    spatial_resolution_km: float = 1.0
    cloud_cover_percent: Optional[float] = None
    sst_c: Optional[float] = None
    chlorophyll_mg_m3: Optional[float] = None
    wind_speed_knots: Optional[float] = None
    download_url: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class MOSDACGranuleResponse(BaseModel):
    """Collection of satellite granules covering requested coordinates."""
    dataset_id: str
    total_granules: int = 0
    granules: List[MOSDACGranuleRecord] = Field(default_factory=list)
    latest_granule: Optional[MOSDACGranuleRecord] = None
    query_timestamp: Optional[str] = None
    raw_payload: Dict[str, Any] = Field(default_factory=dict)
