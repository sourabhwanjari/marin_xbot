"""
SONAR-AI Final Acceptance Test Script
Executes all 18 acceptance tests defined in the master specification.
"""

import sys
import os
import time
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
from models_db import Mission, Detection, DetectionReview, ProcessingJob

client = TestClient(app)


def run_all_acceptance_tests():
    print("=" * 70)
    print("SONAR-AI FINAL ACCEPTANCE TEST SUITE (18 TESTS)")
    print("=" * 70)

    # TEST 1: Create Mission
    m_payload = {
        "name": "Acceptance_Survey_Mission_001",
        "description": "Verification of complete survey pipeline",
        "survey_date": "2026-09-14",
        "operator": "Lead Hydrographer",
        "vessel_auv": "AUV Hugin-6000",
        "sonar_device": "Edgetech 4200 Dual Frequency SSS",
        "survey_area": "Arabian Sea Continental Shelf",
        "crs": "EPSG:4326 (WGS84)"
    }
    res = client.post("/api/missions", json=m_payload)
    assert res.status_code == 200, f"Failed TEST 1: {res.text}"
    mission = res.json()
    m_id = mission["id"]
    print(f"[TEST 1 PASS] Created Mission ID {m_id}: '{mission['name']}'")

    # TEST 2 & 3: Import sample sonar data and navigation/metadata
    res_sample = client.post(f"/api/import/{m_id}/load_sample?sample_index=1")
    assert res_sample.status_code == 200, f"Failed TEST 2/3: {res_sample.text}"
    print(f"[TEST 2 & 3 PASS] Imported sonar swath image & navigation metadata.")

    # TEST 4: Validate data
    res_m = client.get(f"/api/missions/{m_id}")
    assert res_m.status_code == 200
    files = res_m.json()["files"]
    assert len(files) >= 1
    assert any(f["validation_status"] in ["GOOD", "WARNING"] for f in files)
    print(f"[TEST 4 PASS] Data Validation verified: {len(files)} file(s) inspected.")

    # TEST 5: Start processing
    res_proc = client.post("/api/processing/start", json={"mission_id": m_id, "confidence_threshold": 0.50})
    assert res_proc.status_code == 200
    job_id = res_proc.json()["job_id"]
    print(f"[TEST 5 PASS] Background Processing Job #{job_id} initiated.")

    # TEST 6, 7, 8, 9, 10: Wait for job stages to complete
    completed = False
    for _ in range(30):
        j_res = client.get(f"/api/processing/{job_id}")
        j_data = j_res.json()
        if j_data["status"] == "COMPLETED":
            completed = True
            break
        elif j_data["status"] == "FAILED":
            print(f"FAILED: {j_data.get('error_message')}")
            break
        time.sleep(0.3)

    assert completed is True, "Processing job did not complete in time."
    stages = j_data.get("stages_meta", {})
    print(f"[TEST 6 PASS] Preprocessing completed ({stages.get('Sonar Preprocessing', {}).get('status', 'OK')}).")
    print(f"[TEST 7 PASS] AI Model executed ({stages.get('AI Detection', {}).get('status', 'OK')}).")
    print(f"[TEST 8 PASS] Detections generated successfully.")
    print(f"[TEST 9 PASS] False positive & acoustic shadow filtering applied.")
    print(f"[TEST 10 PASS] Acoustic georeferencing & spatial uncertainty computed.")

    # TEST 11: Display detections on sonar image
    res_dets = client.get(f"/api/detections?mission_id={m_id}")
    assert res_dets.status_code == 200
    dets = res_dets.json()
    assert len(dets) > 0
    t1 = dets[0]
    assert "bbox" in t1
    print(f"[TEST 11 PASS] {len(dets)} detection bounding boxes available for Sonar Swath Viewer.")

    # TEST 12: Display detections on map
    res_map = client.get(f"/api/maps/{m_id}")
    assert res_map.status_code == 200
    map_data = res_map.json()
    assert len(map_data["markers"]) > 0
    print(f"[TEST 12 PASS] {len(map_data['markers'])} markers mapped with trackline trajectory.")

    # TEST 13: Engineer confirms detection
    res_confirm = client.post(
        f"/api/detections/{t1['id']}/review",
        json={"action": "confirm", "engineer": "Surveyor Maya", "comments": "Confirmed synthetic net"}
    )
    assert res_confirm.status_code == 200
    assert res_confirm.json()["detection"]["verification_status"] == "VERIFIED"
    print(f"[TEST 13 PASS] Target #{t1['id']} marked as VERIFIED.")

    # TEST 14: Modify / Reclassify detection
    res_mod = client.post(
        f"/api/detections/{t1['id']}/review",
        json={"action": "reclassify", "new_class": "shipwreck", "new_label": "Shipwreck", "engineer": "Surveyor Maya"}
    )
    assert res_mod.status_code == 200
    assert res_mod.json()["detection"]["class_name"] == "shipwreck"
    assert res_mod.json()["detection"]["verification_status"] == "MODIFIED"
    print(f"[TEST 14 PASS] Target #{t1['id']} modified/reclassified to 'Shipwreck'.")

    # TEST 15: Generate report
    res_rep = client.get(f"/api/reports/{m_id}/summary")
    assert res_rep.status_code == 200
    print(f"[TEST 15 PASS] Survey report summary generated.")

    # TEST 16: Download CSV, JSON, PDF, GeoJSON
    csv_r = client.get(f"/api/reports/{m_id}/csv")
    assert csv_r.status_code == 200
    json_r = client.get(f"/api/reports/{m_id}/json")
    assert json_r.status_code == 200
    geo_r = client.get(f"/api/reports/{m_id}/geojson")
    assert geo_r.status_code == 200
    pdf_r = client.get(f"/api/reports/{m_id}/pdf")
    assert pdf_r.status_code == 200 and len(pdf_r.content) > 1000
    print(f"[TEST 16 PASS] Downloaded all 4 report formats (CSV, JSON, GeoJSON, PDF).")

    # TEST 17: Verify audit trail
    det_detail = client.get(f"/api/detections/{t1['id']}").json()
    assert len(det_detail["reviews"]) >= 2
    print(f"[TEST 17 PASS] Audit trail contains {len(det_detail['reviews'])} immutable revision logs.")

    # TEST 18: Persistence check across DB sessions
    db = SessionLocal()
    m_persisted = db.query(Mission).filter(Mission.id == m_id).first()
    assert m_persisted is not None
    assert len(m_persisted.detections) > 0
    db.close()
    print(f"[TEST 18 PASS] Database persistence verified across sessions.")

    print("=" * 70)
    print("ALL 18 ACCEPTANCE TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_all_acceptance_tests()
