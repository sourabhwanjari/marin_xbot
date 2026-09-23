import pytest
from app.agents.planner_agent import planner_agent
from app.models.agent_models import QueryIntent
from app.graph.workflow import run_marine_workflow

def test_planner_location_inheritance_from_history():
    """Verify planner inherits coastal location from earlier conversation turns."""
    history = [
        {"role": "user", "content": "What are the ocean conditions near Mumbai?"},
        {"role": "assistant", "content": "Wave height is 1.8m near Mumbai."}
    ]
    # User does NOT repeat 'Mumbai'
    plan = planner_agent.plan("What is the wind speed?", chat_history=history)
    assert plan.location == "Mumbai"
    assert plan.intent == QueryIntent.WEATHER_INQUIRY

def test_planner_temporal_followup():
    """Verify follow-up inquiries like 'what about tomorrow' retain intent and location."""
    history = [
        {"role": "user", "content": "Is it safe to go fishing near Goa?"},
        {"role": "assistant", "content": "Medium risk identified for Goa."}
    ]
    plan = planner_agent.plan("What about tomorrow?", chat_history=history)
    assert plan.location == "Goa"
    assert plan.time == "tomorrow"
    assert plan.intent == QueryIntent.FISHING_SAFETY

def test_planner_craft_type_followup():
    """Verify small craft inquiries are classified as fishing safety with inherited location."""
    history = [
        {"role": "user", "content": "What are the ocean conditions near Kochi?"},
        {"role": "assistant", "content": "Kochi wave conditions are moderate."}
    ]
    plan = planner_agent.plan("Can small artisanal boats go out?", chat_history=history)
    assert plan.location == "Kochi"
    assert plan.intent == QueryIntent.FISHING_SAFETY

def test_multiturn_workflow_execution():
    """Test full multi-turn execution maintaining context across sequential turns."""
    history = []

    # Turn 1: Specific query specifying Mumbai
    turn1_res = run_marine_workflow("What are the ocean conditions near Mumbai?", chat_history=history)
    assert turn1_res["location"] == "Mumbai"
    history.append({"role": "user", "content": "What are the ocean conditions near Mumbai?"})
    history.append({"role": "assistant", "content": turn1_res["answer"]})

    # Turn 2: Follow-up asking about wind without repeating location
    turn2_res = run_marine_workflow("What is the wind speed?", chat_history=history)
    assert turn2_res["location"] == "Mumbai"
    assert "wind" in turn2_res["evidence"][0].lower() or turn2_res["intent"] == "weather_inquiry"
    history.append({"role": "user", "content": "What is the wind speed?"})
    history.append({"role": "assistant", "content": turn2_res["answer"]})

    # Turn 3: Follow-up asking about tomorrow
    turn3_res = run_marine_workflow("Is it safe to go fishing tomorrow?", chat_history=history)
    assert turn3_res["location"] == "Mumbai"
    assert turn3_res["time_context"] == "tomorrow"
    history.append({"role": "user", "content": "Is it safe to go fishing tomorrow?"})
    history.append({"role": "assistant", "content": turn3_res["answer"]})

    # Turn 4: Follow-up on craft type
    turn4_res = run_marine_workflow("What about for small artisanal boats?", chat_history=history)
    assert turn4_res["location"] == "Mumbai"
    assert turn4_res["risk_level"] in ["LOW", "MEDIUM", "HIGH"]
