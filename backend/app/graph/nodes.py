import logging
from typing import Dict, Any
from app.graph.state import MarineAgentState
from app.agents.planner_agent import planner_agent
from app.agents.weather_agent import weather_agent
from app.agents.ocean_agent import ocean_agent
from app.agents.geospatial_agent import geospatial_agent
from app.agents.marine_knowledge_agent import marine_knowledge_agent
from app.agents.risk_agent import risk_agent
from app.agents.response_agent import response_agent

logger = logging.getLogger("marinex.graph.nodes")

def add_step(state: MarineAgentState, agent: str, status: str, details: str = None):
    steps = state.get("execution_steps", [])
    steps.append({"agent": agent, "status": status, "details": details})
    state["execution_steps"] = steps

def planner_node(state: MarineAgentState) -> MarineAgentState:
    """Planner Node: Decomposes query and selects required specialized agents."""
    logger.info("[LangGraph] Executing planner_node")
    query = state.get("user_query", "")
    default_loc = state.get("location", {}).get("name") if state.get("location") else None

    plan = planner_agent.plan(query, default_location=default_loc)

    state["intent"] = plan.intent.value
    state["tasks"] = plan.tasks
    state["selected_agents"] = plan.required_agents
    state["location"] = {"name": plan.location} if plan.location else {"name": "Chennai"}
    state["time_context"] = {"name": plan.time} if plan.time else {"name": "current"}

    add_step(
        state,
        agent="planner",
        status="completed",
        details=f"Intent: {plan.intent.value} | Agents: {', '.join(plan.required_agents) if plan.required_agents else 'None'}"
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

def marine_knowledge_node(state: MarineAgentState) -> MarineAgentState:
    """Marine Knowledge Node: Retrieves verified guidelines & citations from RAG."""
    logger.info("[LangGraph] Executing marine_knowledge_node")
    query = state.get("user_query", "")

    try:
        res = marine_knowledge_agent.run(query)
        state["rag_results"] = [res]
        sources_cnt = len(res.get("sources", []))
        add_step(state, agent="marine_knowledge", status="completed", details=f"Retrieved {sources_cnt} citations")
    except Exception as e:
        logger.error(f"[LangGraph] Marine knowledge node error: {e}")
        errors = state.get("errors", [])
        errors.append(f"RAG agent error: {str(e)}")
        state["errors"] = errors
        add_step(state, agent="marine_knowledge", status="failed", details=str(e))

    return state

def risk_node(state: MarineAgentState) -> MarineAgentState:
    """Risk Node: Synthesizes multi-factor evidence into a composite risk level."""
    logger.info("[LangGraph] Executing risk_node")
    weather = state.get("weather_results")
    ocean = state.get("ocean_results")
    geospatial = state.get("geospatial_results")
    rag = state.get("rag_results", [{}])[0] if state.get("rag_results") else None

    try:
        res = risk_agent.run(weather=weather, ocean=ocean, geospatial=geospatial, rag=rag)
        state["risk_results"] = res
        add_step(state, agent="risk", status="completed", details=f"Risk: {res.get('risk_level')}")
    except Exception as e:
        logger.error(f"[LangGraph] Risk node error: {e}")
        errors = state.get("errors", [])
        errors.append(f"Risk agent error: {str(e)}")
        state["errors"] = errors
        add_step(state, agent="risk", status="failed", details=str(e))

    return state

def response_node(state: MarineAgentState) -> MarineAgentState:
    """Response Synthesizer Node: Produces final structured answer and evidence."""
    logger.info("[LangGraph] Executing response_node")
    query = state.get("user_query", "")
    intent = state.get("intent")
    loc = state.get("location")
    time_ctx = state.get("time_context")
    weather = state.get("weather_results")
    ocean = state.get("ocean_results")
    geospatial = state.get("geospatial_results")
    rag = state.get("rag_results", [{}])[0] if state.get("rag_results") else None
    risk = state.get("risk_results")
    errors = state.get("errors")

    res = response_agent.synthesize(
        query=query,
        intent=intent,
        location=loc,
        time_context=time_ctx,
        weather=weather,
        ocean=ocean,
        geospatial=geospatial,
        rag=rag,
        risk=risk,
        errors=errors
    )

    state["final_answer"] = res.get("answer")
    state["evidence"] = res.get("evidence", [])
    state["data_status"] = res.get("data_status", "demo")
    state["map_data"] = res.get("map_data")
    add_step(state, agent="response", status="completed", details="Final response synthesized")

    return state
