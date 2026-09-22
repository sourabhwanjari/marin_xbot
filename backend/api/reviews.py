"""
SONAR-AI Detection Review API Router
Enables human-in-the-loop verification, correction, and immutable audit logging.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from database import get_db
from models_db import Detection, DetectionReview

router = APIRouter(prefix="/api/detections", tags=["Engineer Review"])


class ReviewActionSchema(BaseModel):
    action: str  # confirm, reject, modify, reclassify
    engineer: Optional[str] = "Lead Sonar Reviewer"
    new_class: Optional[str] = None
    new_label: Optional[str] = None
    new_bbox: Optional[Dict[str, int]] = None
    comments: Optional[str] = None


@router.post("/{detection_id}/review")
def review_detection(
    detection_id: int,
    data: ReviewActionSchema,
    db: Session = Depends(get_db)
):
    """
    Applies an engineer verification action to an anomaly detection.
    Maintains an immutable audit log entry detailing previous vs updated attributes.
    """
    det = db.query(Detection).filter(Detection.id == detection_id).first()
    if not det:
        raise HTTPException(status_code=404, detail=f"Detection {detection_id} not found.")

    action_lower = data.action.lower()
    original_class = det.class_name
    original_bbox = {"x1": det.bbox_x1, "y1": det.bbox_y1, "x2": det.bbox_x2, "y2": det.bbox_y2}
    original_conf = det.ai_confidence

    if action_lower == "confirm":
        det.verification_status = "VERIFIED"
        review_action = "CONFIRM"
        action_comment = data.comments or "Target confirmed as genuine artificial anomaly."

    elif action_lower == "reject":
        det.verification_status = "REJECTED"
        review_action = "REJECT"
        action_comment = data.comments or "Target rejected as natural seafloor structure / acoustic noise."

    elif action_lower == "reclassify":
        if not data.new_class:
            raise HTTPException(status_code=400, detail="Must specify 'new_class' for reclassification.")
        det.class_name = data.new_class
        det.label = data.new_label or data.new_class.replace("_", " ").title()
        det.verification_status = "MODIFIED"
        review_action = "RECLASSIFY"
        action_comment = data.comments or f"Reclassified from {original_class} to {data.new_class}."

    elif action_lower == "modify":
        if data.new_bbox:
            det.bbox_x1 = data.new_bbox.get("x1", det.bbox_x1)
            det.bbox_y1 = data.new_bbox.get("y1", det.bbox_y1)
            det.bbox_x2 = data.new_bbox.get("x2", det.bbox_x2)
            det.bbox_y2 = data.new_bbox.get("y2", det.bbox_y2)
        if data.new_class:
            det.class_name = data.new_class
            det.label = data.new_label or data.new_class.replace("_", " ").title()
        det.verification_status = "MODIFIED"
        review_action = "MODIFY"
        action_comment = data.comments or "Bounding box and/or target boundary adjusted by engineer."

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported review action '{data.action}'. Use confirm, reject, modify, or reclassify.")

    det.updated_at = datetime.utcnow()

    # Log into audit trail
    review = DetectionReview(
        detection_id=det.id,
        engineer=data.engineer or "Lead Sonar Reviewer",
        action=review_action,
        original_class=original_class,
        new_class=det.class_name,
        original_bbox=original_bbox,
        new_bbox={"x1": det.bbox_x1, "y1": det.bbox_y1, "x2": det.bbox_x2, "y2": det.bbox_y2},
        original_confidence=original_conf,
        comments=action_comment,
        timestamp=datetime.utcnow()
    )
    db.add(review)
    db.commit()
    db.refresh(det)

    return {
        "message": f"Detection {detection_id} successfully updated with action '{review_action}'.",
        "detection": det.to_dict(),
        "audit_review": review.to_dict()
    }
