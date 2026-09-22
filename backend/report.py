"""
Sonar Debris Incident Report Generator
Generates exportable CSV and JSON reports containing localized debris coordinates,
confidence scores, anomaly assessment metrics, and operational metadata.
"""

import os
import csv
import json
from datetime import datetime
from typing import List, Dict, Any

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


def generate_csv_report(detections: List[Dict[str, Any]], mode: str, filename: str = "sonar_debris_report.csv") -> str:
    """
    Generates a CSV report file matching the required schema:
    ID, Object, Confidence, Anomaly Score, Latitude, Longitude, Width, Height, Timestamp, Status, Mode
    """
    file_path = os.path.join(REPORTS_DIR, filename)

    fieldnames = [
        "ID",
        "Object",
        "Confidence",
        "Anomaly Score",
        "Latitude",
        "Longitude",
        "Width",
        "Height",
        "Timestamp",
        "Status",
        "Mode"
    ]

    with open(file_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fieldnames)

        for det in detections:
            writer.writerow([
                det.get("id", ""),
                det.get("label", det.get("class", "Unknown")),
                f"{det.get('confidence_percent', int(det.get('confidence', 0) * 100))}%",
                f"{det.get('anomaly_score_percent', int(det.get('anomaly_score', 0) * 100))}%",
                det.get("latitude", ""),
                det.get("longitude", ""),
                f"{det.get('estimated_width', '')}m",
                f"{det.get('estimated_height', '')}m",
                det.get("timestamp", datetime.utcnow().isoformat()),
                det.get("status", "HIGH CONFIDENCE"),
                mode.upper()
            ])

    return file_path


def generate_json_report(
    detections: List[Dict[str, Any]],
    metadata: Dict[str, Any],
    mode: str,
    filename: str = "sonar_debris_report.json"
) -> str:
    """
    Generates a structured JSON report including summary metrics and individual hazard records.
    """
    file_path = os.path.join(REPORTS_DIR, filename)

    report_payload = {
        "system": "SONAR-AI Underwater Debris Detection System",
        "generated_at": datetime.utcnow().isoformat(),
        "mode": mode,
        "total_anomalies": len(detections),
        "summary": {
            "high_confidence_count": sum(1 for d in detections if d.get("tier") == "high"),
            "medium_confidence_count": sum(1 for d in detections if d.get("tier") == "medium"),
            "low_confidence_count": sum(1 for d in detections if d.get("tier") == "low"),
            "classes": {
                "ghost_net": sum(1 for d in detections if d.get("class") == "ghost_net"),
                "shipwreck": sum(1 for d in detections if d.get("class") == "shipwreck"),
                "pipe": sum(1 for d in detections if d.get("class") == "pipe"),
                "cylinder": sum(1 for d in detections if d.get("class") == "cylinder"),
                "debris": sum(1 for d in detections if d.get("class") == "debris"),
            }
        },
        "preprocessing_metadata": metadata,
        "detections": detections,
        "disclaimer": (
            "Side Scan Sonar interpretation depends strongly on sonar frequency, range, "
            "vehicle motion, seafloor conditions, object orientation, and acoustic shadows. "
            "This prototype is intended as a decision-support tool."
        )
    }

    with open(file_path, mode="w", encoding="utf-8") as f:
        json.dump(report_payload, f, indent=2)

    return file_path
