from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class HealthResponse(BaseModel):
    status: str
    service: str
    problem_statement: str
    version: str
    is_demo: bool

class AlertSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class MarineAlert(BaseModel):
    id: str
    type: str
    severity: AlertSeverity
    location: str
    latitude: float
    longitude: float
    radius_km: float
    time: str
    short_description: str
    advisory: str

class MarineConditions(BaseModel):
    seaSurfaceTemperature: float = Field(..., description="Sea Surface Temperature in Celsius")
    chlorophyll: str = Field(..., description="Chlorophyll concentration category")
    waveHeight: float = Field(..., description="Significant wave height in meters")
    windSpeed: float = Field(..., description="Wind speed in knots")
    windDirection: str = Field("ENE", description="Wind direction")
    seaState: str = Field(..., description="Sea condition (e.g., Calm, Moderate, Rough)")
    visibility: float = Field(..., description="Visibility in nautical miles")
    airTemperature: float = Field(29.1, description="Air temperature in Celsius")
    tide: str = Field("Incoming (High at 14:30 IST)", description="Tide phase")
    updatedAt: str

class FishingZone(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float
    distanceKm: float
    seaSurfaceTemperature: float
    chlorophyll: str
    suitability: str
    status: str  # "Favorable" | "Caution" | "Hazard"
    dominantSpecies: List[str] = []
    depthMeters: int = 45

# --- RAG Schemas ---

class SourceCitation(BaseModel):
    file: str
    page: int = 1
    doc_type: Optional[str] = "unknown"
    chunk_id: Optional[str] = None

class RagQueryRequest(BaseModel):
    question: str

class RagQueryResponse(BaseModel):
    answer: str
    sources: List[SourceCitation] = []
    retrieved_chunks: int = 0
    is_rag: bool = True

class RagIngestResponse(BaseModel):
    status: str
    documents_processed: int
    chunks_created: int
    chunks_indexed: int
    chunks_skipped: int = 0
    errors: List[Dict[str, str]] = []

class RagStatusResponse(BaseModel):
    status: str
    total_documents: int
    total_chunks: int
    embedding_provider: str
    storage_path: str
    documents: List[Dict[str, Any]] = []
    is_available: bool = True

# --- Chat Schemas ---

class ChatHistoryItem(BaseModel):
    role: str = "user"  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatHistoryItem]] = Field(default_factory=list)

class ChatResponse(BaseModel):
    message: str
    source: str = "mock-data"
    is_demo: bool = True
    suggested_actions: Optional[List[str]] = None
    related_zones: Optional[List[str]] = None
    sources: Optional[List[SourceCitation]] = []
    is_rag: Optional[bool] = False
    retrieved_chunks: Optional[int] = 0
    risk_level: Optional[str] = None
    evidence: Optional[List[str]] = []
    execution_steps: Optional[List[Dict[str, Any]]] = []
    location: Optional[str] = None
    time_context: Optional[str] = None
