"""
SONAR-AI Artificial Intelligence Engine
Modules for model lifecycle management, YOLO inference, acoustic shadow estimation,
false-positive suppression, and multi-factor anomaly scoring.
"""

from .model_manager import ModelManager
from .detector import SonarDetector
from .acoustic_shadow import analyze_acoustic_shadow
from .anomaly_scoring import calculate_composite_anomaly_score

__all__ = [
    "ModelManager",
    "SonarDetector",
    "analyze_acoustic_shadow",
    "calculate_composite_anomaly_score"
]
