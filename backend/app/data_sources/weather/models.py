from pydantic import BaseModel
from typing import Dict, Any, Optional, List

class OpenMeteoWeatherResponse(BaseModel):
    latitude: float
    longitude: float
    generationtime_ms: Optional[float] = None
    timezone: Optional[str] = None
    current: Optional[Dict[str, Any]] = None
    hourly: Optional[Dict[str, Any]] = None
