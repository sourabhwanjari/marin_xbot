"""
SONAR-AI Models API Router
Provides active AI model versioning, weights integrity hash, and supported target classes.
"""

from fastapi import APIRouter
from ai.model_manager import ModelManager

router = APIRouter(prefix="/api/models", tags=["AI Models"])
model_manager = ModelManager()


@router.get("")
def get_model_info():
    """Returns runtime model configuration and verification state."""
    return model_manager.get_model_status()
