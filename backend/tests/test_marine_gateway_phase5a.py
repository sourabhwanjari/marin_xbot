import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.marine_models import (
    DataStatus,
    Location,
    BoundingBox,
    TimeWindow,
    MarineEvidence,
    MarineDataPoint,
    MarineDataResponse,
    WeatherData,
    OceanData,
    PFZFeature,
    PFZData,
    SatelliteData,
    GeospatialData,
    HazardData,
)
from app.data_sources.common.models import ProviderCapability
from app.data_sources.imd.provider import IMDWeatherProvider
from app.data_sources.incois.ocean_provider import INCOISOceanProvider
from app.data_sources.incois.pfz_provider import INCOISPFZProvider
from app.data_sources.mosdac.satellite_provider import MOSDACSatelliteProvider
from app.data_sources.gis.provider import GISProvider
from app.marine_gateway.registry import provider_registry, ProviderRegistry
from app.marine_gateway.gateway import marine_gateway, MarineDataGateway


client = TestClient(app)


# ---------------------------------------------------------------------------
# 1. Marine Models Tests
# ---------------------------------------------------------------------------

def test_marine_models_location_and_timewindow():
    loc = Location(latitude=18.92, longitude=72.83, name="Mumbai Coast", region="Arabian Sea")
    assert loc.latitude == 18.92
    assert loc.longitude == 72.83
    assert loc.name == "Mumbai Coast"

    bbox = BoundingBox(min_lat=18.0, min_lon=72.0, max_lat=19.5, max_lon=73.5)
    assert bbox.min_lat == 18.0
    assert bbox.max_lon == 73.5

    now = datetime.now(timezone.utc)
    tw = TimeWindow(start_time=now, end_time=now, context="current")
    assert tw.context == "current"


def test_marine_models_evidence_and_data_point():
    evidence = MarineEvidence(
        source_provider="IMD",
        source_dataset="aws_hourly",
        retrieval_timestamp=datetime.now(timezone.utc),
        confidence_score=0.95,
        verification_status=DataStatus.VERIFIED,
        notes="Calibrated sensor reading"
    )
    assert evidence.provider == "IMD"
    assert evidence.status == DataStatus.VERIFIED

    point = MarineDataPoint(
        parameter="sea_surface_temperature",
        value=28.5,
        unit="°C",
        latitude=18.92,
        longitude=72.83,
        timestamp=datetime.now(timezone.utc),
        source="INCOIS",
        provider="INCOIS Ocean Gateway",
        dataset="insitu_buoy",
        quality="high"
    )
    assert point.parameter == "sea_surface_temperature"
    assert point.value == 28.5
    assert point.unit == "°C"


def test_marine_data_response_and_domain_models():
    loc = Location(latitude=18.92, longitude=72.83, name="Mumbai Port")
    weather = WeatherData(
        temperature=29.2,
        apparent_temperature=32.0,
        wind_speed_knots=12.5,
        wind_direction_deg=240.0,
        humidity=78.0,
        pressure_hpa=1012.0,
        visibility_km=10.0,
        precipitation_mm=0.0,
        weather_code=1,
        condition_text="Mainly Clear"
    )

    resp = MarineDataResponse(
        status=DataStatus.VERIFIED,
        provider="IMD Weather Provider",
        dataset="coastal_synoptic",
        location=loc,
        data=weather,
        retrieved_at=datetime.now(timezone.utc),
        quality="high"
    )

    assert resp.status == DataStatus.VERIFIED
    assert resp.temperature == 29.2
    assert resp.wind_speed == 12.5
    assert resp.humidity == 78.0
    payload = resp.to_dict()
    assert payload["status"] == "verified"
    assert payload["data"]["temperature"] == 29.2


# ---------------------------------------------------------------------------
# 2. Providers Behavior (Unconfigured vs Configured)
# ---------------------------------------------------------------------------

def test_imd_provider_unconfigured():
    provider = IMDWeatherProvider(api_key="", base_url="")
    assert not provider.is_configured

    loc = Location(latitude=18.92, longitude=72.83, name="Mumbai")
    tw = TimeWindow(context="current")

    resp = provider.fetch(loc, tw)
    assert resp.status == DataStatus.NOT_CONFIGURED
    assert resp.provider == "IMD"
    ev = resp.evidence[0] if isinstance(resp.evidence, list) and resp.evidence else resp.evidence
    assert ev.provider == "IMD" or ev.source == "IMD"


def test_incois_ocean_provider_unconfigured():
    provider = INCOISOceanProvider(api_key="", base_url="")
    assert not provider.is_configured

    loc = Location(latitude=18.92, longitude=72.83, name="Mumbai Coast")
    resp = provider.fetch(loc)
    assert resp.status == DataStatus.NOT_CONFIGURED
    assert resp.provider == "INCOIS-Ocean"


def test_incois_pfz_provider_fallback_reference():
    provider = INCOISPFZProvider(api_key="", base_url="")
    assert not provider.is_configured

    loc = Location(latitude=18.92, longitude=72.83, name="Mumbai Coastal Waters")
    resp = provider.fetch(loc)
    assert resp.status in [DataStatus.VERIFIED, DataStatus.SIMULATED, DataStatus.NOT_CONFIGURED]
    assert "INCOIS" in resp.provider
    assert isinstance(resp.data, (PFZData, dict))


def test_mosdac_satellite_provider_unconfigured():
    provider = MOSDACSatelliteProvider(api_key="", base_url="")
    assert not provider.is_configured

    loc = Location(latitude=18.92, longitude=72.83, name="Mumbai")
    resp = provider.fetch(loc)
    assert resp.status == DataStatus.NOT_CONFIGURED
    assert resp.provider == "MOSDAC"


