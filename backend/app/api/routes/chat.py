from fastapi import APIRouter
from app.models.schemas import ChatRequest, ChatResponse
from app.graph.workflow import run_marine_workflow

router = APIRouter(tags=["Conversational Intelligence"])

@router.post("/chat", response_model=ChatResponse)
async def chat_interaction(request: ChatRequest):
    """
    Conversational endpoint for Marine Intelligence.
    Phase 3: Powered by the LangGraph Multi-Agent Orchestration workflow
    (Planner -> Specialized Agents -> Risk Assessment -> Response Synthesis).
    """
    history = [h.model_dump() if hasattr(h, "model_dump") else h.dict() for h in request.history] if request.history else []
    result = run_marine_workflow(query=request.message, chat_history=history)

    suggested_actions = ["Check Current Sea State", "View Active Alerts"]
    if result.get("risk_level") in ["MEDIUM", "HIGH"]:
        suggested_actions = ["Inspect Swell on Map", "View Port Control Notices", "Check Safety Guidelines"]
    elif result.get("intent") == "pfz_discovery":
        suggested_actions = ["Show Zone Alpha on Map", "Check Weather along Route"]

    related_zones = []
    if result.get("location"):
        related_zones.append(f"{result.get('location')} Sector")

    return ChatResponse(
        message=result.get("answer", "Marine assessment completed."),
        source=f"langgraph-multi-agent ({result.get('data_status', 'demo')})",
        is_demo=True,
        suggested_actions=suggested_actions,
        related_zones=related_zones,
        sources=result.get("sources", []),
        is_rag=len(result.get("sources", [])) > 0,
        retrieved_chunks=len(result.get("sources", [])),
        risk_level=result.get("risk_level"),
        evidence=result.get("evidence", []),
        execution_steps=result.get("execution_steps", []),
        location=result.get("location"),
        time_context=result.get("time_context"),
    )
