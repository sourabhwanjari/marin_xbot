from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field

class DataStatus(str, Enum):
    """Permitted operational status values across all marine data providers and gateway responses."""
    DEMO = "demo"
    SIMULATED = "simulated"
    EXTERNAL = "external"
    VERIFIED = "verified"
    NOT_CONFIGURED = "not_configured"
    UNAVAILABLE = "unavailable"
    ERROR = "error"

    def __eq__(self, other):
        if isinstance(other, str):
            return self.value.lower() == other.lower() or self.name.lower() == other.lower()
        return super().__eq__(other)

    def __hash__(self):
        return super().__hash__()

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            val_lower = value.lower()
            for member in cls:
                if member.value == val_lower or member.name.lower() == val_lower:
                    return member
        return None

class Location(BaseModel):
    """Geographic point representation for marine queries and telemetry."""
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees")
    name: Optional[str] = Field(None, description="Human-readable coastal name or port")
    port: Optional[str] = Field(None, description="Associated base port or fish landing center")
    country: str = Field("India", description="Sovereign coastal jurisdiction")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "name": self.name,
            "port": self.port,
            "country": self.country
        }

class BoundingBox(BaseModel):
    """Bounding box for spatial queries and satellite scene clipping."""
    min_lat: float = Field(..., ge=-90.0, le=90.0)
    min_lon: float = Field(..., ge=-180.0, le=180.0)
    max_lat: float = Field(..., ge=-90.0, le=90.0)
    max_lon: float = Field(..., ge=-180.0, le=180.0)

    def contains(self, lat: float, lon: float) -> bool:
        return self.min_lat <= lat <= self.max_lat and self.min_lon <= lon <= self.max_lon

class TimeWindow(BaseModel):
    """Temporal constraints for observational and forecast data retrieval."""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    context: str = Field("current", description="Time description: current, tomorrow, 24h forecast, etc.")

class MarineEvidence(BaseModel):
    """Provenance and audit trail metadata for every marine observation."""
    source: str = Field("MARINEX-Gateway", description="Originating authority or instrument system (e.g. IMD, INCOIS, MOSDAC)")
    provider: str = Field("ProviderAdapter", description="Provider adapter name")
    source_provider: Optional[str] = None
    dataset: Optional[str] = Field(None, description="Official dataset identifier or mission name")
    source_dataset: Optional[str] = None
    parameter: Optional[str] = Field(None, description="Primary parameter observed (e.g. sst, wave_height, wind)")
    observed_at: Optional[str] = None
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    retrieved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="Gateway ingestion timestamp")
    retrieval_timestamp: Optional[Union[datetime, str]] = None
    quality: str = Field("OPERATIONAL", description="Data quality classification")
    confidence_score: float = Field(1.0, ge=0.0, le=1.0, description="Verification confidence score")
    verification_status: Optional[DataStatus] = None
    status: DataStatus = Field(DataStatus.DEMO, description="Provenance status")
    notes: Optional[str] = None
    evidence_url: Optional[str] = Field(None, description="Direct URL to official bulletin or documentation")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional provider-specific metadata")

    def __init__(self, **data):
        if "source_provider" in data:
            data["provider"] = data.get("provider") or data["source_provider"]
            data["source"] = data.get("source") or data["source_provider"]
        elif "source" in data and "provider" not in data:
            data["provider"] = data["source"]
        if "source_dataset" in data and "dataset" not in data:
            data["dataset"] = data["source_dataset"]
        if "retrieval_timestamp" in data and "retrieved_at" not in data:
            rt = data["retrieval_timestamp"]
            data["retrieved_at"] = rt.isoformat() if hasattr(rt, "isoformat") else str(rt)
        if "verification_status" in data and "status" not in data:
            data["status"] = data["verification_status"]
        super().__init__(**data)

class MarineDataPoint(BaseModel):
    """Single normalized scalar observation."""
    parameter: str = Field(..., description="Observed parameter identifier")
    value: Optional[Union[float, int, str, bool]] = Field(None, description="Measured parameter value")
    unit: Optional[str] = Field(None, description="Unit of measurement (m, knots, °C, mg/m³, etc.)")
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timestamp: Optional[Union[datetime, str]] = None
    observed_at: Optional[str] = None
    source: Optional[str] = None
    provider: Optional[str] = None
    dataset: Optional[str] = None
    quality: str = "OPERATIONAL"
    status: DataStatus = DataStatus.DEMO

    def __init__(self, **data):
        if "timestamp" in data and "observed_at" not in data:
            ts = data["timestamp"]
            data["observed_at"] = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)
        super().__init__(**data)

