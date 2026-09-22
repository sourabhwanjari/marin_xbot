"""
API Endpoint verification test using FastAPI TestClient.
"""

import os
import sys
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from main import app

client = TestClient(app)

def test_api():
    # 1. Health
    res = client.get("/health")
    assert res.status_code == 200, res.text
    print("[PASS] GET /health:", res.json())

    # 2. Root
    res = client.get("/")
    assert res.status_code == 200, res.text
    print("[PASS] GET /:", res.json()["system"])

    # 3. Detect
    img_path = os.path.join(os.path.dirname(__file__), "..", "sample_data", "sonar_images", "sample_sonar_01.jpg")
    meta_path = os.path.join(os.path.dirname(__file__), "..", "sample_data", "metadata", "sample_metadata.json")
    
    with open(img_path, "rb") as img_file, open(meta_path, "rb") as meta_file:
        files = {
            "file": ("sample_sonar_01.jpg", img_file, "image/jpeg"),
            "metadata": ("sample_metadata.json", meta_file, "application/json")
        }
        data = {
            "threshold": 0.50,
            "enable_denoise": True,
            "enable_clahe": True
        }
        res = client.post("/detect", files=files, data=data)
        
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["mode"] == "demo"
    assert len(body["detections"]) > 0
    assert "image_data_url" in body
    print(f"[PASS] POST /detect returned {len(body['detections'])} detections successfully.")

    # 4. Reports CSV & JSON
    res_csv = client.get("/reports/csv")
    assert res_csv.status_code == 200
    assert "ID,Object,Confidence" in res_csv.text
    print("[PASS] GET /reports/csv downloaded valid CSV report.")

    res_json = client.get("/reports/json")
    assert res_json.status_code == 200
    json_data = res_json.json()
    assert "total_anomalies" in json_data
    print("[PASS] GET /reports/json downloaded valid JSON report.")

if __name__ == "__main__":
    test_api()
