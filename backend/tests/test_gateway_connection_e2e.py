import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.marine_models.base import Location, TimeWindow, MarineDataResponse, DataStatus, MarineEvidence
from app.marine_gateway.gateway import marine_gateway
from app.marine_gateway.registry import provider_registry, ProviderRegistry
from app.data_sources.common.base_provider import BaseMarineProvider
from app.data_sources.common.models import ProviderCapability
from app.graph.workflow import run_marine_workflow
from app.agents.weather_agent import weather_agent
from app.agents.ocean_agent import ocean_agent
from app.agents.satellite_agent import satellite_agent
from app.agents.geospatial_agent import geospatial_agent
from app.agents.response_agent import response_agent

client = TestClient(app)

# ---------------------------------------------------------------------------
# Controlled Test Providers (Step 12: MockWeatherProvider with SIMULATED status)
# ---------------------------------------------------------------------------

class MockWeatherProvider(BaseMarineProvider):
    def __init__(self):
        super().__init__(
            provider_name="MockWeatherProvider",
            capabilities=[ProviderCapability.WEATHER]
        )

    @property
    def is_enabled(self) -> bool:
        return True

    @property
    def is_configured(self) -> bool:
        return True

    def get_weather(self, location: Location, time_window: TimeWindow = None) -> MarineDataResponse:
        return MarineDataResponse(
            status=DataStatus.SIMULATED,
            provider="MockWeatherProvider",
            dataset="Simulated-Weather-Telemetry",
            parameter="surface_meteorology",
            latitude=location.latitude,
            longitude=location.longitude,
            retrieved_at="2026-09-24T00:00:00Z",
            quality="SIMULATED",
            location=location.to_dict(),
            data={
                "temperature": 31.5,
                "wind_speed": 14.2,
                "wind_direction": "SW",
                "rain_probability": 10,
                "weather_condition": "Clear Tropical Waters",
                "units": {"temperature": "°C", "wind_speed": "knots"}
            },
            evidence=[
                MarineEvidence(
                    source="Mock Controlled Meteorological Test Model",
                    provider="MockWeatherProvider",
                    dataset="Simulated-Weather-Telemetry",
                    retrieved_at="2026-09-24T00:00:00Z",
                    quality="SIMULATED",
                    status=DataStatus.SIMULATED
                )
            ]
        )


class MockUnconfiguredWeatherProvider(BaseMarineProvider):
    def __init__(self):
        super().__init__(
            provider_name="UnconfiguredIMD",
            capabilities=[ProviderCapability.WEATHER]
        )

    @property
    def is_enabled(self) -> bool:
        return False

    @property
    def is_configured(self) -> bool:
        return False

    def get_weather(self, location: Location, time_window: TimeWindow = None) -> MarineDataResponse:
        return MarineDataResponse(
            status=DataStatus.NOT_CONFIGURED,
            provider="UnconfiguredIMD",
            dataset="IMD-Live",
            latitude=location.latitude,
            longitude=location.longitude,
            retrieved_at="2026-09-24T00:00:00Z",
            quality="UNAVAILABLE",
            location=location.to_dict(),
            data={"message": "IMD credentials not configured"},
            evidence=[]
        )


# ---------------------------------------------------------------------------
# Acceptance Test 1: Weather -> Gateway Execution
# ---------------------------------------------------------------------------

def test_weather_agent_executes_gateway():
    """Verifies that WeatherAgent actually executes marine_gateway.get_weather()."""
    with patch.object(marine_gateway, "get_weather", wraps=marine_gateway.get_weather) as spy_weather:
        res = weather_agent.run(location="Mumbai", time_context="current")
        assert spy_weather.called
        assert res is not None
        assert "data_status" in res


def test_chatbot_weather_query_calls_gateway():
    """End-to-End Chat API -> LangGraph -> Router -> Weather Agent -> Gateway -> Response."""
    with patch.object(marine_gateway, "get_weather", wraps=marine_gateway.get_weather) as spy_weather:
        resp = client.post("/api/chat", json={"message": "What is the weather near Mumbai?"})
        assert resp.status_code == 200
        assert spy_weather.called
        # Check call arguments
        call_kwargs = spy_weather.call_args.kwargs
        assert "mumbai" in str(call_kwargs.get("location_name", "")).lower() or call_kwargs.get("latitude") is not None
        data = resp.json()
        assert data.get("message") is not None
        assert len(data.get("message")) > 0


# ---------------------------------------------------------------------------
# Acceptance Test 2: Ocean -> Gateway Execution
# ---------------------------------------------------------------------------

