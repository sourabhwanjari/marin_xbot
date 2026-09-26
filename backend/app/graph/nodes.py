import logging
from typing import Dict, Any
from app.graph.state import MarineAgentState
from app.agents.planner_agent import planner_agent
from app.agents.weather_agent import weather_agent
from app.agents.ocean_agent import ocean_agent
from app.agents.geospatial_agent import geospatial_agent
from app.agents.satellite_agent import satellite_agent
from app.agents.marine_knowledge_agent import marine_knowledge_agent
from app.agents.risk_agent import risk_agent
from app.agents.route_agent import route_agent
from app.agents.response_agent import response_agent
from app.language.language_service import language_service

logger = logging.getLogger("marinex.graph.nodes")

def add_step(state: MarineAgentState, agent: str, status: str, details: str = None):
    steps = state.get("execution_steps", [])
    steps.append({"agent": agent, "status": status, "details": details})
    state["execution_steps"] = steps

def planner_node(state: MarineAgentState) -> MarineAgentState:
    """Planner Node: Decomposes query, detects language, and selects required specialized agents."""
    logger.info("[LangGraph] Executing planner_node")
    query = state.get("user_query", "")
    history = state.get("chat_history", [])
    default_loc = state.get("location", {}).get("name") if state.get("location") else None

    # Detect user language with multi-turn persistence
    lang_res = language_service.detect_language(query, history=history)
    detected_lang = lang_res.language
    state["detected_language"] = detected_lang
    state["response_language"] = detected_lang
    logger.info(f"[LANGUAGE] Detected language: {detected_lang} (confidence: {lang_res.confidence})")


    plan = planner_agent.plan(query, default_location=default_loc, chat_history=history)

    state["intent"] = plan.intent.value
    state["tasks"] = plan.tasks
    state["selected_agents"] = plan.required_agents
    state["location"] = {"name": plan.location} if plan.location else {"name": "Chennai"}
    state["origin"] = {"name": plan.origin} if plan.origin else (state.get("location") or {"name": "Chennai"})
    state["destination"] = {"name": plan.destination} if plan.destination else {"name": "Pulicat"}
    state["time_context"] = {"name": plan.time} if plan.time else {"name": "current"}

    add_step(
        state,
        agent="planner",
        status="completed",
        details=f"Lang: {detected_lang} | Intent: {plan.intent.value} | Agents: {', '.join(plan.required_agents) if plan.required_agents else 'None'}"
    )
    return state


def weather_node(state: MarineAgentState) -> MarineAgentState:
    """Weather Node: Queries and analyzes meteorological conditions."""
    logger.info("[LangGraph] Executing weather_node")
    loc = state.get("location", {}).get("name", "Chennai")
    time_ctx = state.get("time_context", {}).get("name", "current")

    try:
        res = weather_agent.run(location=loc, time_context=time_ctx)
        state["weather_results"] = res
        add_step(state, agent="weather", status="completed", details=f"Wind: {res.get('wind_speed')} kts ({res.get('wind_direction')})")
    except Exception as e:
        logger.error(f"[LangGraph] Weather node error: {e}")
        errors = state.get("errors", [])
        errors.append(f"Weather agent error: {str(e)}")
        state["errors"] = errors
        add_step(state, agent="weather", status="failed", details=str(e))

    return state

def ocean_node(state: MarineAgentState) -> MarineAgentState:
    """Ocean Node: Evaluates SST, chlorophyll, and wave conditions."""
    logger.info("[LangGraph] Executing ocean_node")
    loc = state.get("location", {}).get("name", "Chennai")
    time_ctx = state.get("time_context", {}).get("name", "current")

    try:
        res = ocean_agent.run(location=loc, time_context=time_ctx)
        state["ocean_results"] = res
        add_step(state, agent="ocean", status="completed", details=f"Wave Height: {res.get('wave_height')}m | SST: {res.get('sst')}°C")
    except Exception as e:
        logger.error(f"[LangGraph] Ocean node error: {e}")
        errors = state.get("errors", [])
        errors.append(f"Ocean agent error: {str(e)}")
        state["errors"] = errors
        add_step(state, agent="ocean", status="failed", details=str(e))

    return state

def geospatial_node(state: MarineAgentState) -> MarineAgentState:
    """Geospatial Node: Resolves coordinates, distance, and geofenced zones."""
    logger.info("[LangGraph] Executing geospatial_node")
    loc = state.get("location", {}).get("name", "Chennai")

    try:
        res = geospatial_agent.run(location=loc)
        state["geospatial_results"] = res
        add_step(
            state,
            agent="geospatial",
            status="completed",
            details=f"Port: {res.get('nearest_port')} | Restricted: {res.get('restricted_zone')}"
        )
    except Exception as e:
        logger.error(f"[LangGraph] Geospatial node error: {e}")
        errors = state.get("errors", [])
        errors.append(f"Geospatial agent error: {str(e)}")
        state["errors"] = errors
        add_step(state, agent="geospatial", status="failed", details=str(e))

    return state

