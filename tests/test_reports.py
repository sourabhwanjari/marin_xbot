"""
Unit tests for Report Exporter (CSV, JSON, GeoJSON, PDF)
"""

import pytest
import os
import tempfile
from pathlib import Path

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from reports.exporter import SurveyReportExporter


@pytest.fixture
def mock_survey_data():
    mission = {
        "id": 101,
        "name": "Arabian_Sea_Test_Mission",
        "survey_area": "Bombay High Offshore Zone",
        "operator": "Survey Hydrographer",
        "vessel_auv": "AUV Bluefin-21",
        "sonar_device": "Edgetech 4200",
        "crs": "EPSG:4326 (WGS84)"
    }
    detections = [
        {
            "id": 1,
            "class_name": "ghost_net",
            "label": "Ghost Net",
            "ai_confidence": 0.94,
            "ai_confidence_percent": 94,
            "anomaly_score": 0.91,
            "anomaly_score_percent": 91,
            "verification_status": "VERIFIED",
            "latitude": 18.9224,
            "longitude": 72.8351,
            "depth": 32.4,
            "estimated_width": 3.4,
            "estimated_height": 2.1,
            "location_quality": "EXACT / HIGH QUALITY",
            "horizontal_uncertainty_m": 2.4,
            "model_version": "1.0.0",
            "created_at": "2026-09-14T10:00:00Z"
        },
        {
            "id": 2,
            "class_name": "shipwreck",
            "label": "Shipwreck",
            "ai_confidence": 0.88,
            "ai_confidence_percent": 88,
            "anomaly_score": 0.85,
            "anomaly_score_percent": 85,
            "verification_status": "NEEDS_REVIEW",
            "latitude": 18.9230,
            "longitude": 72.8360,
            "depth": 34.1,
            "estimated_width": 11.5,
            "estimated_height": 4.2,
            "location_quality": "ESTIMATED",
            "horizontal_uncertainty_m": 4.1,
            "model_version": "1.0.0",
            "created_at": "2026-09-14T10:05:00Z"
        }
    ]
    return mission, detections


def test_export_csv(mock_survey_data, tmp_path):
    mission, dets = mock_survey_data
    exporter = SurveyReportExporter(output_dir=tmp_path)
    csv_file = exporter.export_csv(mission, dets, "test_report.csv")
    assert csv_file.exists()
    assert csv_file.stat().st_size > 0
    content = csv_file.read_text(encoding="utf-8")
    assert "Ghost Net" in content
    assert "Shipwreck" in content


def test_export_json(mock_survey_data, tmp_path):
    mission, dets = mock_survey_data
    exporter = SurveyReportExporter(output_dir=tmp_path)
    json_file = exporter.export_json(mission, dets, "test_report.json")
    assert json_file.exists()
    content = json_file.read_text(encoding="utf-8")
    assert "SONAR-AI" in content
    assert "Arabian_Sea_Test_Mission" in content


def test_export_geojson(mock_survey_data, tmp_path):
    mission, dets = mock_survey_data
    exporter = SurveyReportExporter(output_dir=tmp_path)
    geojson_file = exporter.export_geojson(mission, dets, "test_report.geojson")
    assert geojson_file.exists()
    content = geojson_file.read_text(encoding="utf-8")
    assert "FeatureCollection" in content
    assert "Point" in content


def test_export_pdf(mock_survey_data, tmp_path):
    mission, dets = mock_survey_data
    exporter = SurveyReportExporter(output_dir=tmp_path)
    pdf_file = exporter.export_pdf(mission, dets, "test_report.pdf")
    assert pdf_file.exists()
    assert pdf_file.stat().st_size > 1000  # Non-trivial PDF size
