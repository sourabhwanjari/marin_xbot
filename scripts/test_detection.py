"""
Verification test for Sonar Detector, Noise Filtering, Geotagging and Reporting.
"""

import os
import sys
import cv2

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from detector import SonarDetector
from filtering import filter_and_score_detections
from geotagging import parse_metadata_file, geotag_detections
from report import generate_csv_report, generate_json_report

def test_full_detection_pipeline():
    sample_img_path = os.path.join(os.path.dirname(__file__), "..", "sample_data", "sonar_images", "sample_sonar_01.jpg")
    img = cv2.imread(sample_img_path)
    assert img is not None

    detector = SonarDetector()
    status = detector.get_status()
    print("Detector status:", status)

    # 1. Detection
    res = detector.detect(img, confidence_threshold=0.5)
    assert "detections" in res
    assert len(res["detections"]) > 0
    print(f"Raw detections found: {len(res['detections'])}")

    # 2. Filtering & Anomaly scoring
    filtered = filter_and_score_detections(res["detections"], image=img, min_confidence=0.5)
    assert len(filtered) > 0
    for d in filtered:
        assert "anomaly_score" in d
        assert "shadow_score" in d
        assert "tier" in d
    print(f"Filtered detections: {len(filtered)}")

    # 3. Geotagging
    meta_path = os.path.join(os.path.dirname(__file__), "..", "sample_data", "metadata", "sample_metadata.json")
    with open(meta_path, "rb") as f:
        meta_bytes = f.read()
    nav_data = parse_metadata_file(meta_bytes, "sample_metadata.json")
    geotagged = geotag_detections(filtered, nav_data, img.shape[1], img.shape[0])
    for g in geotagged:
        assert "latitude" in g
        assert "longitude" in g
    print(f"Geotagged {len(geotagged)} anomalies with lat/lon")

    # 4. Report generation
    csv_file = generate_csv_report(geotagged, mode=res["mode"], filename="test_report.csv")
    json_file = generate_json_report(geotagged, metadata={}, mode=res["mode"], filename="test_report.json")
    assert os.path.exists(csv_file)
    assert os.path.exists(json_file)
    print(f"[PASS] Full pipeline test passed successfully!")

if __name__ == "__main__":
    test_full_detection_pipeline()
