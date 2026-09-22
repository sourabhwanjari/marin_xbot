"""
SONAR-AI System Health API Router
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime

from database import get_db
from ai.model_manager import ModelManager

router = APIRouter(prefix="/api/health", tags=["Health"])
manager = ModelManager()


@router.get("")
def health_check(db: Session = Depends(get_db)):
    """Validates API responsiveness, database connectivity, and AI model status."""
    db_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    status = manager.get_model_status()

    return {
        "status": "healthy" if db_ok else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected" if db_ok else "disconnected",
        "detector_mode": status["mode"],
        "detector_label": status["label"]
    }
