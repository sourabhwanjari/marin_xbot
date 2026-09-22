from pydantic import BaseModel
from typing import Dict, Any, List, Optional

class SatelliteProductMetadata(BaseModel):
    product_key: str
    name: str
    dataset_id: str
    enabled: bool = False
    spatial_resolution: str = "1 km"
    temporal_resolution: str = "Daily"
    format: str = "NetCDF4"

class SatelliteQueryResult(BaseModel):
    status: str  # "not_configured", "available", "unavailable"
    message: str
    provider: str = "ISRO MOSDAC"
    products: List[Dict[str, Any]] = []
    data_status: str = "not_configured"
