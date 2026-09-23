from fastapi import APIRouter, HTTPException
from app.models.agent_models import AgentChatRequest, AgentChatResponse
from app.graph.workflow import run_marine_workflow

router = APIRouter(prefix="/agent", tags=["Multi-Agent Orchestration"])

@router.post("/chat", response_model=AgentChatResponse)
async def agent_chat_interaction(request: AgentChatRequest):
    """
    LangGraph Multi-Agent Orchestration endpoint.
    Decomposes the query, selects specialized agents (Weather, Ocean, Geospatial,
    Marine Knowledge/RAG, Risk Assessment), coordinates evidence, and synthesizes
    an actionable marine decision support recommendation.
    """
    try:
        history = [h.model_dump() if hasattr(h, "model_dump") else h.dict() for h in request.history] if request.history else []
        result = run_marine_workflow(
            query=request.message,
            location=request.location,
            chat_history=history
        )
        return AgentChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent workflow failed: {str(e)}")

@router.get("/status")
async def get_agent_status():
    """
    Returns registered agents, workflow graph nodes, and orchestration readiness.
    """
    return {
        "status": "active",
        "orchestrator": "LangGraph StateGraph",
        "registered_agents": [
            {"name": "planner", "role": "Intent Classification & Task Decomposition"},
            {"name": "weather", "role": "Meteorological & Wind Squall Analysis"},
            {"name": "ocean", "role": "Oceanographic & Wave Spectral Analysis"},
            {"name": "geospatial", "role": "Coordinate & Maritime Geofencing Analysis"},
            {"name": "marine_knowledge", "role": "Chroma RAG Document Retrieval"},
            {"name": "risk", "role": "Multi-Factor Marine Risk Reasoning"},
            {"name": "response", "role": "Actionable Decision Synthesis"},
        ],
        "data_status": "demo",
        "is_available": True
    }
