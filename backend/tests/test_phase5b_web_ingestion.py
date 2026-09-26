import os
import json
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.data_ingestion.common.scraper_status import (
    ScraperStatus, FreshnessStatus, calculate_freshness
)
from app.data_ingestion.parsers.geo_parser import GeoSpatialParser
from app.data_ingestion.parsers.html_parser import HTMLTableParser
from app.data_ingestion.parsers.json_parser import JSONFeedParser
from app.data_ingestion.storage.repository import ingestion_repository
from app.data_ingestion.normalization.marine_normalizer import MarineNormalizer
from app.data_ingestion.common.scraper_registry import scraper_registry
from app.data_ingestion.imd.scraper import IMDCoastalScraper
from app.data_ingestion.incois.ocean_scraper import INCOISOceanScraper
from app.data_ingestion.incois.pfz_scraper import INCOISPFZScraper
from app.data_ingestion.mosdac.satellite_scraper import MOSDACSatelliteScraper
from app.marine_gateway.gateway import marine_gateway
from app.marine_models.base import Location, TimeWindow, DataStatus
from app.agents.response_agent import response_agent

client = TestClient(app)

# --- 1. Status and Freshness Tests ---

def test_freshness_status_calculation():
    now = datetime.now(timezone.utc)
    fresh_time = (now - timedelta(hours=1)).isoformat()
    recent_time = (now - timedelta(hours=6)).isoformat()
    stale_time = (now - timedelta(hours=20)).isoformat()
    expired_time = (now - timedelta(hours=30)).isoformat()

    f_status, desc = calculate_freshness(fresh_time, category="weather")
    assert f_status == FreshnessStatus.FRESH
    assert "Fresh" in desc

    r_status, _ = calculate_freshness(recent_time, category="weather")
    assert r_status == FreshnessStatus.RECENT

    s_status, _ = calculate_freshness(stale_time, category="weather")
    assert s_status == FreshnessStatus.STALE

    e_status, _ = calculate_freshness(expired_time, category="weather")
    assert e_status == FreshnessStatus.EXPIRED

    u_status, _ = calculate_freshness(None, category="weather")
    assert u_status == FreshnessStatus.UNKNOWN


# --- 2. Parser Unit Tests ---

def test_geospatial_parser():
    # Haversine distance
    dist = GeoSpatialParser.haversine_distance_km(18.922, 72.834, 18.950, 72.850)
    assert 2.0 < dist < 6.0

    # Coordinate string parsing
    lat, lon = GeoSpatialParser.parse_coordinate_string("18.92N, 72.83E")
    assert abs(lat - 18.92) < 0.01
    assert abs(lon - 72.83) < 0.01

    # GeoJSON creation
    pt = GeoSpatialParser.create_geojson_point(18.922, 72.834)
    assert pt["type"] == "Point"
    assert pt["coordinates"] == [72.834, 18.922]

    # Validation
    valid, err = GeoSpatialParser.validate_coordinates(18.922, 72.834)
    assert valid is True
    assert err is None

    invalid, err_msg = GeoSpatialParser.validate_coordinates(95.0, 72.834)
    assert invalid is False
    assert "Latitude" in err_msg


def test_html_table_parser():
    mock_html = """
    <html>
      <body>
        <table id="coastal-bulletin">
          <thead>
            <tr><th>Station</th><th>Latitude</th><th>Longitude</th><th>Wind Speed (kts)</th><th>Temp (C)</th></tr>
          </thead>
          <tbody>
            <tr><td>Mumbai High</td><td>18.92</td><td>72.83</td><td>18.5</td><td>29.2</td></tr>
            <tr><td>Chennai Port</td><td>13.08</td><td>80.27</td><td>14.0</td><td>30.1</td></tr>
          </tbody>
        </table>
      </body>
    </html>
    """
    tables = HTMLTableParser.parse_all_tables(mock_html)
    assert len(tables) == 1
    assert len(tables[0]) == 2
    assert tables[0][0]["station"] == "Mumbai High"
    assert tables[0][0]["temp_c"] == "29.2"
    assert tables[0][1]["station"] == "Chennai Port"



def test_json_feed_parser():
    mock_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "zone_id": "PFZ-MUM-01",
                    "name": "Mumbai Offshore Bank",
                    "sst": 28.2,
                    "chlorophyll": "High"
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [72.50, 18.90]
                }
            }
        ]
    }
    features = JSONFeedParser.extract_geojson_features(mock_geojson)
    assert len(features) == 1
    assert features[0]["properties"]["zone_id"] == "PFZ-MUM-01"
    assert features[0]["geometry"]["coordinates"] == [72.50, 18.90]


