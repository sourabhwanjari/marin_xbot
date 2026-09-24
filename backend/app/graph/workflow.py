import logging
from typing import Dict, Any, Optional, List
from langgraph.graph import StateGraph, START, END

from app.graph.state import MarineAgentState
from app.graph.nodes import (
    planner_node,
    weather_node,
    ocean_node,
    satellite_node,
    geospatial_node,
    marine_knowledge_node,
    risk_node,
    response_node,
)
from app.graph.edges import (
    route_from_planner,
    route_after_weather,
    route_after_ocean,
    route_after_satellite,
    route_after_geospatial,
    route_after_knowledge,
)

logger = logging.getLogger("marinex.graph.workflow")

def build_marine_graph() -> StateGraph:
    """
    Constructs the LangGraph multi-agent orchestration workflow.
    """
    workflow = StateGraph(MarineAgentState)

    # 1. Register agent nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("weather", weather_node)
    workflow.add_node("ocean", ocean_node)
    workflow.add_node("satellite", satellite_node)
    workflow.add_node("geospatial", geospatial_node)
    workflow.add_node("marine_knowledge", marine_knowledge_node)
    workflow.add_node("risk", risk_node)
    workflow.add_node("response", response_node)

    # 2. Add edges & conditional transitions
    workflow.add_edge(START, "planner")

    workflow.add_conditional_edges(
        "planner",
        route_from_planner,
        {
            "weather": "weather",
            "ocean": "ocean",
            "satellite": "satellite",
            "geospatial": "geospatial",
            "marine_knowledge": "marine_knowledge",
            "response": "response",
        }
    )

    workflow.add_conditional_edges(
        "weather",
        route_after_weather,
        {
            "ocean": "ocean",
            "satellite": "satellite",
            "geospatial": "geospatial",
            "marine_knowledge": "marine_knowledge",
            "risk": "risk",
            "response": "response",
        }
    )

    workflow.add_conditional_edges(
        "ocean",
        route_after_ocean,
        {
            "satellite": "satellite",
            "geospatial": "geospatial",
            "marine_knowledge": "marine_knowledge",
            "risk": "risk",
            "response": "response",
        }
    )

    workflow.add_conditional_edges(
        "satellite",
        route_after_satellite,
        {
            "geospatial": "geospatial",
            "marine_knowledge": "marine_knowledge",
            "risk": "risk",
            "response": "response",
        }
    )

    workflow.add_conditional_edges(
        "geospatial",
        route_after_geospatial,
        {
            "marine_knowledge": "marine_knowledge",
            "risk": "risk",
            "response": "response",
        }
    )

    workflow.add_conditional_edges(
        "marine_knowledge",
        route_after_knowledge,
        {
            "risk": "risk",
            "response": "response",
        }
    )

    workflow.add_edge("risk", "response")
    workflow.add_edge("response", END)

    return workflow

# Compile graph once
marine_graph = build_marine_graph()
compiled_marine_workflow = marine_graph.compile()

def run_marine_workflow(
    query: str,
    location: Optional[str] = None,
    chat_history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Executes the LangGraph multi-agent orchestration workflow for a marine query.
    Returns structured results ready for API responses.
    """
    logger.info(f"[LANGGRAPH] Starting workflow execution for query: '{query}'")

    initial_state: MarineAgentState = {
        "user_query": query,
        "chat_history": chat_history or [],
        "intent": None,
        "location": {"name": location} if location else None,
        "time_context": None,
        "tasks": [],
        "selected_agents": [],
        "rag_results": [],
        "weather_results": None,
        "ocean_results": None,
        "geospatial_results": None,
        "satellite_results": None,
        "risk_results": None,
        "evidence": [],
        "intermediate_results": [],
        "final_answer": None,
        "response_type": None,
        "errors": [],
        "execution_steps": [],
        "data_status": "demo"
    }

    try:
        final_state = compiled_marine_workflow.invoke(initial_state)
        logger.info(f"[LANGGRAPH] Workflow execution completed for query: '{query}'")
    except Exception as e:
        logger.error(f"[LANGGRAPH] Invocation error: {e}")
        # Fallback response if graph fails
        return {
            "answer": f"Marine Intelligence Service: Unable to complete multi-agent workflow ({str(e)}).",
            "intent": "general_marine",
            "risk_level": "MEDIUM",
            "location": location or "Chennai",
            "time_context": "current",
            "sources": [],
            "evidence": ["Error during agent orchestration"],
            "weather": None,
            "ocean": None,
            "geospatial": None,
            "satellite": None,
            "risk": None,
            "map_data": None,
            "execution_steps": [{"agent": "workflow", "status": "failed", "details": str(e)}],
            "data_status": "demo",
            "is_demo": True
        }

    # Extract sources from RAG results
    sources = []
    rag_res = final_state.get("rag_results", [])
    if rag_res and isinstance(rag_res[0], dict):
        sources = rag_res[0].get("sources", [])

    risk_res = final_state.get("risk_results")
    risk_lvl = risk_res.get("risk_level") if risk_res else None

    # Map data for GIS visualization
    map_data = final_state.get("map_data")
    geospatial_res = final_state.get("geospatial_results")
    if not map_data and geospatial_res:
        if geospatial_res.get("map_data"):
            map_data = geospatial_res["map_data"]
        elif geospatial_res.get("coordinates"):
            map_data = {
                "center": geospatial_res["coordinates"],
                "location_name": geospatial_res.get("location_name"),
                "nearest_port": geospatial_res.get("nearest_port"),
                "restricted_zone": geospatial_res.get("restricted_zone", False),
                "protected_zone": geospatial_res.get("protected_zone", False)
            }

    return {
        "answer": final_state.get("final_answer") or "Marine assessment completed.",
        "intent": final_state.get("intent") or "general_marine",
        "risk_level": risk_lvl,
        "location": final_state.get("location", {}).get("name") if final_state.get("location") else location,
        "time_context": final_state.get("time_context", {}).get("name") if final_state.get("time_context") else "current",
        "sources": sources,
        "evidence": final_state.get("evidence", []),
        "weather": final_state.get("weather_results"),
        "ocean": final_state.get("ocean_results"),
        "geospatial": geospatial_res,
        "satellite": final_state.get("satellite_results"),
        "risk": risk_res,
        "map_data": map_data,
        "execution_steps": final_state.get("execution_steps", []),
        "data_status": final_state.get("data_status", "demo"),
        "is_demo": True
    }
