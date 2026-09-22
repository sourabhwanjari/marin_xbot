"""
SONAR-AI Import & Data Validation API Router
Handles file uploads for sonar imagery and navigation logs with immediate structural validation.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import shutil
import uuid
from pathlib import Path

from database import get_db
from models_db import Mission, SurveyFile
from config import UPLOADS_DIR, ALLOWED_SONAR_EXTENSIONS, ALLOWED_NAV_EXTENSIONS
from sonar_adapters.image_adapter import ImageAdapter
from sonar_adapters.generic_metadata_adapter import GenericMetadataAdapter
from sonar_adapters.vendor_adapter_stub import FutureVendorAdapterStub

router = APIRouter(prefix="/api/import", tags=["Data Import"])

img_adapter = ImageAdapter()
nav_adapter = GenericMetadataAdapter()
vendor_stub = FutureVendorAdapterStub()


@router.post("/{mission_id}")
async def upload_survey_files(
    mission_id: int,
    sonar_files: List[UploadFile] = File(default=[]),
    nav_files: List[UploadFile] = File(default=[]),
    db: Session = Depends(get_db)
):
    """
    Accepts sonar imagery and navigation telemetry files for a mission.
    Validates file formats, coordinates, timestamps, and returns structured validation status.
    """
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail=f"Mission {mission_id} not found.")

    mission_upload_dir = UPLOADS_DIR / f"mission_{mission_id}"
    mission_upload_dir.mkdir(parents=True, exist_ok=True)

    imported_files = []
    validation_summary = {
        "overall_status": "GOOD",
        "sonar_valid": False,
        "nav_valid": False,
        "items": []
    }

    # 1. Process Sonar Files
    for upload in sonar_files:
        if not upload.filename:
            continue
        safe_name = f"{uuid.uuid4().hex[:8]}_{Path(upload.filename).name}"
        dest_path = mission_upload_dir / safe_name

        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(upload.file, buffer)

        ext = dest_path.suffix.lower()

        # Check for vendor proprietary formats
        if vendor_stub.supports(dest_path):
            val = vendor_stub.validate(dest_path)
            file_type = "proprietary_sonar"
        elif img_adapter.supports(dest_path):
            val = img_adapter.validate(dest_path)
            file_type = "sonar_image"
            if val.is_valid:
                validation_summary["sonar_valid"] = True
        else:
            val = nav_adapter.validate(dest_path)
            file_type = "metadata"

        # Track worst status
        if val.status == "CRITICAL":
            validation_summary["overall_status"] = "CRITICAL"
        elif val.status == "WARNING" and validation_summary["overall_status"] != "CRITICAL":
            validation_summary["overall_status"] = "WARNING"

        file_rec = SurveyFile(
            mission_id=mission_id,
            filename=upload.filename,
            file_type=file_type,
            file_path=str(dest_path),
            file_size=dest_path.stat().st_size,
            mime_type=upload.content_type,
            validation_status=val.status,
            validation_report=val.to_dict(),
            width=val.metadata.get("width"),
            height=val.metadata.get("height")
        )
        db.add(file_rec)
        db.commit()
        db.refresh(file_rec)

        imported_files.append(file_rec.to_dict())
        validation_summary["items"].append({
            "file": upload.filename,
            "type": file_type,
            "status": val.status,
            "messages": val.messages
        })

    # 2. Process Navigation Files
    for upload in nav_files:
        if not upload.filename:
            continue
        safe_name = f"{uuid.uuid4().hex[:8]}_{Path(upload.filename).name}"
        dest_path = mission_upload_dir / safe_name

        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(upload.file, buffer)

        val = nav_adapter.validate(dest_path)
        file_type = "navigation"
        if val.is_valid:
            validation_summary["nav_valid"] = True

        if val.status == "CRITICAL":
            validation_summary["overall_status"] = "CRITICAL"
        elif val.status == "WARNING" and validation_summary["overall_status"] != "CRITICAL":
            validation_summary["overall_status"] = "WARNING"

        file_rec = SurveyFile(
            mission_id=mission_id,
            filename=upload.filename,
            file_type=file_type,
            file_path=str(dest_path),
            file_size=dest_path.stat().st_size,
            mime_type=upload.content_type,
            validation_status=val.status,
            validation_report=val.to_dict()
        )
        db.add(file_rec)
        db.commit()
        db.refresh(file_rec)

        imported_files.append(file_rec.to_dict())
        validation_summary["items"].append({
            "file": upload.filename,
            "type": file_type,
            "status": val.status,
            "messages": val.messages
        })

    return {
        "mission_id": mission_id,
        "files_uploaded": len(imported_files),
        "validation_summary": validation_summary,
        "files": imported_files
    }


@router.post("/{mission_id}/load_sample")
def load_sample_survey_data(mission_id: int, sample_index: int = 1, db: Session = Depends(get_db)):
    """
    Copies bundled test sonar images and navigation metadata into mission folder for quick evaluation.
    Clearly tags as SAMPLE DATA.
    """
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail=f"Mission {mission_id} not found.")

    mission_upload_dir = UPLOADS_DIR / f"mission_{mission_id}"
    mission_upload_dir.mkdir(parents=True, exist_ok=True)

    project_root = Path(__file__).resolve().parent.parent.parent
    sample_dir = project_root / "sample_data"

    img_name = "sample_sonar_01.jpg" if sample_index == 1 else "sample_sonar_02.png"
    src_img = sample_dir / "sonar_images" / img_name
    src_meta = sample_dir / "metadata" / ("sample_metadata.json" if sample_index == 1 else "sample_metadata.csv")

    if not src_img.exists():
        raise HTTPException(status_code=500, detail="Sample sonar image missing from repository sample_data.")

    dest_img = mission_upload_dir / f"SAMPLE_{img_name}"
    shutil.copy2(src_img, dest_img)

    val_img = img_adapter.validate(dest_img)
    file_img = SurveyFile(
        mission_id=mission_id,
        filename=f"SAMPLE_{img_name}",
        file_type="sonar_image",
        file_path=str(dest_img),
        file_size=dest_img.stat().st_size,
        mime_type="image/jpeg" if img_name.endswith(".jpg") else "image/png",
        validation_status=val_img.status,
        validation_report=val_img.to_dict(),
        width=val_img.metadata.get("width"),
        height=val_img.metadata.get("height")
    )
    db.add(file_img)

    dest_meta = None
    if src_meta.exists():
        dest_meta = mission_upload_dir / f"SAMPLE_{src_meta.name}"
        shutil.copy2(src_meta, dest_meta)
        val_meta = nav_adapter.validate(dest_meta)
        file_meta = SurveyFile(
            mission_id=mission_id,
            filename=f"SAMPLE_{src_meta.name}",
            file_type="navigation",
            file_path=str(dest_meta),
            file_size=dest_meta.stat().st_size,
            mime_type="application/json" if src_meta.suffix == ".json" else "text/csv",
            validation_status=val_meta.status,
            validation_report=val_meta.to_dict()
        )
        db.add(file_meta)

    db.commit()
    return {
        "message": "Sample survey files loaded successfully.",
        "sample_tag": "SAMPLE DATA (Test Fixtures)",
        "mission_id": mission_id,
        "image_file": file_img.to_dict()
    }
