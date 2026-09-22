import pytest
from app.data_sources.weather.service import weather_service
from app.data_sources.ocean.service import ocean_service
from app.data_sources.pfz.service import pfz_service
from app.data_sources.satellite.service import satellite_service
from app.data_sources.geospatial.service import geospatial_service
from app.marine_gateway.gateway import marine_gateway
from app.marine_gateway.health import check_all_data_sources
from app.marine_gateway.models import (
    NormalizedWeather,
    NormalizedOcean,
    NormalizedPFZ,
    NormalizedGeospatial,
)
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_weather_service_returns_normalized_data():
    weather = weather_service.get_weather(18.922, 72.834, "Mumbai", "current")
    assert isinstance(weather, NormalizedWeather)
    assert weather.temperature is not None
    assert weather.wind_speed is not None
    assert weather.wind_direction is not None
    assert weather.rain_probability is not None
    assert weather.provider is not None
    assert weather.status in ["external", "demo"]
    assert weather.timestamp is not None
    assert weather.units["wind_speed"] == "knots"

def test_ocean_service_returns_normalized_data():
    ocean = ocean_service.get_ocean_conditions(18.922, 72.834, "Mumbai", "current")
    assert isinstance(ocean, NormalizedOcean)
    assert ocean.wave_height is not None
    assert ocean.sea_surface_temperature is not None
    assert ocean.ocean_condition is not None
    assert ocean.status in ["external", "demo"]
    assert ocean.timestamp is not None
    assert ocean.units["wave_height"] == "m"

def test_pfz_service_produces_valid_geographic_objects():
    zones = pfz_service.get_pfz_zones()
    assert len(zones) >= 4
    first_zone = zones[0]
    assert isinstance(first_zone, NormalizedPFZ)
    assert -90.0 <= first_zone.latitude <= 90.0
    assert -180.0 <= first_zone.longitude <= 180.0
    assert first_zone.suitability in ["Favorable", "Moderate", "Caution"]
    assert first_zone.data_status in ["verified", "verified_sample", "demo"]

    # Test nearest PFZ calculation
    nearest = pfz_service.get_nearest_pfz(18.922, 72.834)
    assert nearest is not None
    assert "Mumbai" in nearest.name or "Alibaug" in nearest.name
    assert nearest.distance_km > 0

    # Test GeoJSON generation
    geojson = pfz_service.get_pfz_geojson("Mumbai")
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) > 0
    assert geojson["features"][0]["geometry"]["type"] == "Point"

def test_geospatial_service_spatial_queries():
    # 1. Port detection
    port = geospatial_service.find_nearest_port(18.922, 72.834)
    assert "Mumbai" in port.name

    # 2. Restricted zone detection inside Mumbai Naval Fairway (18.920, 72.830)
    restr = geospatial_service.check_restricted_zone(18.920, 72.830)
    assert restr.is_restricted is True
    assert "Mumbai Naval" in (restr.zone_name or "")

    # 3. Protected area check near Pulicat (13.450, 80.320)
    prot = geospatial_service.check_protected_area(13.450, 80.320)
    assert prot.is_protected is True
    assert "Pulicat" in (prot.area_name or "")

    # 4. Normalized geospatial summary
    summary = geospatial_service.get_geospatial_summary("Mumbai", 18.922, 72.834)
    assert isinstance(summary, NormalizedGeospatial)
    assert summary.restricted_zone is True
    assert summary.status == "verified"

def test_satellite_service_not_configured_guardrail():
    # Without MOSDAC credentials configured, it must strictly return 'not_configured'
    res = satellite_service.get_satellite_product("sst")
    assert res.status == "not_configured"
    assert "not configured" in res.message.lower()
    assert res.data_status == "not_configured"

def test_gateway_caching_and_routing():
    # Fetch through gateway
    w1 = marine_gateway.get_weather(18.922, 72.834, "Mumbai", "current")
    w2 = marine_gateway.get_weather(18.922, 72.834, "Mumbai", "current")
    # Verify cached return
    assert w1.timestamp == w2.timestamp
    assert w1.temperature == w2.temperature

def test_data_sources_rest_endpoints():
    res = client.get("/api/data-sources/status")
    assert res.status_code == 200
    data = res.json()
    assert "weather" in data
    assert "ocean" in data
    assert "pfz" in data
    assert "satellite" in data
    assert data["satellite"]["status"] == "not_configured"

    # Test PFZ endpoint
    pfz_res = client.get("/api/data-sources/pfz?location=Mumbai")
    assert pfz_res.status_code == 200
    pfz_data = pfz_res.json()
    assert pfz_data["type"] == "FeatureCollection"
    assert len(pfz_data["features"]) > 0

    # Test Geospatial layers endpoint
    geo_res = client.get("/api/data-sources/geospatial")
    assert geo_res.status_code == 200
    geo_data = geo_res.json()
    assert "ports" in geo_data
    assert "restricted_zones" in geo_data
    assert "protected_areas" in geo_data
    assert "hazard_zones" in geo_data
