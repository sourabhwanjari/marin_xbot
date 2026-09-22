import pytest
from app.agents.planner_agent import planner_agent
from app.agents.weather_agent import weather_agent
from app.agents.ocean_agent import ocean_agent
from app.agents.geospatial_agent import geospatial_agent
from app.agents.marine_knowledge_agent import marine_knowledge_agent
from app.agents.risk_agent import risk_agent
from app.agents.response_agent import response_agent
from app.models.agent_models import QueryIntent

# 1. Test Planner Agent
def test_planner_agent_intents():
    # Fishing safety
    p1 = planner_agent.plan("Is it safe to go fishing tomorrow morning near Mumbai?")
    assert p1.intent == QueryIntent.FISHING_SAFETY
    assert p1.location == "Mumbai"
    assert "tomorrow morning" in p1.time
    assert "weather" in p1.required_agents
    assert "ocean" in p1.required_agents
    assert "risk" in p1.required_agents
    assert len(p1.tasks) >= 3

    # Weather inquiry
    p2 = planner_agent.plan("What is the weather forecast today?")
    assert p2.intent == QueryIntent.WEATHER_INQUIRY
    assert "weather" in p2.required_agents

    # Ocean conditions
    p3 = planner_agent.plan("What are the wave conditions and sea state?")
    assert p3.intent == QueryIntent.OCEAN_CONDITIONS
    assert "ocean" in p3.required_agents

    # PFZ discovery
    p4 = planner_agent.plan("Find areas with high fish productivity near the coast.")
    assert p4.intent == QueryIntent.PFZ_DISCOVERY
    assert "ocean" in p4.required_agents
    assert "geospatial" in p4.required_agents

    # Restricted zones
    p5 = planner_agent.plan("Are there any restricted naval channels near Chennai?")
    assert p5.intent == QueryIntent.RESTRICTED_ZONES
    assert p5.location == "Chennai"
    assert "geospatial" in p5.required_agents

    # Out of scope
    p6 = planner_agent.plan("Tell me a funny joke.")
    assert p6.intent == QueryIntent.OUT_OF_SCOPE
    assert len(p6.required_agents) == 0

# 2. Test Weather Agent
def test_weather_agent():
    w = weather_agent.run(location="Mumbai", time_context="tomorrow morning")
    assert "temperature" in w
    assert "wind_speed" in w
    assert "wind_direction" in w
    assert "storm_risk" in w
    assert w["data_status"] in ["external", "demo"]

# 3. Test Ocean Agent
def test_ocean_agent():
    o = ocean_agent.run(location="Chennai", time_context="current")
    assert "sst" in o
    assert "wave_height" in o
    assert "ocean_condition" in o
    assert o["data_status"] in ["external", "demo"]

# 4. Test Geospatial Agent
def test_geospatial_agent():
    g = geospatial_agent.run(location="Chennai")
    assert "coordinates" in g
    assert "nearest_port" in g
    assert "restricted_zone" in g
    assert g["data_status"] in ["verified", "demo"]

# 5. Test Marine Knowledge Agent
def test_marine_knowledge_agent():
    mk = marine_knowledge_agent.run("high wave safety guidelines")
    assert "answer" in mk
    assert "sources" in mk
    assert mk["is_rag"] is True

# 6. Test Risk Agent
def test_risk_agent_reasoning():
    # Severe conditions -> HIGH risk
    r_high = risk_agent.run(
        weather={"wind_speed": 26.0, "storm_risk": "high"},
        ocean={"wave_height": 3.2, "ocean_condition": "rough"},
        geospatial={"restricted_zone": True, "nearest_hazard": "Naval Fairway"}
    )
    assert r_high["risk_level"] == "HIGH"
    assert len(r_high["risk_factors"]) >= 2

    # Calm conditions -> LOW risk
    r_low = risk_agent.run(
        weather={"wind_speed": 10.0, "storm_risk": "low"},
        ocean={"wave_height": 1.1, "ocean_condition": "calm"},
        geospatial={"restricted_zone": False}
    )
    assert r_low["risk_level"] == "LOW"

# 7. Test Response Agent
def test_response_agent():
    # Out of scope response
    resp_out = response_agent.synthesize(
        query="Tell me a joke",
        intent=QueryIntent.OUT_OF_SCOPE.value
    )
    assert "MARINEX AI" in resp_out["answer"]
    assert resp_out["risk_level"] is None

    # Safety response
    resp_safety = response_agent.synthesize(
        query="Is it safe to fish tomorrow morning near Mumbai?",
        intent=QueryIntent.FISHING_SAFETY.value,
        location={"name": "Mumbai"},
        time_context={"name": "tomorrow morning"},
        weather={"temperature": 30, "wind_speed": 16, "wind_direction": "SW", "rain_probability": 20, "description": "Moderate breeze"},
        ocean={"wave_height": 1.4, "ocean_condition": "moderate", "sst": 28.1, "swell_period": 8.5},
        geospatial={"nearest_port": "Mumbai Major Port", "distance_from_coast_km": 5, "restricted_zone": False},
        risk={"risk_level": "MEDIUM", "risk_factors": ["Moderate swell waves of 1.4m"]}
    )
    assert "Mumbai" in resp_safety["answer"]
    assert resp_safety["risk_level"] == "MEDIUM"
    assert len(resp_safety["evidence"]) >= 2
