"""
SONAR-AI Model Manager
Manages AI model loading, metadata, versioning, and honest runtime reporting.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import os
import hashlib

from config import MODEL_PATH, DEFAULT_CLASSES


class ModelManager:
    """
    Central manager for AI models. Checks presence of trained weights
    and configures the detection runtime accordingly.
    """

    def __init__(self, model_path: Optional[Path] = None):
        self.model_path = Path(model_path) if model_path else MODEL_PATH
        self.model_name = "sonar_best"
        self.model_version = "1.0.0"
        self.model_type = "YOLOv8-Object-Detection"
        self.classes = DEFAULT_CLASSES
        self.input_resolution = 1280
        self.default_confidence_threshold = 0.50
        self.is_real_model = False
        self.model_instance = None
        self.weights_hash = None

        self._initialize_model()

    def _initialize_model(self):
        """Attempts to load trained weights if present; otherwise enters DEVELOPMENT MODE."""
        if self.model_path.exists() and self.model_path.is_file() and self.model_path.stat().st_size > 1000:
            try:
                # Compute SHA-256 checksum of weights for provenance
                with open(self.model_path, "rb") as f:
                    self.weights_hash = hashlib.sha256(f.read()).hexdigest()[:16]

                from ultralytics import YOLO
                self.model_instance = YOLO(str(self.model_path))
                self.is_real_model = True
                print(f"[SONAR-AI] Loaded verified weights: {self.model_path.name} (SHA: {self.weights_hash})")
            except Exception as e:
                print(f"[SONAR-AI] Warning: Found {self.model_path} but could not initialize: {e}. Defaulting to DEVELOPMENT MODE.")
                self.is_real_model = False
                self.model_instance = None
        else:
            self.is_real_model = False
            self.model_instance = None

    def get_model_status(self) -> Dict[str, Any]:
        """
        Returns transparent model metadata. Never fabricates evaluation metrics.
        """
        if self.is_real_model:
            return {
                "mode": "model",
                "label": "AI MODEL ACTIVE",
                "model_name": self.model_name,
                "model_version": self.model_version,
                "model_type": self.model_type,
                "weights_path": str(self.model_path),
                "weights_hash": self.weights_hash,
                "input_resolution": self.input_resolution,
                "classes": [c["id"] for c in self.classes],
                "evaluation_metrics": "Evaluation not available (Requires benchmark survey dataset validation)",
                "description": f"Loaded verified weights from {self.model_path.name}"
            }
        else:
            return {
                "mode": "demo",
                "label": "DEVELOPMENT MODE — No validated sonar AI model is currently loaded",
                "model_name": "development_simulator",
                "model_version": "0.1.0-dev",
                "model_type": "Deterministic-Development-Fixture",
                "weights_path": None,
                "weights_hash": None,
                "input_resolution": self.input_resolution,
                "classes": [c["id"] for c in self.classes],
                "evaluation_metrics": "Evaluation not available (Simulation only)",
                "description": "No validated sonar AI model is currently loaded. Results are simulated for software testing only."
            }
