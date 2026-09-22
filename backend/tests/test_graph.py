import pytest
from app.graph.workflow import run_marine_workflow
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Test 1: Weather query
def test_workflow_weather():
    result = run_marine_workflow("What is the weather today?")
    assert result["intent"] == "weather_inquiry"
    assert result["weather"] is not None
    assert result["data_status"] in ["external", "demo", "verified"]
    # Verify execution steps contain planner and weather
    agents_executed = [step["agent"] for step in result["execution_steps"]]
    assert "planner" in agents_executed
    assert "weather" in agents_executed
    assert "response" in agents_executed

# Test 2: Ocean query
def test_workflow_ocean():
    result = run_marine_workflow("What are the ocean conditions?")
    assert result["intent"] == "ocean_conditions"
    assert result["ocean"] is not None
    agents_executed = [step["agent"] for step in result["execution_steps"]]
    assert "planner" in agents_executed
    assert "ocean" in agents_executed

# Test 3: PFZ discovery
def test_workflow_pfz():
    result = run_marine_workflow("Find a fishing area with favorable ocean conditions.")
    assert result["intent"] == "pfz_discovery"
    assert result["ocean"] is not None
    agents_executed = [step["agent"] for step in result["execution_steps"]]
    assert "ocean" in agents_executed
    assert "geospatial" in agents_executed

# Test 4: Main Demo Scenario (Complex Fishing Safety near Mumbai)
def test_workflow_demo_fishing_safety_mumbai():
    result = run_marine_workflow("Is it safe to go fishing tomorrow morning near Mumbai?")
    assert result["intent"] == "fishing_safety"
    assert result["location"] == "Mumbai"
    assert "tomorrow morning" in result["time_context"]
    assert result["risk_level"] in ["LOW", "MEDIUM", "HIGH"]
    assert result["weather"] is not None
    assert result["ocean"] is not None
    assert result["geospatial"] is not None
    assert result["risk"] is not None
    assert len(result["evidence"]) >= 3

    agents_executed = [step["agent"] for step in result["execution_steps"]]
    assert "planner" in agents_executed
    assert "weather" in agents_executed
    assert "ocean" in agents_executed
    assert "geospatial" in agents_executed
    assert "risk" in agents_executed
    assert "response" in agents_executed

# Test 5: Restricted marine zones
def test_workflow_restricted_zones():
    result = run_marine_workflow("Find restricted marine zones near Chennai.")
    assert result["intent"] == "restricted_zones"
    assert result["geospatial"] is not None
    agents_executed = [step["agent"] for step in result["execution_steps"]]
    assert "geospatial" in agents_executed

# Test 6: Out of scope
def test_workflow_out_of_scope():
    result = run_marine_workflow("Tell me a joke.")
    assert result["intent"] == "out_of_scope"
    assert "MARINEX AI" in result["answer"]
    agents_executed = [step["agent"] for step in result["execution_steps"]]
    assert "weather" not in agents_executed
    assert "ocean" not in agents_executed

# Test 7: API Endpoints
def test_agent_api_endpoints():
    # 1. Agent Status
    r_status = client.get("/api/agent/status")
    assert r_status.status_code == 200
    data_status = r_status.json()
    assert data_status["status"] == "active"
    assert len(data_status["registered_agents"]) == 7

    # 2. Agent Chat
    r_chat = client.post("/api/agent/chat", json={
        "message": "Is it safe to go fishing tomorrow morning near Mumbai?"
    })
    assert r_chat.status_code == 200
    data_chat = r_chat.json()
    assert data_chat["intent"] == "fishing_safety"
    assert data_chat["risk_level"] in ["LOW", "MEDIUM", "HIGH"]
    assert len(data_chat["evidence"]) > 0
    assert len(data_chat["execution_steps"]) > 0

    # 3. Existing Chat endpoint (preserved & enhanced)
    r_old = client.post("/api/chat", json={
        "message": "What is the weather today?"
    })
    assert r_old.status_code == 200
    data_old = r_old.json()
    assert "langgraph-multi-agent" in data_old["source"]
