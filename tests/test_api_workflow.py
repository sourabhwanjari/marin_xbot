"""
End-to-End API Integration Tests for complete survey workflow
"""

import pytest
import os
import time
from fastapi.testclient import TestClient

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from main import app
from database import init_db

client = TestClient(app)


def setup_module():
    init_db()


def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "detector_mode" in data


def test_complete_survey_workflow():
    # 1. Create Mission
    mission_payload = {
        "name": "E2E_Test_Survey_Track_01",
        "description": "Autonomous integration verification survey",
        "survey_date": "2026-09-14",
        "operator": "Senior Survey Engineer",
        "vessel_auv": "AUV Surveyor-IV",
        "sonar_device": "Edgetech 4200 SSS",
        "survey_area": "Arabian Sea North Track",
        "crs": "EPSG:4326 (WGS84)"
    }
    m_res = client.post("/api/missions", json=mission_payload)
    assert m_res.status_code == 200
    mission = m_res.json()
    mission_id = mission["id"]
    assert mission["name"] == mission_payload["name"]

    # 2. Ingest Sample Sonar & Telemetry
    imp_res = client.post(f"/api/import/{mission_id}/load_sample?sample_index=1")
    assert imp_res.status_code == 200
    assert "image_file" in imp_res.json()

    # 3. Start Processing Job
    proc_payload = {
        "mission_id": mission_id,
        "confidence_threshold": 0.50,
        "enable_denoise": True,
        "enable_clahe": True
    }
    p_res = client.post("/api/processing/start", json=proc_payload)
    assert p_res.status_code == 200
    job = p_res.json()
    job_id = job["job_id"]

    # 4. Poll until job completes (typically takes 1-3 seconds locally)
    max_wait = 20
    poll_start = time.time()
    job_completed = False

    while time.time() - poll_start < max_wait:
        status_res = client.get(f"/api/processing/{job_id}")
        assert status_res.status_code == 200
        job_status = status_res.json()
        if job_status["status"] == "COMPLETED":
            job_completed = True
            break
        elif job_status["status"] in ["FAILED", "CANCELLED"]:
            pytest.fail(f"Processing failed: {job_status.get('error_message')}")
        time.sleep(0.5)

    assert job_completed is True, "Processing job timed out."

    # 5. Fetch Detections
    det_res = client.get(f"/api/detections?mission_id={mission_id}")
    assert det_res.status_code == 200
    dets = det_res.json()
    assert len(dets) > 0, "Expected at least one detection candidate."
    target_1 = dets[0]
    target_id = target_1["id"]

    # 6. Engineer Review: Confirm target as VERIFIED
    rev_confirm = client.post(
        f"/api/detections/{target_id}/review",
        json={"action": "confirm", "engineer": "Surveyor Alice", "comments": "Confirmed synthetic net structure"}
    )
    assert rev_confirm.status_code == 200
    assert rev_confirm.json()["detection"]["verification_status"] == "VERIFIED"

    # 7. Engineer Review: Reclassify target
    rev_reclass = client.post(
        f"/api/detections/{target_id}/review",
        json={"action": "reclassify", "new_class": "pipe", "new_label": "Pipe", "engineer": "Surveyor Bob"}
    )
    assert rev_reclass.status_code == 200
    assert rev_reclass.json()["detection"]["class_name"] == "pipe"
    assert rev_reclass.json()["detection"]["verification_status"] == "MODIFIED"

    # 8. Add Manual Target (Missed anomaly)
    manual_payload = {
        "mission_id": mission_id,
        "class_name": "cylinder",
        "bbox_x1": 200,
        "bbox_y1": 250,
        "bbox_x2": 260,
        "bbox_y2": 320,
        "engineer": "Lead Hydrographer",
        "notes": "Target discovered during acoustic shadow cross-check"
    }
    man_res = client.post("/api/detections/manual", json=manual_payload)
    assert man_res.status_code == 200
    manual_det = man_res.json()
    assert manual_det["is_manual"] is True
    assert manual_det["verification_status"] == "VERIFIED"

    # 9. Verify GIS Map Data
    map_res = client.get(f"/api/maps/{mission_id}")
    assert map_res.status_code == 200
    map_data = map_res.json()
    assert len(map_data["markers"]) >= len(dets)
    assert "trajectory" in map_data

    # 10. Generate & Verify Reports
    rep_summary = client.get(f"/api/reports/{mission_id}/summary")
    assert rep_summary.status_code == 200
    sum_data = rep_summary.json()["summary"]
    assert sum_data["verified"] >= 1

    # Check downloads
    csv_res = client.get(f"/api/reports/{mission_id}/csv")
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers.get("content-type", "")

    json_res = client.get(f"/api/reports/{mission_id}/json")
    assert json_res.status_code == 200

    geojson_res = client.get(f"/api/reports/{mission_id}/geojson")
    assert geojson_res.status_code == 200

    pdf_res = client.get(f"/api/reports/{mission_id}/pdf")
    assert pdf_res.status_code == 200
    assert "application/pdf" in pdf_res.headers.get("content-type", "")
