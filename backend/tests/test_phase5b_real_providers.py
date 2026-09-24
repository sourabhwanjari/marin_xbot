"""
Phase 5B Real Marine Data Provider Integration Test Suite
Validates:
1. ProviderStatus enum & BaseMarineProvider lifecycle/health check
2. IMD Weather Client & Provider (configured, unconfigured, timeout, error)
3. INCOIS Ocean Client & Provider (configured, unconfigured, timeout, error)
4. INCOIS PFZ Client & Provider (configured, reference fallback, disabled)
5. MOSDAC Satellite Client & Provider (configured, unconfigured)
6. GIS / PostGIS Provider (PostGIS check, deterministic spatial calculation)
7. Gateway Provider Status API (GET /api/marine/providers/status)
8. Gateway Caching with configurable TTLs
9. Freshness and Evidence Metadata integrity
10. End-to-End Chat & LangGraph execution with providers
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from app.main import app
from app.marine_models.base import Location, TimeWindow, DataStatus
from app.data_sources.common.provider_status import ProviderStatus
from app.data_sources.common.models import ProviderCapability
from app.data_sources.common.base_provider import BaseMarineProvider
from app.data_sources.common.exceptions import ProviderUnavailableError
from app.data_sources.imd.client import IMDClient
from app.data_sources.imd.provider import IMDWeatherProvider
from app.data_sources.imd.schemas import IMDWeatherObservation
from app.data_sources.incois.client import INCOISClient
from app.data_sources.incois.ocean_provider import INCOISOceanProvider
from app.data_sources.incois.pfz_provider import INCOISPFZProvider
from app.data_sources.incois.schemas import INCOISOceanObservation, INCOISPFZRecord, INCOISPFZResponse
from app.data_sources.mosdac.client import MOSDACClient
from app.data_sources.mosdac.satellite_provider import MOSDACSatelliteProvider
from app.data_sources.mosdac.schemas import MOSDACGranuleRecord, MOSDACGranuleResponse
from app.data_sources.gis.provider import GISProvider
from app.marine_gateway.gateway import marine_gateway
from app.marine_gateway.registry import provider_registry
from app.marine_gateway.cache import MarineCache


client = TestClient(app)


# =====================================================================
# 1. ProviderStatus Enum & BaseMarineProvider Tests
# =====================================================================

def test_provider_status_enum():
    """Verify ProviderStatus values, case-insensitive string matching, and serialization."""
    assert ProviderStatus.CONNECTED == "CONNECTED"
    assert ProviderStatus.CONNECTED == "connected"
    assert ProviderStatus.NOT_CONFIGURED == "not_configured"
    assert ProviderStatus.UNAVAILABLE == "UNAVAILABLE"
    assert ProviderStatus.ERROR == "ERROR"
    assert ProviderStatus.DEGRADED == "DEGRADED"
    assert ProviderStatus("CONNECTED") == ProviderStatus.CONNECTED


def test_base_provider_lifecycle():
    """Verify BaseMarineProvider properties, status evaluation, and health_check()."""
    class TestProvider(BaseMarineProvider):
        def __init__(self, configured=True, enabled=True, last_error=None):
            super().__init__(provider_name="Test-Provider", capabilities=[ProviderCapability.WEATHER])
            self._configured = configured
            self._enabled = enabled
            self.last_error = last_error

        @property
        def is_configured(self) -> bool:
            return self._configured

        @property
        def is_enabled(self) -> bool:
            return self._enabled

    # 1. Configured & enabled with no errors -> CONNECTED
    p1 = TestProvider(configured=True, enabled=True)
    assert p1.name == "Test-Provider"
    assert p1.provider_id == "test_provider"
    assert p1.status == ProviderStatus.CONNECTED
    health1 = p1.health_check()
    assert health1["status"] == "CONNECTED"
    assert health1["enabled"] is True
    assert health1["configured"] is True

    # 2. Unconfigured -> NOT_CONFIGURED
    p2 = TestProvider(configured=False, enabled=True)
    assert p2.status == ProviderStatus.NOT_CONFIGURED

    # 3. Disabled -> NOT_CONFIGURED
    p3 = TestProvider(configured=True, enabled=False)
    assert p3.status == ProviderStatus.NOT_CONFIGURED

    # 4. Error with 'timeout' or 'unavailable' -> UNAVAILABLE
    p4 = TestProvider(configured=True, enabled=True, last_error="HTTP Connection timeout after 6s")
    assert p4.status == ProviderStatus.UNAVAILABLE

    # 5. General error -> ERROR
    p5 = TestProvider(configured=True, enabled=True, last_error="500 Internal Server Error")
    assert p5.status == ProviderStatus.ERROR


# =====================================================================
# 2. IMD Weather Client & Provider Tests
# =====================================================================

def test_imd_provider_unconfigured_default():
    """When IMD is unconfigured, provider returns NOT_CONFIGURED without fake data."""
    provider = IMDWeatherProvider()
    if not provider.is_configured:
        assert provider.status == ProviderStatus.NOT_CONFIGURED
        loc = Location(latitude=18.922, longitude=72.834, name="Mumbai")
        resp = provider.get_weather(loc)
        assert resp.status == DataStatus.NOT_CONFIGURED
        assert resp.provider == "IMD"
        # Verify unconfigured or disabled notice
        msg = (resp.data.get("message", "") + " " + resp.data.get("disclaimer", "")).lower()
        assert any(term in msg for term in ["not configured", "disabled", "missing"])
        # Verify freshness fields exist
        assert resp.retrieved_at is not None
        assert resp.observed_at == "UNAVAILABLE"


def test_imd_client_and_provider_configured_mock():
    """When IMD is configured with valid credentials, client fetches and provider normalizes."""
    mock_obs = IMDWeatherObservation(
        station_id="MUM_COLABA",
        station_name="Mumbai Colaba Coastal Observatory",
        latitude=18.905,
        longitude=72.815,
        observation_time=datetime.now(timezone.utc).isoformat(),
        air_temperature_c=30.2,
        wind_speed_knots=13.0,
        wind_direction_deg=260.0,
        wind_direction_text="W",
        relative_humidity_percent=78.0,
        pressure_hpa=1010.5,
        visibility_km=9.0,
        weather_condition="Partly Cloudy"
    )

    with patch.object(IMDClient, "is_configured", True), \
         patch.object(IMDWeatherProvider, "is_enabled", True), \
         patch.object(IMDClient, "fetch_coastal_weather", return_value=mock_obs):
        provider = IMDWeatherProvider()
        assert provider.is_configured is True
        assert provider.status == ProviderStatus.CONNECTED

        loc = Location(latitude=18.905, longitude=72.815, name="Mumbai")
        resp = provider.get_weather(loc)

        assert resp.status in (DataStatus.EXTERNAL, DataStatus.VERIFIED)
        assert resp.provider == "IMD"
        assert resp.data["temperature"] == 30.2
        assert resp.data["wind_speed"] == 13.0
        assert resp.data["humidity"] == 78.0
        assert resp.quality in ("OPERATIONAL", "HIGH")

        # Freshness verification
        assert resp.observed_at is not None
        assert resp.retrieved_at is not None

        # Evidence verification
        assert len(resp.evidence) > 0
        ev = resp.evidence[0]
        assert ev.provider == "IMDWeatherProvider"
        assert ev.dataset == "IMD-Coastal-AWS"
        assert ev.metadata["station_name"] == "Mumbai Colaba Coastal Observatory"


def test_imd_provider_timeout_handling():
    """When IMD client times out, provider returns UNAVAILABLE without crashing."""
    with patch.object(IMDClient, "is_configured", True), \
         patch.object(IMDWeatherProvider, "is_enabled", True), \
         patch.object(IMDClient, "fetch_coastal_weather", side_effect=ProviderUnavailableError(provider_name="IMD", reason="Request timed out after 6s")):
        provider = IMDWeatherProvider()
        loc = Location(latitude=18.905, longitude=72.815, name="Mumbai")
        resp = provider.get_weather(loc)

        assert resp.status == DataStatus.UNAVAILABLE
        assert "unavailable" in (resp.data.get("disclaimer", "") + resp.data.get("error", "")).lower()
        assert provider.status == ProviderStatus.UNAVAILABLE


# =====================================================================
# 3. INCOIS Ocean Client & Provider Tests
# =====================================================================

def test_incois_ocean_provider_unconfigured_default():
    """When INCOIS Ocean is unconfigured, provider returns NOT_CONFIGURED."""
    provider = INCOISOceanProvider()
    if not provider.is_configured:
        assert provider.status == ProviderStatus.NOT_CONFIGURED
        loc = Location(latitude=13.0827, longitude=80.2707, name="Chennai")
        resp = provider.get_ocean_conditions(loc)
        assert resp.status == DataStatus.NOT_CONFIGURED
        assert resp.provider == "INCOIS-Ocean"
        assert resp.observed_at == "UNAVAILABLE"


def test_incois_ocean_provider_configured_mock():
    """When INCOIS Ocean is configured, fetches and normalizes wave, swell, SST, and currents."""
    mock_obs = INCOISOceanObservation(
        sector_name="Chennai Coastal Buoy",
        latitude=13.100,
        longitude=80.350,
        observation_time=datetime.now(timezone.utc).isoformat(),
        valid_until=datetime.now(timezone.utc).isoformat(),
        significant_wave_height_m=1.8,
        swell_wave_period_s=7.5,
        swell_wave_direction_deg=140.0,
        swell_direction_text="SE",
        sea_surface_temperature_c=29.1,
        current_speed_m_s=0.41,
        sea_state="Moderate",
        tide_status="Rising"
    )

    with patch.object(INCOISClient, "is_configured", True), \
         patch.object(INCOISOceanProvider, "is_enabled", True), \
         patch.object(INCOISClient, "fetch_ocean_conditions", return_value=mock_obs):
        provider = INCOISOceanProvider()
        assert provider.is_configured is True
        assert provider.status == ProviderStatus.CONNECTED

        loc = Location(latitude=13.100, longitude=80.350, name="Chennai Coastal Buoy")
        resp = provider.get_ocean_conditions(loc)

        assert resp.status in (DataStatus.EXTERNAL, DataStatus.VERIFIED)
        assert resp.provider == "INCOIS-Ocean"
        assert resp.data["wave_height"] == 1.8
        assert resp.data["swell_period"] == 7.5
        assert resp.data["sst"] == 29.1

        # Freshness verification
        assert resp.observed_at is not None
        assert resp.retrieved_at is not None
        assert resp.valid_until is not None

        # Evidence verification
        assert len(resp.evidence) > 0
        ev = resp.evidence[0]
        assert ev.provider == "INCOISOceanProvider"
        assert ev.dataset == "INCOIS-Wave-Hydrodynamic"


# =====================================================================
# 4. INCOIS PFZ Client & Provider Tests
# =====================================================================

def test_incois_pfz_provider_reference_fallback():
    """INCOIS PFZ operates with verified reference fallback when live API is unconfigured."""
    provider = INCOISPFZProvider()
    assert provider.is_enabled is True
    assert provider.status == ProviderStatus.CONNECTED
    # Reference mode provides operational fallback
    loc = Location(latitude=18.922, longitude=72.834, name="Mumbai")
    resp = provider.get_pfz(location=loc)

    assert resp.status == DataStatus.VERIFIED
    assert "INCOIS-PFZ" in resp.provider
    assert "zones" in resp.data
    assert len(resp.data["zones"]) > 0
    # First zone has realistic oceanographic metrics
    zone = resp.data["zones"][0]
    assert "zone_id" in zone
    assert "sst" in zone
    assert "chlorophyll" in zone
    assert "distance_km" in zone

    # Check evidence
    assert len(resp.evidence) > 0
    assert resp.evidence[0].dataset.startswith("INCOIS-PFZ")


def test_incois_pfz_provider_configured_mock():
    """When INCOIS PFZ live API returns data, it normalizes into PFZData."""
    mock_record = INCOISPFZRecord(
        zone_id="PFZ_LIVE_01",
        name="Versova Coastal Front",
        latitude=19.120,
        longitude=72.650,
        sector="Maharashtra",
        distance_km=22.5,
        direction="WNW",
        depth_meters=42,
        sst_c=28.4,
        chlorophyll="1.65 mg/m3",
        valid_from=datetime.now(timezone.utc).isoformat(),
        valid_until=datetime.now(timezone.utc).isoformat()
    )
    mock_resp = INCOISPFZResponse(
        advisory_id="ADV_2026_LIVE_01",
        total_active_zones=1,
        zones=[mock_record],
        nearest_zone=mock_record
    )

    with patch.object(INCOISClient, "is_configured", True), \
         patch.object(INCOISPFZProvider, "is_enabled", True), \
         patch.object(INCOISClient, "fetch_pfz_advisories", return_value=mock_resp):
        provider = INCOISPFZProvider()
        loc = Location(latitude=19.120, longitude=72.650, name="Versova")
        resp = provider.get_pfz(location=loc)

        assert resp.status in (DataStatus.EXTERNAL, DataStatus.VERIFIED)
        assert resp.data["total_active_zones"] == 1
        assert resp.data["zones"][0]["zone_id"] == "PFZ_LIVE_01"
        assert resp.data["zones"][0]["sst"] == 28.4


# =====================================================================
# 5. MOSDAC Satellite Client & Provider Tests
# =====================================================================

def test_mosdac_satellite_provider_unconfigured_default():
    """When MOSDAC is unconfigured, returns NOT_CONFIGURED without fabricating granules."""
    provider = MOSDACSatelliteProvider()
    if not provider.is_configured:
        assert provider.status == ProviderStatus.NOT_CONFIGURED
        loc = Location(latitude=18.922, longitude=72.834, name="Mumbai")
        resp = provider.get_satellite_data(location=loc, product="sst")
        assert resp.status == DataStatus.NOT_CONFIGURED
        assert resp.provider == "MOSDAC"
        msg = (resp.data.get("message", "") + " " + resp.data.get("disclaimer", "")).lower()
        assert any(term in msg for term in ["not configured", "missing", "credentials"])
        assert resp.observed_at == "UNAVAILABLE"


def test_mosdac_satellite_provider_configured_mock():
    """When MOSDAC is configured, returns normalized granules, freshness, and evidence."""
    mock_granule = MOSDACGranuleRecord(
        granule_id="O3_SST_20260924_G01",
        dataset_id="OS3_SST_L3",
        satellite_mission="ISRO Oceansat-3",
        sensor="OCM-3 / SSTM",
        product_name="Sea Surface Temperature (SST)",
        pass_timestamp=datetime.now(timezone.utc).isoformat(),
        spatial_resolution_km=1.0,
        cloud_cover_percent=12.5,
        sst_c=28.7,
        download_url="https://mosdac.gov.in/catalog/download/O3_SST_20260924_G01"
    )
    mock_resp = MOSDACGranuleResponse(
        dataset_id="OS3_SST_L3",
        total_granules=1,
        granules=[mock_granule],
        latest_granule=mock_granule
    )

    with patch.object(MOSDACClient, "is_configured", True), \
         patch.object(MOSDACSatelliteProvider, "is_enabled", True), \
         patch.object(MOSDACClient, "fetch_granule_catalog", return_value=mock_resp):
        provider = MOSDACSatelliteProvider()
        assert provider.is_configured is True
        assert provider.status == ProviderStatus.CONNECTED

        loc = Location(latitude=18.922, longitude=72.834, name="Arabian Sea")
        resp = provider.get_satellite_data(location=loc, product="sst")

        assert resp.status in (DataStatus.EXTERNAL, DataStatus.VERIFIED)
        assert resp.provider == "MOSDAC"
        assert resp.data["granule_id"] == "O3_SST_20260924_G01"
        assert resp.data["satellite_mission"] == "ISRO Oceansat-3"
        assert resp.data["cloud_cover_percent"] == 12.5

        # Freshness verification
        assert resp.observed_at is not None
        assert resp.retrieved_at is not None

        # Evidence verification
        assert len(resp.evidence) > 0
        ev = resp.evidence[0]
        assert ev.metadata["granule_id"] == "O3_SST_20260924_G01"


# =====================================================================
# 6. GIS / PostGIS Provider Tests
# =====================================================================

def test_gis_provider_deterministic_computation():
    """Verify GIS provider computes spatial constraints deterministically without LLM guessing."""
    provider = GISProvider()
    assert provider.is_enabled is True
    assert provider.status == ProviderStatus.CONNECTED

    loc = Location(latitude=18.940, longitude=72.860, name="Mumbai Port Approach")
    resp = provider.get_geospatial_data(location=loc)

    assert resp.status == DataStatus.VERIFIED
    assert resp.provider in ("GIS-Spatial-Engine", "GeoJSON-Spatial-Engine", "PostGIS-Engine")
    assert "nearest_port" in resp.data
    # Should resolve Mumbai Port deterministically based on coordinates
    nearest_port = resp.data["nearest_port"]
    assert "Mumbai" in nearest_port["name"]
    assert nearest_port["distance_km"] < 15.0  # Within ~15km of Mumbai port coordinates

    # Verify maritime constraints are computed deterministically
    assert "restricted_zone" in resp.data
    assert "distance_from_coast_km" in resp.data

    # Freshness
    assert resp.retrieved_at is not None
    assert resp.observed_at is not None

    # Evidence
    assert len(resp.evidence) > 0
    assert "Mumbai" in resp.evidence[0].metadata.get("nearest_port", "")


def test_gis_postgis_connection_check():
    """Verify check_postgis_connection returns boolean without unhandled exception."""
    provider = GISProvider()
    result = provider.check_postgis_connection()
    assert isinstance(result, bool)


# =====================================================================
# 7. Gateway Provider Status API (GET /api/marine/providers/status)
# =====================================================================

def test_get_providers_status_endpoint():
    """Verify GET /api/marine/providers/status endpoint contract and structure."""
    response = client.get("/api/marine/providers/status")
    assert response.status_code == 200
    data = response.json()

    # Must contain all 5 target provider keys
    for provider_key in ["imd", "incois_ocean", "incois_pfz", "mosdac", "postgis"]:
        assert provider_key in data, f"Missing key: {provider_key}"
        assert "status" in data[provider_key]
        assert data[provider_key]["status"] in [
            "CONNECTED", "NOT_CONFIGURED", "UNAVAILABLE", "ERROR", "DEGRADED"
        ]

    # Check known default states
    assert data["postgis"]["status"] == "CONNECTED"
    assert data["incois_pfz"]["status"] in ["CONNECTED", "NOT_CONFIGURED"]


# =====================================================================
# 8. Marine Gateway Caching & TTLs
# =====================================================================

def test_marine_gateway_cache_ttls():
    """Verify configurable cache TTLs for weather, ocean, pfz, and satellite."""
    cache = MarineCache()
    assert cache.weather_ttl > 0
    assert cache.ocean_ttl > 0
    assert cache.pfz_ttl > 0
    assert cache.satellite_ttl > 0

    # Test cache set and get
    loc = Location(latitude=18.922, longitude=72.834, name="Mumbai")
    dummy_resp = marine_gateway.get_weather(location=loc)
    cache.set("weather:18.922:72.834", dummy_resp, category="weather")

    cached_item = cache.get("weather:18.922:72.834", category="weather")
    assert cached_item is not None
    assert cached_item.provider == dummy_resp.provider


# =====================================================================
# 9. Freshness and Evidence Metadata Validation
# =====================================================================

def test_freshness_metadata_integrity():
    """Verify all gateway responses contain proper ISO timestamps and validity windows."""
    loc = Location(latitude=18.922, longitude=72.834, name="Mumbai")

    # 1. Weather
    weather_resp = marine_gateway.get_weather(location=loc)
    assert weather_resp.retrieved_at is not None
    assert weather_resp.observed_at is not None

    # 2. Ocean
    ocean_resp = marine_gateway.get_ocean_conditions(location=loc)
    assert ocean_resp.retrieved_at is not None
    assert ocean_resp.observed_at is not None

    # 3. PFZ
    pfz_resp = marine_gateway.get_pfz(location=loc)
    assert pfz_resp.retrieved_at is not None
    assert pfz_resp.observed_at is not None

    # 4. Satellite
    sat_resp = marine_gateway.get_satellite_data(location=loc, product_name="sst")
    assert sat_resp.retrieved_at is not None
    assert sat_resp.observed_at is not None


# =====================================================================
# 10. Multi-Agent & Chat Integration with Gateway
# =====================================================================

def test_chatbot_invokes_gateway_weather():
    """Verify chat route processes weather query through LangGraph and Gateway."""
    req = {
        "message": "What is the marine weather and wind speed near Mumbai Port?",
        "session_id": "test_phase5b_weather"
    }
    response = client.post("/api/chat/", json=req)
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert len(data["message"]) > 0


def test_chatbot_invokes_gateway_satellite():
    """Verify chat route handles satellite request gracefully via Gateway."""
    req = {
        "message": "Show me the latest Oceansat satellite sea surface temperature data for Mumbai",
        "session_id": "test_phase5b_sat"
    }
    response = client.post("/api/chat/", json=req)
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    # Response should acknowledge satellite data or unconfigured disclaimer without fabricating fake numbers
    resp_text = data["message"].lower()
    assert any(term in resp_text for term in ["satellite", "oceansat", "mosdac", "sst", "surface temperature"])