# --- 3. Storage and Repository Tests ---

def test_ingestion_repository_persistence():
    now_iso = datetime.now(timezone.utc).isoformat()
    valid_until = (datetime.now(timezone.utc) + timedelta(hours=6)).isoformat()

    # Weather observation insertion
    weather_recs = [
        {
            "source": "India Meteorological Department",
            "dataset": "IMD-Coastal-AWS-Observations",
            "location_name": "Mumbai Harbour AWS",
            "latitude": 18.922,
            "longitude": 72.834,
            "temperature_c": 29.5,
            "wind_speed_knots": 14.5,
            "wind_direction_text": "WSW",
            "rain_probability_pct": 20,
            "weather_condition": "Fair coastal skies",
            "observed_at": now_iso,
            "valid_until": valid_until,
            "retrieved_at": now_iso,
            "quality": "OPERATIONAL",
            "source_url": "https://mausam.imd.gov.in"
        }
    ]
    saved_w = ingestion_repository.save_weather_observations(weather_recs)
    assert saved_w == 1

    # Weather retrieval
    retrieved_w = ingestion_repository.get_latest_weather(18.922, 72.834, max_distance_km=20.0)
    assert retrieved_w is not None
    assert retrieved_w.location_name == "Mumbai Harbour AWS"
    assert retrieved_w.temperature_c == 29.5
    assert retrieved_w.wind_speed_knots == 14.5

    # Ocean observation insertion
    ocean_recs = [
        {
            "source": "INCOIS Hyderabad",
            "dataset": "INCOIS-Ocean-State-Forecast",
            "sector_name": "Maharashtra Coast",
            "latitude": 18.920,
            "longitude": 72.830,
            "significant_wave_height_m": 1.4,
            "wave_period_s": 8.0,
            "sea_surface_temp_c": 28.6,
            "sea_state": "Moderate",
            "observed_at": now_iso,
            "valid_until": valid_until,
            "retrieved_at": now_iso,
            "quality": "OPERATIONAL",
            "source_url": "https://incois.gov.in/portal/osf/osf.jsp"
        }
    ]
    saved_o = ingestion_repository.save_ocean_observations(ocean_recs)
    assert saved_o == 1

    # Ocean retrieval
    retrieved_o = ingestion_repository.get_latest_ocean(18.920, 72.830, max_distance_km=25.0)
    assert retrieved_o is not None
    assert retrieved_o.sector_name == "Maharashtra Coast"
    assert retrieved_o.significant_wave_height_m == 1.4

    # PFZ advisory insertion
    pfz_recs = [
        {
            "source": "INCOIS PFZ Mission",
            "dataset": "INCOIS-PFZ-Advisory",
            "zone_id": "PFZ-MAH-901",
            "zone_name": "Offshore Ratnagiri Ridge",
            "sector": "Maharashtra South",
            "latitude": 17.00,
            "longitude": 73.15,
            "distance_km": 18.5,
            "direction": "WSW",
            "depth_meters": 45,
            "sst_c": 28.1,
            "chlorophyll": "High",
            "suitability": "Favorable",
            "dominant_species": ["Mackerel", "Sardine", "Tuna"],
            "observed_at": now_iso,
            "valid_until": valid_until,
            "retrieved_at": now_iso,
            "quality": "HIGH",
            "source_url": "https://incois.gov.in/portal/pfz/pfz.jsp"
        }
    ]
    saved_p = ingestion_repository.save_pfz_advisories(pfz_recs)
    assert saved_p == 1

    # PFZ retrieval
    active_pfz = ingestion_repository.get_active_pfz(17.00, 73.15, radius_km=50.0)
    assert len(active_pfz) >= 1
    assert active_pfz[0].zone_id == "PFZ-MAH-901"

    # Ingestion Run Audit logging
    run_log = ingestion_repository.record_run(
        scraper_name="IMDCoastalScraper",
        source_name="India Meteorological Department",
        status="SUCCESS",
        records_ingested=1,
        duration_ms=45.2,
        source_url="https://mausam.imd.gov.in"
    )
    assert run_log.id is not None
    assert run_log.status == "SUCCESS"

    # Database health stats
    db_stat = ingestion_repository.get_database_status()
    assert db_stat["status"] == "CONNECTED"
    assert db_stat["counts"]["weather_records"] >= 1
    assert db_stat["counts"]["ocean_records"] >= 1


# --- 4. Scrapers & Normalization Tests ---

