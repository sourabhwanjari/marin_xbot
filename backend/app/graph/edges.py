import logging
from typing import List, Literal
from app.graph.state import MarineAgentState
from app.models.agent_models import QueryIntent

logger = logging.getLogger("marinex.graph.edges")

def route_from_planner(state: MarineAgentState) -> str:
    """
    Evaluates Planner output and routes to the first required agent node,
    or directly to response if out-of-scope.
    """
    intent = state.get("intent")
    selected_agents = state.get("selected_agents", [])
    logger.info(f"[LangGraph Router] Routing for intent '{intent}', selected agents: {selected_agents}")

    if intent in [QueryIntent.OUT_OF_SCOPE.value, QueryIntent.GREETING.value, QueryIntent.EXPLAIN_CONCEPT.value]:
        return "response"

    if intent == QueryIntent.FISHING_SAFETY.value or "risk" in selected_agents:
        # Complex safety pipeline starts with weather
        return "weather"

    if intent == QueryIntent.WEATHER_INQUIRY.value:
        return "weather"

    if intent == QueryIntent.OCEAN_CONDITIONS.value:
        return "ocean"

    if intent == QueryIntent.PFZ_DISCOVERY.value:
        return "ocean"

    if intent == QueryIntent.RESTRICTED_ZONES.value:
        return "geospatial"

    if intent == QueryIntent.MARINE_KNOWLEDGE.value:
        return "marine_knowledge"

    # Default fallback
    if "weather" in selected_agents:
        return "weather"
    elif "ocean" in selected_agents:
        return "ocean"
    elif "geospatial" in selected_agents:
        return "geospatial"
    elif "marine_knowledge" in selected_agents:
        return "marine_knowledge"
    else:
        return "response"

def route_after_weather(state: MarineAgentState) -> str:
    """
    After Weather Node: Check if Ocean is required, or route to Response.
    """
    selected = state.get("selected_agents", [])
    if "ocean" in selected:
        return "ocean"
    elif "geospatial" in selected:
        return "geospatial"
    elif "marine_knowledge" in selected:
        return "marine_knowledge"
    elif "risk" in selected:
        return "risk"
    return "response"

def route_after_ocean(state: MarineAgentState) -> str:
    """
    After Ocean Node: Check if Geospatial, Knowledge, Risk, or Response is next.
    """
    selected = state.get("selected_agents", [])
    if "geospatial" in selected:
        return "geospatial"
    elif "marine_knowledge" in selected:
        return "marine_knowledge"
    elif "risk" in selected:
        return "risk"
    return "response"

def route_after_geospatial(state: MarineAgentState) -> str:
    """
    After Geospatial Node: Check if Marine Knowledge, Risk, or Response is next.
    """
    selected = state.get("selected_agents", [])
    if "marine_knowledge" in selected:
        return "marine_knowledge"
    elif "risk" in selected:
        return "risk"
    return "response"

def route_after_knowledge(state: MarineAgentState) -> str:
    """
    After Marine Knowledge Node: Check if Risk or Response is next.
    """
    selected = state.get("selected_agents", [])
    if "risk" in selected:
        return "risk"
    return "response"
