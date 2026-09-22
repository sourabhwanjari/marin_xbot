"""
SONAR-AI Reports API Router
Endpoints for generating and downloading survey anomaly reports in CSV, JSON, GeoJSON, and PDF.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path

from database import get_db
from models_db import Mission, Detection
from reports.exporter import SurveyReportExporter

router = APIRouter(prefix="/api/reports", tags=["Reports"])
exporter = SurveyReportExporter()


@router.get("/{mission_id}/summary")
def get_report_summary(mission_id: int, db: Session = Depends(get_db)):
    """Returns aggregated survey targets and verification metrics."""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail=f"Mission {mission_id} not found.")

    dets = db.query(Detection).filter(Detection.mission_id == mission_id).all()
    det_dicts = [d.to_dict() for d in dets]

    total = len(dets)
    verified = sum(1 for d in dets if d.verification_status == "VERIFIED")
    rejected = sum(1 for d in dets if d.verification_status == "REJECTED")
    modified = sum(1 for d in dets if d.verification_status == "MODIFIED")
    needs_review = sum(1 for d in dets if d.verification_status in ["NEEDS_REVIEW", "AI_DETECTED"])

    class_counts = {
        "ghost_net": sum(1 for d in dets if d.class_name == "ghost_net"),
        "shipwreck": sum(1 for d in dets if d.class_name == "shipwreck"),
        "pipe": sum(1 for d in dets if d.class_name == "pipe"),
        "cylinder": sum(1 for d in dets if d.class_name == "cylinder"),
        "debris": sum(1 for d in dets if d.class_name == "debris")
    }

    return {
        "mission": mission.to_dict(),
        "summary": {
            "total_detections": total,
            "verified": verified,
            "rejected": rejected,
            "modified": modified,
            "needs_review": needs_review,
            "class_breakdown": class_counts
        },
        "detections": det_dicts
    }


@router.get("/{mission_id}/csv")
def download_csv_report(mission_id: int, db: Session = Depends(get_db)):
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail=f"Mission {mission_id} not found.")

    dets = [d.to_dict() for d in mission.detections]
    filename = f"survey_report_mission_{mission_id}.csv"
    path = exporter.export_csv(mission.to_dict(), dets, filename)
    return FileResponse(path, media_type="text/csv", filename=filename)


@router.get("/{mission_id}/json")
def download_json_report(mission_id: int, db: Session = Depends(get_db)):
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail=f"Mission {mission_id} not found.")

    dets = [d.to_dict() for d in mission.detections]
    filename = f"survey_report_mission_{mission_id}.json"
    path = exporter.export_json(mission.to_dict(), dets, filename)
    return FileResponse(path, media_type="application/json", filename=filename)


@router.get("/{mission_id}/geojson")
def download_geojson_report(mission_id: int, db: Session = Depends(get_db)):
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail=f"Mission {mission_id} not found.")

    dets = [d.to_dict() for d in mission.detections]
    filename = f"survey_anomalies_mission_{mission_id}.geojson"
    path = exporter.export_geojson(mission.to_dict(), dets, filename)
    return FileResponse(path, media_type="application/geo+json", filename=filename)


@router.get("/{mission_id}/pdf")
def download_pdf_report(mission_id: int, db: Session = Depends(get_db)):
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail=f"Mission {mission_id} not found.")

    dets = [d.to_dict() for d in mission.detections]
    filename = f"survey_dossier_mission_{mission_id}.pdf"
    path = exporter.export_pdf(mission.to_dict(), dets, filename)
    return FileResponse(path, media_type="application/pdf", filename=filename)