def test_ocean_agent_executes_gateway():
    """Verifies that OceanAgent actually executes marine_gateway.get_ocean_conditions()."""
    with patch.object(marine_gateway, "get_ocean_conditions", wraps=marine_gateway.get_ocean_conditions) as spy_ocean:
        res = ocean_agent.run(location="Mumbai", time_context="current")
        assert spy_ocean.called
        assert res is not None


def test_chatbot_ocean_query_calls_gateway():
    """End-to-End Chat API -> LangGraph -> Router -> Ocean Agent -> Gateway -> Response."""
    with patch.object(marine_gateway, "get_ocean_conditions", wraps=marine_gateway.get_ocean_conditions) as spy_ocean:
        resp = client.post("/api/chat", json={"message": "What are the ocean conditions near Mumbai?"})
        assert resp.status_code == 200
        assert spy_ocean.called


# ---------------------------------------------------------------------------
# Acceptance Test 3: PFZ -> Gateway Execution
# ---------------------------------------------------------------------------

def test_geospatial_pfz_agent_executes_gateway():
    """Verifies that GeospatialAgent actually executes marine_gateway.get_pfz()."""
    with patch.object(marine_gateway, "get_pfz", wraps=marine_gateway.get_pfz) as spy_pfz:
        res = geospatial_agent.run(location="Mumbai")
        assert spy_pfz.called
        assert res is not None


def test_chatbot_pfz_query_calls_gateway():
    """End-to-End Chat API -> LangGraph -> Router -> PFZ/Ocean/Geospatial Agent -> Gateway."""
    with patch.object(marine_gateway, "get_pfz", wraps=marine_gateway.get_pfz) as spy_pfz:
        resp = client.post("/api/chat", json={"message": "Is PFZ information available near Mumbai?"})
        assert resp.status_code == 200
        assert spy_pfz.called


# ---------------------------------------------------------------------------
# Acceptance Test 4: Satellite -> Gateway Execution
# ---------------------------------------------------------------------------

def test_satellite_agent_executes_gateway():
    """Verifies that SatelliteAgent actually executes marine_gateway.get_satellite_data()."""
    with patch.object(marine_gateway, "get_satellite_data", wraps=marine_gateway.get_satellite_data) as spy_sat:
        res = satellite_agent.run(location="Mumbai", product="sst")
        assert spy_sat.called
        assert res["provider"] == "MOSDAC"
        assert res["data_status"] == "not_configured"


def test_chatbot_satellite_query_calls_gateway_and_returns_unconfigured():
    """End-to-End Chat API -> LangGraph -> Router -> Satellite Agent -> Gateway -> Response."""
    with patch.object(marine_gateway, "get_satellite_data", wraps=marine_gateway.get_satellite_data) as spy_sat:
        resp = client.post("/api/chat", json={"message": "Is satellite marine data available near Mumbai?"})
        assert resp.status_code == 200
        assert spy_sat.called
        data = resp.json()
        # Must clearly inform user that MOSDAC is unconfigured without hallucinating fake data
        msg = data.get("message", "").lower()
        assert "not configured" in msg or "mosdac" in msg


# ---------------------------------------------------------------------------
# Acceptance Test 5: Gateway -> Provider Registry
# ---------------------------------------------------------------------------

def test_gateway_queries_provider_registry():
    """Verifies that the gateway consults ProviderRegistry to resolve provider adapters."""
    with patch.object(marine_gateway.registry, "get_provider", wraps=marine_gateway.registry.get_provider) as spy_reg:
        loc = Location(latitude=18.92, longitude=72.83, name="Mumbai")
        resp = marine_gateway.get_satellite_data(loc)
        assert spy_reg.called
        assert spy_reg.call_args[0][0] == ProviderCapability.SATELLITE
        assert resp.status == DataStatus.NOT_CONFIGURED


# ---------------------------------------------------------------------------
# Acceptance Test 6: Provider Registry -> Provider Execution
# ---------------------------------------------------------------------------

def test_provider_registry_executes_custom_mock_provider():
    """Verifies that registering a mock provider in ProviderRegistry routes calls to that provider."""
    mock_p = MockWeatherProvider()
    original_providers = provider_registry._providers.copy()
    try:
        provider_registry.register_provider(mock_p, capabilities=[ProviderCapability.WEATHER], is_primary=True)
        provider = provider_registry.get_primary_provider(ProviderCapability.WEATHER)
        assert provider.provider_name == "MockWeatherProvider"

        loc = Location(latitude=18.92, longitude=72.83, name="Mumbai")
        res = provider.get_weather(loc)
        assert res.status == DataStatus.SIMULATED
        assert res.data["temperature"] == 31.5
    finally:
        provider_registry.initialize_default_providers()


