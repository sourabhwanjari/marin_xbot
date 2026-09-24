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
    logger.info(f"[ROUTER] Routing for intent '{intent}', selected agents: {selected_agents}")

    target = "response"
    if intent in [QueryIntent.OUT_OF_SCOPE.value, QueryIntent.GREETING.value, QueryIntent.EXPLAIN_CONCEPT.value]:
        target = "response"
    elif intent == QueryIntent.FISHING_SAFETY.value or "risk" in selected_agents:
        target = "weather"
    elif intent == QueryIntent.WEATHER_INQUIRY.value:
        target = "weather"
    elif intent == QueryIntent.OCEAN_CONDITIONS.value:
        target = "ocean"
    elif intent == QueryIntent.PFZ_DISCOVERY.value:
        target = "ocean"
    elif intent == QueryIntent.SATELLITE_DATA.value or "satellite" in selected_agents:
        target = "satellite"
    elif intent == QueryIntent.RESTRICTED_ZONES.value:
        target = "geospatial"
    elif intent == QueryIntent.MARINE_KNOWLEDGE.value:
        target = "marine_knowledge"
    elif "weather" in selected_agents:
        target = "weather"
    elif "ocean" in selected_agents:
        target = "ocean"
    elif "satellite" in selected_agents:
        target = "satellite"
    elif "geospatial" in selected_agents:
        target = "geospatial"
    elif "marine_knowledge" in selected_agents:
        target = "marine_knowledge"

    logger.info(f"[ROUTER] Planner routed to '{target}' for intent='{intent}'")
    return target

def route_after_weather(state: MarineAgentState) -> str:
    """
    After Weather Node: Check if Ocean, Satellite, Geospatial, etc. is required.
    """
    selected = state.get("selected_agents", [])
    if "ocean" in selected:
        target = "ocean"
    elif "satellite" in selected:
        target = "satellite"
    elif "geospatial" in selected:
        target = "geospatial"
    elif "marine_knowledge" in selected:
        target = "marine_knowledge"
    elif "risk" in selected:
        target = "risk"
    else:
        target = "response"
    logger.info(f"[ROUTER] After weather routed to '{target}'")
    return target

def route_after_ocean(state: MarineAgentState) -> str:
    """
    After Ocean Node: Check if Geospatial, Satellite, Knowledge, Risk, or Response is next.
    """
    selected = state.get("selected_agents", [])
    if "satellite" in selected:
        target = "satellite"
    elif "geospatial" in selected:
        target = "geospatial"
    elif "marine_knowledge" in selected:
        target = "marine_knowledge"
    elif "risk" in selected:
        target = "risk"
    else:
        target = "response"
    logger.info(f"[ROUTER] After ocean routed to '{target}'")
    return target

def route_after_satellite(state: MarineAgentState) -> str:
    """
    After Satellite Node: Check if Geospatial, Knowledge, Risk, or Response is next.
    """
    selected = state.get("selected_agents", [])
    if "geospatial" in selected:
        target = "geospatial"
    elif "marine_knowledge" in selected:
        target = "marine_knowledge"
    elif "risk" in selected:
        target = "risk"
    else:
        target = "response"
    logger.info(f"[ROUTER] After satellite routed to '{target}'")
    return target

def route_after_geospatial(state: MarineAgentState) -> str:
    """
    After Geospatial Node: Check if Marine Knowledge, Risk, or Response is next.
    """
    selected = state.get("selected_agents", [])
    if "marine_knowledge" in selected:
        target = "marine_knowledge"
    elif "risk" in selected:
        target = "risk"
    else:
        target = "response"
    logger.info(f"[ROUTER] After geospatial routed to '{target}'")
    return target

def route_after_knowledge(state: MarineAgentState) -> str:
    """
    After Marine Knowledge Node: Check if Risk or Response is next.
    """
    selected = state.get("selected_agents", [])
    if "risk" in selected:
        target = "risk"
    else:
        target = "response"
    logger.info(f"[ROUTER] After knowledge routed to '{target}'")
    return target