def test_gis_spatial_provider():
    provider = GISProvider()
    assert provider.is_configured is False or provider.is_configured is True

    loc = Location(latitude=18.92, longitude=72.83, name="Mumbai")
    resp = provider.fetch(loc)
    assert resp.status in [DataStatus.VERIFIED, DataStatus.EXTERNAL]
    assert "Spatial-Engine" in resp.provider or "PostGIS" in resp.provider
    assert "distance_from_coast_km" in resp.data or hasattr(resp.data, "distance_from_coast_km")


# ---------------------------------------------------------------------------
# 3. ProviderRegistry Tests
# ---------------------------------------------------------------------------

def test_provider_registry_capabilities_and_sanitization():
    registry = ProviderRegistry()
    registry.initialize_default_providers()

    primary_weather = registry.get_primary_provider(ProviderCapability.WEATHER)
    assert primary_weather is not None
    assert primary_weather.provider_id == "imd"

    primary_ocean = registry.get_primary_provider(ProviderCapability.OCEAN)
    assert primary_ocean is not None
    assert primary_ocean.provider_id == "incois_ocean"

    status = registry.get_all_provider_statuses()
    assert "capabilities" in status
    assert "providers" in status

    # Verify no secret credentials are leaked in status
    status_str = str(status).lower()
    assert "api_key" not in status_str
    assert "secret" not in status_str
    assert "password" not in status_str


# ---------------------------------------------------------------------------
# 4. MarineDataGateway Unified Routing Tests
# ---------------------------------------------------------------------------

def test_gateway_weather_routing():
    loc = Location(latitude=18.92, longitude=72.83, name="Mumbai Offshore")
    resp = marine_gateway.get_weather(loc)
    assert isinstance(resp, MarineDataResponse)
    assert resp.status in [DataStatus.EXTERNAL, DataStatus.VERIFIED, DataStatus.NOT_CONFIGURED]
    assert resp.data is not None


def test_gateway_ocean_conditions():
    loc = Location(latitude=18.92, longitude=72.83, name="Mumbai Offshore")
    resp = marine_gateway.get_ocean_conditions(loc)
    assert isinstance(resp, MarineDataResponse)
    assert resp.data is not None
    # Wave height property should be accessible
    assert hasattr(resp, "wave_height")


def test_gateway_pfz_data():
    loc = Location(latitude=18.92, longitude=72.83, name="Mumbai Offshore")
    resp = marine_gateway.get_pfz(loc)
    assert isinstance(resp, MarineDataResponse)
    assert resp.data is not None


def test_gateway_satellite_data_unconfigured_handling():
    loc = Location(latitude=18.92, longitude=72.83, name="Mumbai Offshore")
    resp = marine_gateway.get_satellite_data(loc)
    assert isinstance(resp, MarineDataResponse)
    # MOSDAC is unconfigured by default, so it returns NOT_CONFIGURED
    assert resp.status == DataStatus.NOT_CONFIGURED
    assert resp.provider == "MOSDAC"


def test_gateway_geospatial_context():
    loc = Location(latitude=18.92, longitude=72.83, name="Mumbai Coast")
    resp = marine_gateway.get_geospatial_context(loc)
    assert isinstance(resp, MarineDataResponse)
    assert resp.status in [DataStatus.VERIFIED, DataStatus.EXTERNAL]


def test_gateway_hazards_aggregation():
    loc = Location(latitude=18.92, longitude=72.83, name="Mumbai Coast")
    resp = marine_gateway.get_hazards(loc)
    assert isinstance(resp, list) or isinstance(resp, MarineDataResponse)


def test_gateway_status_report():
    status = marine_gateway.get_gateway_status()
    assert status.status == "healthy"
    assert "capabilities" in status.metadata
    assert "providers" in status.metadata


# ---------------------------------------------------------------------------
# 5. REST API Endpoints Tests
# ---------------------------------------------------------------------------

def test_api_gateway_status():
    response = client.get("/api/marine/gateway/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "metadata" in data
    # Ensure no credentials in API output
    content_str = response.text.lower()
    assert "secret" not in content_str
    assert "token" not in content_str
    assert "password" not in content_str


def test_api_marine_weather():
    response = client.get("/api/marine/weather?lat=18.92&lon=72.83&location_name=Mumbai")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "provider" in data
    assert "location" in data
    assert "data" in data
    assert "evidence" in data


def test_api_marine_ocean():
    response = client.get("/api/marine/ocean?lat=18.92&lon=72.83&location_name=Mumbai")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "provider" in data
    assert "data" in data


def test_api_marine_pfz():
    response = client.get("/api/marine/pfz?lat=18.92&lon=72.83&location_name=Mumbai")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "data" in data


def test_api_marine_satellite():
    response = client.get("/api/marine/satellite?lat=18.92&lon=72.83&location_name=Mumbai")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "not_configured"
    assert data["provider"] == "MOSDAC"


def test_api_marine_geospatial():
    response = client.get("/api/marine/geospatial?lat=18.92&lon=72.83&location_name=Mumbai")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["verified", "external"]


def test_legacy_endpoints_backward_compatibility():
    # Phase 1-4 existing routes must continue to work without regression
    resp_cond = client.get("/api/marine/conditions?lat=18.92&lon=72.83")
    assert resp_cond.status_code == 200

    resp_pfz = client.get("/api/marine/fishing-zones?lat=18.92&lon=72.83")
    assert resp_pfz.status_code == 200

    resp_alerts = client.get("/api/marine/alerts?lat=18.92&lon=72.83")
    assert resp_alerts.status_code == 200