# ---------------------------------------------------------------------------
# Acceptance Test 7: Provider -> Normalized MarineDataResponse
# ---------------------------------------------------------------------------

def test_provider_returns_normalized_marine_data_response():
    """Verifies that all gateway responses follow the strict MarineDataResponse model with metadata."""
    loc = Location(latitude=18.92, longitude=72.83, name="Mumbai")
    resp = marine_gateway.get_weather(loc)
    assert isinstance(resp, MarineDataResponse)
    assert resp.provider is not None
    assert resp.status in [DataStatus.EXTERNAL, DataStatus.SIMULATED, DataStatus.NOT_CONFIGURED, DataStatus.VERIFIED]
    assert resp.location is not None
    assert resp.retrieved_at is not None


# ---------------------------------------------------------------------------
# Acceptance Test 8: Response -> Agent (No Fabrication Guardrail)
# ---------------------------------------------------------------------------

def test_agent_does_not_fabricate_defaults_when_unconfigured():
    """
    CRITICAL GUARDRAIL: When a provider returns NOT_CONFIGURED,
    the agent MUST NOT substitute hardcoded numbers (e.g. 29.5 C, 18 kts).
    """
    unconf_p = MockUnconfiguredWeatherProvider()
    unconf_resp = unconf_p.get_weather(Location(latitude=18.92, longitude=72.83, name="Mumbai"))

    with patch.object(marine_gateway, "get_weather", return_value=unconf_resp):
        res = weather_agent.run(location="Mumbai")
        assert res["data_status"] == "not_configured"
        # Values must NOT be defaulted to 29.5 or 18.0!
        assert res.get("temperature") is None
        assert res.get("wind_speed") is None


# ---------------------------------------------------------------------------
# Acceptance Test 9: Agent -> Final Chat Response
# ---------------------------------------------------------------------------

def test_final_response_synthesizer_uses_unconfigured_disclaimer():
    """Verifies that response synthesizer reports NOT_CONFIGURED transparently without hallucinating."""
    weather_payload = {
        "temperature": None,
        "wind_speed": None,
        "wind_direction": None,
        "rain_probability": None,
        "storm_risk": "unknown",
        "source": "IMD Weather Service",
        "data_status": "not_configured",
        "description": "Provider not configured in environment"
    }

    res = response_agent.synthesize(
        query="What is the weather near Mumbai?",
        intent="weather_inquiry",
        location={"name": "Mumbai"},
        weather=weather_payload
    )

    assert res["data_status"] == "not_configured"
    assert "not configured" in res["answer"].lower()
    # Ensure no fabricated 29.5 C appears in answer
    assert "29.5" not in res["answer"]


# ---------------------------------------------------------------------------
# Acceptance Test 10: Multi-Turn Conversation Preserves Location & Routes to Gateway
# ---------------------------------------------------------------------------

def test_multiturn_conversation_maintains_context_and_executes_gateway():
    """
    Verifies multi-turn sequence:
    Turn 1: 'What is the marine weather near Mumbai?'
    Turn 2: 'What about tomorrow morning?'
    Turn 3: 'What about the waves?'
    """
    # Turn 1
    resp1 = client.post("/api/chat", json={
        "message": "What is the marine weather near Mumbai?",
        "history": []
    })
    assert resp1.status_code == 200
    d1 = resp1.json()
    assert "mumbai" in str(d1.get("location", "")).lower()

    # Turn 2: 'What about tomorrow morning?' - should inherit Mumbai and route to weather gateway
    history1 = [
        {"role": "user", "content": "What is the marine weather near Mumbai?"},
        {"role": "assistant", "content": d1.get("message", "")}
    ]
    with patch.object(marine_gateway, "get_weather", wraps=marine_gateway.get_weather) as spy_weather_t2:
        resp2 = client.post("/api/chat", json={
            "message": "What about tomorrow morning?",
            "history": history1
        })
        assert resp2.status_code == 200
        assert spy_weather_t2.called
        d2 = resp2.json()
        assert "mumbai" in str(d2.get("location", "")).lower()

    # Turn 3: 'What about the waves?' - should route to ocean gateway for Mumbai
    history2 = history1 + [
        {"role": "user", "content": "What about tomorrow morning?"},
        {"role": "assistant", "content": d2.get("message", "")}
    ]
    with patch.object(marine_gateway, "get_ocean_conditions", wraps=marine_gateway.get_ocean_conditions) as spy_ocean_t3:
        resp3 = client.post("/api/chat", json={
            "message": "What about the waves?",
            "history": history2
        })
        assert resp3.status_code == 200
        assert spy_ocean_t3.called
        d3 = resp3.json()
        assert "mumbai" in str(d3.get("location", "")).lower()