def satellite_node(state: MarineAgentState) -> MarineAgentState:
    """Satellite Node: Retrieves MOSDAC / ISRO satellite earth observation telemetry."""
    logger.info("[LANGGRAPH] Executing satellite_node")
    loc = state.get("location", {}).get("name", "Chennai")

    try:
        res = satellite_agent.run(location=loc, product="sst")
        state["satellite_results"] = res
        add_step(
            state,
            agent="satellite",
            status="completed",
            details=f"Provider: {res.get('provider')} | Status: {res.get('data_status')}"
        )
    except Exception as e:
        logger.error(f"[LANGGRAPH] Satellite node error: {e}")
        errors = state.get("errors", [])
        errors.append(f"Satellite agent error: {str(e)}")
        state["errors"] = errors
        add_step(state, agent="satellite", status="failed", details=str(e))

    return state

def marine_knowledge_node(state: MarineAgentState) -> MarineAgentState:
    """Marine Knowledge Node: Retrieves verified guidelines & citations from RAG."""
    logger.info("[LANGGRAPH] Executing marine_knowledge_node")
    query = state.get("user_query", "")

    try:
        res = marine_knowledge_agent.run(query)
        state["rag_results"] = [res]
        sources_cnt = len(res.get("sources", []))
        add_step(state, agent="marine_knowledge", status="completed", details=f"Retrieved {sources_cnt} citations")
    except Exception as e:
        logger.error(f"[LANGGRAPH] Marine knowledge node error: {e}")
        errors = state.get("errors", [])
        errors.append(f"RAG agent error: {str(e)}")
        state["errors"] = errors
        add_step(state, agent="marine_knowledge", status="failed", details=str(e))

    return state

def risk_node(state: MarineAgentState) -> MarineAgentState:
    """Risk Node: Synthesizes multi-factor evidence into a composite risk level."""
    logger.info("[LANGGRAPH] Executing risk_node")
    weather = state.get("weather_results")
    ocean = state.get("ocean_results")
    geospatial = state.get("geospatial_results")
    rag = state.get("rag_results", [{}])[0] if state.get("rag_results") else None

    try:
        res = risk_agent.run(weather=weather, ocean=ocean, geospatial=geospatial, rag=rag)
        state["risk_results"] = res
        add_step(state, agent="risk", status="completed", details=f"Risk: {res.get('risk_level')}")
    except Exception as e:
        logger.error(f"[LANGGRAPH] Risk node error: {e}")
        errors = state.get("errors", [])
        errors.append(f"Risk agent error: {str(e)}")
        state["errors"] = errors
        add_step(state, agent="risk", status="failed", details=str(e))

    return state

def route_node(state: MarineAgentState) -> MarineAgentState:
    """Route Node: Calculates deterministic safe marine route and safety scoring."""
    logger.info("[LangGraph] Executing route_node")
    orig_dict = state.get("origin") or state.get("location") or {"name": "Chennai"}
    dest_dict = state.get("destination") or {"name": "Pulicat"}
    orig_name = orig_dict.get("name") or "Chennai"
    dest_name = dest_dict.get("name") or "Pulicat"
    time_ctx = state.get("time_context", {}).get("name", "current")

    try:
        res = route_agent.run(
            origin=orig_name,
            destination=dest_name,
            departure_time=time_ctx,
            vessel_type="fishing_boat",
            vessel_speed_knots=10.0,
            route_preference="balanced"
        )
        state["route_results"] = res
        state["route_requested"] = True
        add_step(
            state,
            agent="route",
            status="completed",
            details=f"Track: {orig_name} -> {dest_name} | {res.get('distance_km')}km | Score: {res.get('safety_score')}/100 ({res.get('risk_level')})"
        )
    except Exception as e:
        logger.error(f"[LangGraph] Route node error: {e}")
        errors = state.get("errors", [])
        errors.append(f"Route agent error: {str(e)}")
        state["errors"] = errors
        add_step(state, agent="route", status="failed", details=str(e))

    return state

def response_node(state: MarineAgentState) -> MarineAgentState:
    """Response Synthesizer Node: Produces final structured answer and evidence in detected language."""
    logger.info("[LANGGRAPH] Executing response_node")
    query = state.get("user_query", "")
    intent = state.get("intent")
    loc = state.get("location")
    time_ctx = state.get("time_context")
    weather = state.get("weather_results")
    ocean = state.get("ocean_results")
    geospatial = state.get("geospatial_results")
    satellite = state.get("satellite_results")
    route = state.get("route_results")
    rag = state.get("rag_results", [{}])[0] if state.get("rag_results") else None
    risk = state.get("risk_results")
    errors = state.get("errors")
    history = state.get("chat_history", [])
    detected_lang = state.get("detected_language", "en")

    res = response_agent.synthesize(
        query=query,
        intent=intent,
        location=loc,
        time_context=time_ctx,
        weather=weather,
        ocean=ocean,
        geospatial=geospatial,
        satellite=satellite,
        route=route,
        rag=rag,
        risk=risk,
        errors=errors,
        chat_history=history,
        language=detected_lang
    )

    state["final_answer"] = res.get("answer")
    state["evidence"] = res.get("evidence", [])
    state["data_status"] = res.get("data_status", "demo")
    state["map_data"] = res.get("map_data")
    if route:
        state["route_results"] = res.get("route", route)
    add_step(state, agent="response", status="completed", details=f"Final response synthesized in [{detected_lang}]")

    return state

