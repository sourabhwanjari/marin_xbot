"""
SONAR-AI File Stream & Image Serving API Router
Streams uploaded sonar imagery and generated previews to the frontend Sonar Viewer.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
import os

from database import get_db
from models_db import SurveyFile

router = APIRouter(prefix="/api/files", tags=["Files"])


@router.get("/{file_id}/image")
def get_file_image(file_id: int, db: Session = Depends(get_db)):
    """Streams the raw sonar image file to the frontend canvas viewer."""
    survey_file = db.query(SurveyFile).filter(SurveyFile.id == file_id).first()
    if not survey_file:
        raise HTTPException(status_code=404, detail=f"Survey file {file_id} not found.")

    path = Path(survey_file.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File content missing from local storage.")

    media_type = survey_file.mime_type or "image/jpeg"
    if path.suffix.lower() == ".png":
        media_type = "image/png"
    elif path.suffix.lower() in [".tif", ".tiff"]:
        media_type = "image/tiff"

    return FileResponse(path, media_type=media_type, filename=survey_file.filename)
