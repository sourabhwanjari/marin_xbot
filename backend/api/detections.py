"""
SONAR-AI Detections API Router
Querying and creating detections with bounding box geometry and spatial geotags.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from database import get_db
from models_db import Detection, DetectionReview, Mission, SurveyFile
from geospatial.georeferencing import SonarGeoreferencer

router = APIRouter(prefix="/api/detections", tags=["Detections"])


class ManualDetectionCreateSchema(BaseModel):
    mission_id: int
    class_name: str
    label: Optional[str] = None
    bbox_x1: int
    bbox_y1: int
    bbox_x2: int
    bbox_y2: int
    engineer: Optional[str] = "Sonar Review Engineer"
    notes: Optional[str] = "Manual target annotation added by hydrographer."


@router.get("")
def list_detections(
    mission_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    class_name: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Returns detections filtered by mission, verification status, or object class."""
    query = db.query(Detection)
    if mission_id:
        query = query.filter(Detection.mission_id == mission_id)
    if status:
        query = query.filter(Detection.verification_status == status)
    if class_name:
        query = query.filter(Detection.class_name == class_name)

    dets = query.order_by(Detection.id.asc()).all()
    return [d.to_dict() for d in dets]


@router.get("/{detection_id}")
def get_detection_details(detection_id: int, db: Session = Depends(get_db)):
    """Returns comprehensive detection details including audit review trail."""
    det = db.query(Detection).filter(Detection.id == detection_id).first()
    if not det:
        raise HTTPException(status_code=404, detail=f"Detection {detection_id} not found.")

    res = det.to_dict()
    res["reviews"] = [r.to_dict() for r in det.reviews]
    return res


@router.post("/manual")
def add_manual_detection(data: ManualDetectionCreateSchema, db: Session = Depends(get_db)):
    """
    Enables hydrographer to manually annotate a sonar target that was missed by AI.
    Calculates georeferencing and creates an initial audit log entry.
    """
    mission = db.query(Mission).filter(Mission.id == data.mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail=f"Mission {data.mission_id} not found.")

    first_image = db.query(SurveyFile).filter(
        SurveyFile.mission_id == data.mission_id,
        SurveyFile.file_type == "sonar_image"
    ).first()

    w = first_image.width if first_image and first_image.width else 1280
    h = first_image.height if first_image and first_image.height else 800

    # Approximate georeference based on first navigation point or mission defaults
    nav_pt = mission.navigation_points[0] if mission.navigation_points else None
    nav_data = {
        "latitude": nav_pt.latitude if nav_pt else 18.9220,
        "longitude": nav_pt.longitude if nav_pt else 72.8347,
        "heading": nav_pt.heading if nav_pt else 90.0,
        "depth": nav_pt.depth if nav_pt else 28.5,
        "is_demo_gps": False if nav_pt else True
    }

    georeferencer = SonarGeoreferencer()
    geo_res = georeferencer.georeference_detection(
        det={"bbox": {"x1": data.bbox_x1, "y1": data.bbox_y1, "x2": data.bbox_x2, "y2": data.bbox_y2}},
        nav_data=nav_data,
        img_width=w,
        img_height=h
    )

    det = Detection(
        mission_id=data.mission_id,
        source_file_id=first_image.id if first_image else None,
        class_name=data.class_name,
        label=data.label or data.class_name.replace("_", " ").title(),
        ai_confidence=1.00,  # Human engineer verification
        anomaly_score=1.00,
        shape_score=1.00,
        shadow_score=0.80,
        bbox_x1=data.bbox_x1,
        bbox_y1=data.bbox_y1,
        bbox_x2=data.bbox_x2,
        bbox_y2=data.bbox_y2,
        latitude=geo_res["latitude"],
        longitude=geo_res["longitude"],
        depth=geo_res["depth"],
        estimated_width=2.5,
        estimated_height=2.0,
        location_quality=geo_res["location_quality"],
        horizontal_uncertainty_m=geo_res["horizontal_uncertainty_m"],
        vertical_uncertainty_m=geo_res["vertical_uncertainty_m"],
        verification_status="VERIFIED",
        model_name="human_operator",
        model_version="manual_annotation",
        is_manual=True
    )
    db.add(det)
    db.commit()
    db.refresh(det)

    # Add audit review record
    review = DetectionReview(
        detection_id=det.id,
        engineer=data.engineer or "Sonar Review Engineer",
        action="MANUAL_ADD",
        new_class=data.class_name,
        new_bbox={"x1": data.bbox_x1, "y1": data.bbox_y1, "x2": data.bbox_x2, "y2": data.bbox_y2},
        original_confidence=1.00,
        comments=data.notes
    )
    db.add(review)
    db.commit()

    return det.to_dict()
