from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from app.models.schemas import SourceCitation, ChatHistoryItem

class QueryIntent(str, Enum):
    GREETING = "greeting"
    EXPLAIN_CONCEPT = "explain_concept"
    FISHING_SAFETY = "fishing_safety"
    WEATHER_INQUIRY = "weather_inquiry"
    OCEAN_CONDITIONS = "ocean_conditions"
    PFZ_DISCOVERY = "pfz_discovery"
    RESTRICTED_ZONES = "restricted_zones"
    MARINE_KNOWLEDGE = "marine_knowledge"
    GENERAL_MARINE = "general_marine"
    OUT_OF_SCOPE = "out_of_scope"

class PlannerOutput(BaseModel):
    intent: QueryIntent
    location: Optional[str] = None
    time: Optional[str] = None
    required_agents: List[str] = Field(default_factory=list)
    tasks: List[str] = Field(default_factory=list)

class WeatherResult(BaseModel):
    temperature: float
    wind_speed: float
    wind_direction: str
    rain_probability: int
    storm_risk: str
    source: str = "Demo Weather Service (IMD/GFS simulated)"
    data_status: str = "demo"

class OceanResult(BaseModel):
    sst: float
    chlorophyll: str
    wave_height: float
    ocean_condition: str
    source: str = "Demo Ocean Service (INCOIS simulated)"
    data_status: str = "demo"

class GeospatialResult(BaseModel):
    coordinates: Dict[str, float]
    location_name: str
    nearest_port: str
    restricted_zone: bool
    protected_zone: bool
    distance_from_coast_km: float
    nearest_hazard: Optional[str] = None
    source: str = "Demo Geospatial Service (PostGIS simulated)"
    data_status: str = "demo"

class RiskResult(BaseModel):
    risk_level: str  # "LOW", "MEDIUM", "HIGH"
    risk_factors: List[str] = Field(default_factory=list)
    recommendation_basis: List[str] = Field(default_factory=list)
    confidence: float = 0.85

class ExecutionStep(BaseModel):
    agent: str
    status: str  # "completed", "skipped", "failed"
    details: Optional[str] = None

class AgentChatRequest(BaseModel):
    message: str
    location: Optional[str] = None
    history: Optional[List[ChatHistoryItem]] = Field(default_factory=list)

class AgentChatResponse(BaseModel):
    answer: str
    intent: str
    risk_level: Optional[str] = None
    location: Optional[str] = None
    time_context: Optional[str] = None
    sources: List[SourceCitation] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    weather: Optional[Dict[str, Any]] = None
    ocean: Optional[Dict[str, Any]] = None
    geospatial: Optional[Dict[str, Any]] = None
    risk: Optional[Dict[str, Any]] = None
    map_data: Optional[Dict[str, Any]] = None
    execution_steps: List[ExecutionStep] = Field(default_factory=list)
    data_status: str = "demo"
    is_demo: bool = True
