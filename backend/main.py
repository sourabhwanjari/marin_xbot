"""
SONAR-AI Production Backend Application
AI-Powered Side Scan Sonar Marine Survey & Underwater Anomaly Detection System
"""

import os
import io
import base64
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from config import CORS_ORIGINS, STORAGE_DIR, REPORTS_DIR
from database import init_db, get_db
from models_db import Mission, SurveyFile, Detection
from api.missions import router as missions_router
from api.imports import router as imports_router
from api.processing import router as processing_router
from api.detections import router as detections_router
from api.reviews import router as reviews_router
from api.maps import router as maps_router
from api.reports import router as reports_router
from api.models import router as models_router
from api.health import router as health_router, health_check as api_health_check
from api.files import router as files_router

from sonar_processing.preprocessing import SonarPreprocessor
from ai.detector import SonarDetector
from ai.postprocessing.filtering import filter_and_postprocess_detections
from geospatial.georeferencing import SonarGeoreferencer
from reports.exporter import SurveyReportExporter

# Initialize database schema on startup
init_db()

app = FastAPI(
    title="SONAR-AI",
    description="AI-Powered Side Scan Sonar Marine Survey & Underwater Anomaly Detection System",
    version="2.0.0"
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register modular routers
app.include_router(health_router)
app.include_router(missions_router)
app.include_router(imports_router)
app.include_router(processing_router)
app.include_router(detections_router)
app.include_router(reviews_router)
app.include_router(maps_router)
app.include_router(reports_router)
app.include_router(models_router)
app.include_router(files_router)

# Compatibility single detector instance
_shared_detector = SonarDetector()
_shared_exporter = SurveyReportExporter()


@app.get("/")
def read_root():
    return {
        "system": "SONAR-AI",
        "description": "AI-Powered Side Scan Sonar Marine Survey & Underwater Anomaly Detection System",
        "version": "2.0.0",
        "status": "online",
        "screens": [
            "1. Missions (/api/missions)",
            "2. Import & Processing (/api/import, /api/processing)",
            "3. Analysis (/api/detections, /api/detections/{id}/review)",
            "4. Map (/api/maps/{mission_id})",
            "5. Reports (/api/reports/{mission_id})"
        ]
    }


# Backward-compatible endpoints for existing test scripts
@app.get("/health")
def root_health(db: Session = Depends(get_db)):
    return api_health_check(db)


@app.post("/detect")
async def single_swath_detect(
    file: UploadFile = File(...),
    metadata: Optional[UploadFile] = File(None),
    threshold: float = Form(0.50),
    enable_denoise: bool = Form(True),
    enable_clahe: bool = Form(True)
):
    """Direct single-image detection endpoint for testing & quick evaluation."""
    filename = file.filename or "unknown.jpg"
    image_bytes = await file.read()
    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty file.")

    nparr = np.frombuffer(image_bytes, np.uint8)
    raw_img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
    if raw_img is None:
        raise HTTPException(status_code=400, detail="Could not decode image.")

    # Preprocessing
    preprocessor = SonarPreprocessor(
        target_size=1280,
        enable_denoise=enable_denoise,
        enable_clahe=enable_clahe
    )
    processed_img, prep_meta = preprocessor.process(raw_img)

    # Detection
    raw_res = _shared_detector.detect(processed_img, confidence_threshold=threshold)
    raw_dets = raw_res.get("detections", [])
    mode = raw_res.get("mode", "demo")

    # Postprocessing
    filtered = filter_and_postprocess_detections(
        raw_dets, image=processed_img, min_confidence=threshold, iou_threshold=0.45
    )

    # Georeferencing
    nav_data = {
        "latitude": 18.9220,
        "longitude": 72.8347,
        "heading": 90.0,
        "depth": 28.5,
        "is_demo_gps": True
    }
    georef = SonarGeoreferencer()
    geotagged = georef.georeference_all(
        filtered, nav_data, prep_meta["processed_width"], prep_meta["processed_height"]
    )

    # Generate quick export reports
    from report import generate_csv_report, generate_json_report, REPORTS_DIR as LEGACY_REPORTS_DIR
    generate_csv_report(geotagged, mode=mode)
    generate_json_report(geotagged, metadata=prep_meta, mode=mode)

    # Encode image data url
    _, buffer = cv2.imencode(".jpg", processed_img, [cv2.IMWRITE_JPEG_QUALITY, 85])
    encoded = base64.b64encode(buffer).decode("utf-8")

    return {
        "mode": mode,
        "model_status": raw_res.get("model_status"),
        "image_name": filename,
        "image_data_url": f"data:image/jpeg;base64,{encoded}",
        "image_width": prep_meta["processed_width"],
        "image_height": prep_meta["processed_height"],
        "summary": {
            "total": len(geotagged),
            "high": sum(1 for d in geotagged if d.get("tier") == "high"),
            "medium": sum(1 for d in geotagged if d.get("tier") == "medium"),
            "low": sum(1 for d in geotagged if d.get("tier") == "low")
        },
        "detections": geotagged
    }


@app.get("/reports/csv")
def legacy_csv_report():
    from report import REPORTS_DIR as LEGACY_REPORTS_DIR
    file_path = os.path.join(LEGACY_REPORTS_DIR, "sonar_debris_report.csv")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="No report generated yet.")
    return FileResponse(file_path, media_type="text/csv", filename="sonar_debris_report.csv")


@app.get("/reports/json")
def legacy_json_report():
    from report import REPORTS_DIR as LEGACY_REPORTS_DIR
    file_path = os.path.join(LEGACY_REPORTS_DIR, "sonar_debris_report.json")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="No report generated yet.")
    return FileResponse(file_path, media_type="application/json", filename="sonar_debris_report.json")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
