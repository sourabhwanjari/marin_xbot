from pydantic import BaseModel
from typing import Dict, Any, Optional

class OpenMeteoMarineResponse(BaseModel):
    latitude: float
    longitude: float
    generationtime_ms: Optional[float] = None
    current: Optional[Dict[str, Any]] = None
    hourly: Optional[Dict[str, Any]] = None
