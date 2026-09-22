"""
SONAR-AI Missions API Router
Endpoints for managing marine survey missions.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from database import get_db
from models_db import Mission, SurveyFile, Detection, ProcessingJob

router = APIRouter(prefix="/api/missions", tags=["Missions"])


class MissionCreateSchema(BaseModel):
    name: str
    description: Optional[str] = None
    survey_date: Optional[str] = None
    operator: Optional[str] = "Sonar Survey Engineer"
    vessel_auv: Optional[str] = "Survey Vessel / AUV"
    sonar_device: Optional[str] = "Side Scan Sonar (SSS)"
    survey_area: Optional[str] = "Coastal Survey Zone"
    crs: Optional[str] = "EPSG:4326 (WGS84)"


class MissionUpdateSchema(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    operator: Optional[str] = None
    vessel_auv: Optional[str] = None
    sonar_device: Optional[str] = None
    survey_area: Optional[str] = None
    crs: Optional[str] = None


@router.get("")
def list_missions(include_archived: bool = Query(False), db: Session = Depends(get_db)):
    """Returns all missions with file counts, detection stats, and processing status."""
    query = db.query(Mission)
    if not include_archived:
        query = query.filter(Mission.is_archived == False)
    missions = query.order_by(Mission.created_at.desc()).all()
    return [m.to_dict() for m in missions]


@router.post("")
def create_mission(data: MissionCreateSchema, db: Session = Depends(get_db)):
    """Creates a new marine survey mission."""
    survey_date_str = data.survey_date or datetime.utcnow().strftime("%Y-%m-%d")
    mission = Mission(
        name=data.name.strip(),
        description=data.description,
        survey_date=survey_date_str,
        operator=data.operator,
        vessel_auv=data.vessel_auv,
        sonar_device=data.sonar_device,
        survey_area=data.survey_area,
        crs=data.crs or "EPSG:4326 (WGS84)",
        status="READY"
    )
    db.add(mission)
    db.commit()
    db.refresh(mission)
    return mission.to_dict()


@router.get("/{mission_id}")
def get_mission(mission_id: int, db: Session = Depends(get_db)):
    """Returns full mission details including file inventory and detection summary."""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail=f"Mission {mission_id} not found.")

    res = mission.to_dict()
    res["files"] = [f.to_dict() for f in mission.files]
    res["jobs"] = [j.to_dict() for j in mission.jobs]

    # Summary of detections
    dets = mission.detections
    res["detections_summary"] = {
        "total": len(dets),
        "verified": sum(1 for d in dets if d.verification_status == "VERIFIED"),
        "rejected": sum(1 for d in dets if d.verification_status == "REJECTED"),
        "needs_review": sum(1 for d in dets if d.verification_status in ["NEEDS_REVIEW", "AI_DETECTED"]),
        "classes": {
            "ghost_net": sum(1 for d in dets if d.class_name == "ghost_net"),
            "shipwreck": sum(1 for d in dets if d.class_name == "shipwreck"),
            "pipe": sum(1 for d in dets if d.class_name == "pipe"),
            "cylinder": sum(1 for d in dets if d.class_name == "cylinder"),
            "debris": sum(1 for d in dets if d.class_name == "debris")
        }
    }
    return res


@router.patch("/{mission_id}")
def update_mission(mission_id: int, data: MissionUpdateSchema, db: Session = Depends(get_db)):
    """Updates or renames an existing mission."""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail=f"Mission {mission_id} not found.")

    if data.name:
        mission.name = data.name.strip()
    if data.description is not None:
        mission.description = data.description
    if data.operator is not None:
        mission.operator = data.operator
    if data.vessel_auv is not None:
        mission.vessel_auv = data.vessel_auv
    if data.sonar_device is not None:
        mission.sonar_device = data.sonar_device
    if data.survey_area is not None:
        mission.survey_area = data.survey_area
    if data.crs is not None:
        mission.crs = data.crs

    db.commit()
    db.refresh(mission)
    return mission.to_dict()


@router.post("/{mission_id}/archive")
def archive_mission(mission_id: int, db: Session = Depends(get_db)):
    """Toggles archive state for mission."""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail=f"Mission {mission_id} not found.")
    mission.is_archived = not mission.is_archived
    db.commit()
    return {"message": f"Mission {'archived' if mission.is_archived else 'unarchived'} successfully.", "mission": mission.to_dict()}


@router.delete("/{mission_id}")
def delete_mission(mission_id: int, db: Session = Depends(get_db)):
    """Deletes mission and associated records permanently."""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail=f"Mission {mission_id} not found.")
    db.delete(mission)
    db.commit()
    return {"message": f"Mission {mission_id} deleted successfully."}
