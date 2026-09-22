"""
SONAR-AI Processing API Router
Starts and monitors multi-stage asynchronous survey processing jobs.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from pydantic import BaseModel

from database import get_db
from models_db import Mission, ProcessingJob, ProcessingLog
from jobs.job_runner import get_job_manager

router = APIRouter(prefix="/api/processing", tags=["Processing"])


class ProcessingStartSchema(BaseModel):
    mission_id: int
    confidence_threshold: float = 0.50
    enable_denoise: bool = True
    enable_clahe: bool = True


@router.post("/start")
def start_processing(data: ProcessingStartSchema, db: Session = Depends(get_db)):
    """Creates a ProcessingJob and launches the pipeline asynchronously."""
    mission = db.query(Mission).filter(Mission.id == data.mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail=f"Mission {data.mission_id} not found.")

    if not mission.files:
        raise HTTPException(status_code=400, detail="No survey files imported for this mission. Please upload sonar imagery first.")

    config = {
        "confidence_threshold": data.confidence_threshold,
        "enable_denoise": data.enable_denoise,
        "enable_clahe": data.enable_clahe
    }

    job = ProcessingJob(
        mission_id=mission.id,
        status="PENDING",
        current_stage="QUEUED",
        progress_percent=0,
        config=config
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Launch in background worker
    manager = get_job_manager()
    manager.start_job(job_id=job.id, mission_id=mission.id, config=config)

    return {
        "job_id": job.id,
        "mission_id": mission.id,
        "status": "PENDING",
        "message": "Processing pipeline initiated in background worker."
    }


@router.get("/{job_id}")
def get_job_status(job_id: int, db: Session = Depends(get_db)):
    """Returns real-time progress, active stage, and step diagnostics."""
    job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found.")
    return job.to_dict()


@router.post("/{job_id}/cancel")
def cancel_processing_job(job_id: int, db: Session = Depends(get_db)):
    """Cancels an active background processing task."""
    job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found.")

    manager = get_job_manager()
    success = manager.cancel_job(job_id)
    job.status = "CANCELLED"
    db.commit()
    return {"message": "Job cancellation requested.", "success": success}


@router.get("/mission/{mission_id}/logs")
def get_mission_logs(mission_id: int, db: Session = Depends(get_db)):
    """Returns historical event logs for the given mission."""
    logs = db.query(ProcessingLog).filter(
        ProcessingLog.mission_id == mission_id
    ).order_by(ProcessingLog.timestamp.asc()).all()
    return [l.to_dict() for l in logs]
