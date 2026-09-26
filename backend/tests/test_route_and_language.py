import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.language.detector import language_detector
from app.language.language_service import language_service
from app.route.route_models import RouteRequest, RoutePoint
from app.route.route_engine import route_engine
from app.route.route_service import route_service
from app.route.route_scoring import route_scorer
from app.graph.workflow import run_marine_workflow
from app.models.agent_models import QueryIntent
from app.agents.planner_agent import planner_agent

client = TestClient(app)

# =====================================================================
# 1. LANGUAGE DETECTION TESTS (English, Hindi, Marathi, Multi-turn)
# =====================================================================

def test_language_detection_english():
    res = language_detector.detect("Recommend a safe route from Chennai to Pulicat")
    assert res.language == "en"
    assert res.language_name == "English"
    assert res.confidence >= 0.85

def test_language_detection_hindi():
    res = language_detector.detect("चेन्नई से पुलिकट सुरक्षित मार्ग बताओ")
    assert res.language == "hi"
    assert res.language_name == "Hindi"
    assert res.script == "Devanagari"
    assert res.confidence >= 0.85

def test_language_detection_marathi():
    res = language_detector.detect("मुंबई ते गोवा सुरक्षित मार्ग दाखवा")
    assert res.language == "mr"
    assert res.language_name == "Marathi"
    assert res.script == "Devanagari"
    assert res.confidence >= 0.85

def test_language_detection_marathi_unique_letters():
    # 'ळ' is an exclusive Marathi letter in Devanagari
    res = language_detector.detect("समुद्रातील लाटांची माहिती द्या आणि वेळ सांगा")
    assert res.language == "mr"
    assert res.confidence >= 0.95

def test_language_service_multiturn_persistence():
    # First turn in Marathi
    res1 = language_service.detect_language("नमस्कार, आज हवामान कसे आहे?")
    assert res1.language == "mr"

    # Follow-up short neutral query inherits Marathi
    history = [
        {"role": "user", "content": "नमस्कार, आज हवामान कसे आहे?"},
        {"role": "assistant", "content": "नमस्कार कॅप्टन, आज हवामान शांत आहे."}
    ]
    res2 = language_service.detect_language("Mumbai", history=history)
    assert res2.language == "mr"

def test_prompt_language_directives():
    hi_dir = language_service.get_prompt_language_instruction("hi")
    assert "Hindi" in hi_dir or "हिन्दी" in hi_dir
    mr_dir = language_service.get_prompt_language_instruction("mr")
    assert "Marathi" in mr_dir or "मराठी" in mr_dir

# =====================================================================
# 2. DETERMINISTIC ROUTE ENGINE & SCORING TESTS
# =====================================================================

def test_route_planner_endpoint_extraction():
    # English
    plan_en = planner_agent.plan("Recommend a safe route from Chennai to Pulicat")
    assert plan_en.intent == QueryIntent.SAFE_ROUTE
    assert plan_en.origin == "Chennai"
    assert plan_en.destination == "Pulicat"
    assert "route" in plan_en.required_agents

    # Hindi
    plan_hi = planner_agent.plan("चेन्नई से पुलिकट सुरक्षित मार्ग बताओ")
    assert plan_hi.intent == QueryIntent.SAFE_ROUTE
    assert plan_hi.origin == "Chennai"
    assert plan_hi.destination == "Pulicat"

    # Marathi
    plan_mr = planner_agent.plan("मुंबई ते गोवा सुरक्षित मार्ग दाखवा")
    assert plan_mr.intent == QueryIntent.SAFE_ROUTE
    assert plan_mr.origin == "Mumbai"
    assert plan_mr.destination == "Goa"

def test_route_service_calculation():
    req = RouteRequest(
        origin=RoutePoint(latitude=13.125, longitude=80.298, name="Chennai"),
        destination=RoutePoint(latitude=13.420, longitude=80.320, name="Pulicat"),
        vessel_speed_knots=10.0,
        route_preference="balanced"
    )
    resp = route_service.recommend_route(req)

    assert resp.status == "SUCCESS"
    assert resp.distance_km > 0.0
    assert resp.estimated_duration_hours > 0.0
    assert len(resp.waypoints) >= 2
    assert resp.safety_score >= 0 and resp.safety_score <= 100
    assert resp.risk_level in ["LOW", "MODERATE", "HIGH"]
    assert resp.route_geometry is not None
    assert resp.route_geometry.get("type") == "LineString"
    assert len(resp.evidence) >= 1

def test_route_scorer_weights():
    cost = route_scorer.calculate_cost(
        distance_km=50.0,
        avg_wind_speed_knots=15.0,
        max_wave_height_m=1.2,
        geofence_violations=0,
        hazard_intersections=0
    )
    assert cost > 0.0
    # Violation penalty drastically increases cost
    violated_cost = route_scorer.calculate_cost(
        distance_km=50.0,
        avg_wind_speed_knots=15.0,
        max_wave_height_m=1.2,
        geofence_violations=1,
        hazard_intersections=0
    )
    assert violated_cost > cost

# =====================================================================
# 3. FASTAPI ROUTE & CHAT INTEGRATION TESTS
# =====================================================================

def test_api_route_recommend_endpoint():
    payload = {
        "origin": {"latitude": 13.125, "longitude": 80.298, "name": "Chennai"},
        "destination": {"latitude": 13.420, "longitude": 80.320, "name": "Pulicat"},
        "vessel_speed_knots": 10.0,
        "route_preference": "balanced"
    }
    response = client.post("/api/marine/route/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["distance_km"] > 0
    assert "waypoints" in data
    assert len(data["waypoints"]) >= 2
    assert "route_geometry" in data

def test_api_chat_route_flow_english():
    response = client.post("/api/chat", json={"message": "Recommend a safe route from Chennai to Pulicat"})
    assert response.status_code == 200
    data = response.json()
    assert data["message"] is not None
    assert data["route"] is not None
    assert data["route"]["distance_km"] > 0
    assert data["detected_language"] == "en"

def test_api_chat_route_flow_hindi():
    response = client.post("/api/chat", json={"message": "चेन्नई से पुलिकट सुरक्षित मार्ग बताओ"})
    assert response.status_code == 200
    data = response.json()
    assert data["route"] is not None
    assert data["detected_language"] == "hi"

def test_api_chat_route_flow_marathi():
    response = client.post("/api/chat", json={"message": "मुंबई ते गोवा सुरक्षित मार्ग दाखवा"})
    assert response.status_code == 200
    data = response.json()
    assert data["route"] is not None
    assert data["detected_language"] == "mr"