class MarineDataResponse(BaseModel):
    """
    Standard normalized response schema returned by all marine providers and gateway endpoints.
    Provides complete provenance, location, data payload, and evidence.
    """
    status: DataStatus = Field(..., description="Standardized operational status")
    provider: str = Field(..., description="Executing provider adapter")
    dataset: Optional[str] = Field(None, description="Originating dataset or telemetry source")
    parameter: Optional[str] = Field(None, description="Primary parameter query identifier")
    value: Optional[Any] = Field(None, description="Primary value if scalar")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    observed_at: Optional[str] = None
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    retrieved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    quality: str = Field("OPERATIONAL", description="Quality index")
    evidence_url: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    location: Optional[Union[Dict[str, Any], Location]] = Field(default_factory=dict)
    data: Any = Field(default_factory=dict)
    evidence: Union[List[MarineEvidence], MarineEvidence] = Field(default_factory=list)

    def __init__(self, **data):
        if "retrieved_at" in data and hasattr(data["retrieved_at"], "isoformat"):
            data["retrieved_at"] = data["retrieved_at"].isoformat()
        if "evidence" in data and isinstance(data["evidence"], MarineEvidence):
            data["evidence"] = [data["evidence"]]
        super().__init__(**data)

    def _get_attr(self, name: str, default: Any = None) -> Any:
        if isinstance(self.data, dict):
            return self.data.get(name, default)
        return getattr(self.data, name, default)

    @property
    def temperature(self) -> Optional[float]:
        return self._get_attr("temperature")

    @property
    def wind_speed(self) -> Optional[float]:
        return self._get_attr("wind_speed") or self._get_attr("wind_speed_knots")

    @property
    def wind_direction(self) -> Optional[str]:
        return self._get_attr("wind_direction")

    @property
    def humidity(self) -> Optional[float]:
        return self._get_attr("humidity")

    @property
    def rain_probability(self) -> Optional[int]:
        return self._get_attr("rain_probability")

    @property
    def weather_condition(self) -> Optional[str]:
        return self._get_attr("weather_condition") or self._get_attr("condition_text")

    @property
    def warnings(self) -> List[str]:
        return self._get_attr("warnings", [])

    @property
    def wave_height(self) -> Optional[float]:
        return self._get_attr("wave_height")

    @property
    def sea_surface_temperature(self) -> Optional[float]:
        return self._get_attr("sea_surface_temperature") or self._get_attr("sst")

    @property
    def sst(self) -> Optional[float]:
        return self.sea_surface_temperature

    @property
    def ocean_condition(self) -> Optional[str]:
        return self._get_attr("ocean_condition")

    @property
    def chlorophyll(self) -> Optional[str]:
        return self._get_attr("chlorophyll")

    @property
    def swell_period(self) -> Optional[float]:
        return self._get_attr("swell_period")

    @property
    def tide_status(self) -> Optional[str]:
        return self._get_attr("tide_status")

    @property
    def units(self) -> Dict[str, str]:
        return self._get_attr("units", {
            "temperature": "°C",
            "wind_speed": "knots",
            "rain_probability": "%",
            "wave_height": "m"
        })

    @property
    def timestamp(self) -> str:
        return self.retrieved_at

    @property
    def nearest_port(self) -> Dict[str, Any]:
        return self._get_attr("nearest_port", {})

    @property
    def restricted_zone(self) -> bool:
        return self._get_attr("restricted_zone", False)

    @property
    def source_reference(self) -> Optional[str]:
        return self.metadata.get("source_reference") or self.dataset

    def to_dict(self) -> Dict[str, Any]:
        loc_val = self.location.to_dict() if hasattr(self.location, "to_dict") else (self.location if isinstance(self.location, dict) else {})
        data_val = self.data.model_dump() if hasattr(self.data, "model_dump") else (self.data if isinstance(self.data, dict) else {})
        ev_list = self.evidence if isinstance(self.evidence, list) else [self.evidence]
        ev_serialized = [e.model_dump() if hasattr(e, "model_dump") else e for e in ev_list]

        return {
            "status": self.status.value if hasattr(self.status, "value") else str(self.status),
            "provider": self.provider,
            "dataset": self.dataset,
            "parameter": self.parameter,
            "value": self.value,
            "unit": self.unit,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "observed_at": self.observed_at,
            "valid_from": self.valid_from,
            "valid_until": self.valid_until,
            "retrieved_at": self.retrieved_at,
            "quality": self.quality,
            "evidence_url": self.evidence_url,
            "metadata": self.metadata,
            "location": loc_val,
            "data": data_val,
            "evidence": ev_serialized
        }