def test_imd_scraper_execution_and_normalization():
    scraper = IMDCoastalScraper()
    assert scraper.source_name == "India Meteorological Department (IMD)"
    assert scraper.source_url.startswith("https://mausam.imd.gov.in")

    result = scraper.run_ingestion()
    assert result["status"] in ("SUCCESS", "UNAVAILABLE")
    if result["status"] == "SUCCESS":
        assert result["records_ingested"] > 0


def test_incois_ocean_scraper_execution():
    scraper = INCOISOceanScraper()
    assert "INCOIS" in scraper.source_name
    result = scraper.run_ingestion()
    assert result["status"] in ("SUCCESS", "UNAVAILABLE")


def test_incois_pfz_scraper_execution():
    scraper = INCOISPFZScraper()
    assert "PFZ" in scraper.source_name
    result = scraper.run_ingestion()
    assert result["status"] in ("SUCCESS", "UNAVAILABLE")


def test_mosdac_scraper_unconfigured_policy():
    """MOSDAC requires authentication; strictly returns NOT_CONFIGURED when unconfigured."""
    scraper = MOSDACSatelliteScraper()
    result = scraper.run_ingestion()
    assert result["status"] == ScraperStatus.NOT_CONFIGURED.value
    msg = (result.get("message") or result.get("error") or "").lower()
    assert "disabled" in msg or "not configured" in msg or "credentials" in msg




# --- 5. Marine Data Gateway Integration Tests ---

def test_gateway_uses_ingested_weather_data():
    loc = Location(latitude=18.922, longitude=72.834, name="Mumbai")
    resp = marine_gateway.get_weather(location=loc)

    assert resp is not None
    assert resp.status in (DataStatus.EXTERNAL, DataStatus.VERIFIED)
    assert resp.temperature is not None
    assert resp.wind_speed is not None
    assert len(resp.evidence) > 0


def test_gateway_uses_ingested_ocean_data():
    loc = Location(latitude=18.920, longitude=72.830, name="Mumbai")
    resp = marine_gateway.get_ocean_conditions(location=loc)

    assert resp is not None
    assert resp.status in (DataStatus.EXTERNAL, DataStatus.VERIFIED)
    assert resp.wave_height is not None
    assert len(resp.evidence) > 0


def test_gateway_uses_ingested_pfz_data():
    loc = Location(latitude=17.00, longitude=73.15, name="Ratnagiri")
    resp = marine_gateway.get_pfz(location=loc)

    assert resp is not None
    assert hasattr(resp, "data")
    assert resp.status in (DataStatus.EXTERNAL, DataStatus.VERIFIED)


def test_gateway_status_reports_ingestion_metadata():
    stat = marine_gateway.get_gateway_status()
    assert stat.status == "healthy"
    assert stat.gateway_version == "Phase-5B"
    assert "ingestion_database" in stat.metadata
    assert stat.metadata["ingestion_database"]["status"] == "CONNECTED"


# --- 6. API Route Verification Tests ---

def test_api_ingestion_status():
    resp = client.get("/api/marine/ingestion/status")
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "healthy"
    assert "scheduler" in data
    assert "scrapers" in data
    assert "database" in data

    # Verify all scrapers are present in report
    scrapers = data["scrapers"]
    assert "imd" in scrapers
    assert "incois_ocean" in scrapers
    assert "incois_pfz" in scrapers
    assert "mosdac" in scrapers
    assert scrapers["mosdac"]["status"] == "NOT_CONFIGURED"


def test_api_ingestion_manual_trigger():
    resp = client.post("/api/marine/ingestion/run/imd")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert data["source"] == "imd"
    assert "result" in data


def test_api_marine_advisories():
    resp = client.get("/api/marine/advisories")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


# --- 7. Conversational Chatbot Provenance & Freshness Tests ---

def test_chatbot_responds_to_provenance_and_freshness_queries():
    query = "Which source provided this marine data and when was it retrieved? Is it fresh?"
    resp = response_agent.synthesize(
        query=query,
        location={"name": "Mumbai Harbour AWS", "latitude": 18.922, "longitude": 72.834},
        weather={"source": "IMD Coastal AWS", "temperature": 29.5, "wind_speed": 14.5, "data_status": "external"},
        ocean={"source": "INCOIS Ocean State Forecast", "wave_height": 1.4, "sst": 28.6, "data_status": "external"}
    )

    answer = resp["answer"]
    assert "Provenance & Freshness Report" in answer
    assert "Official Web Data Sources" in answer
    assert "IMD" in answer
    assert "INCOIS" in answer
    assert "MOSDAC" in answer
    assert "Fresh" in answer
    assert len(resp["evidence"]) > 0
    assert resp["data_status"] == "verified"
