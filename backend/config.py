"""
SONAR-AI Central Configuration Module
Provides environment-variable-backed settings for database, directories,
AI models, and survey processing defaults.
"""

import os
from pathlib import Path
from typing import List

# Base paths
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/sonar_ai.db")

# Directory paths
STORAGE_DIR = Path(os.getenv("STORAGE_DIR", BASE_DIR / "storage"))
UPLOADS_DIR = STORAGE_DIR / "raw"
PROCESSED_DIR = STORAGE_DIR / "processed"
REPORTS_DIR = STORAGE_DIR / "reports"
LOGS_DIR = STORAGE_DIR / "logs"

for path in [STORAGE_DIR, UPLOADS_DIR, PROCESSED_DIR, REPORTS_DIR, LOGS_DIR]:
    path.mkdir(parents=True, exist_ok=True)

# AI & Models configuration
MODEL_DIR = BASE_DIR / "ai" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)
MODEL_PATH = Path(os.getenv("MODEL_PATH", MODEL_DIR / "sonar_best.pt"))

# Sonar Detection Classes
DEFAULT_CLASSES = [
    {"id": "ghost_net", "label": "Ghost Net", "description": "Abandoned, lost, or discarded fishing gear", "typical_size": (3.5, 2.2)},
    {"id": "shipwreck", "label": "Shipwreck", "description": "Sunken vessel or structural wreckage", "typical_size": (12.0, 4.5)},
    {"id": "pipe", "label": "Pipe", "description": "Underwater pipeline or conduit", "typical_size": (6.0, 0.8)},
    {"id": "cylinder", "label": "Cylinder", "description": "Cylindrical artificial container or tank", "typical_size": (1.8, 0.9)},
    {"id": "debris", "label": "Other Debris", "description": "Unclassified man-made debris or anomaly", "typical_size": (2.0, 1.5)},
]

# Security & Upload constraints
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", 100 * 1024 * 1024))  # 100 MB
ALLOWED_SONAR_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"}
ALLOWED_NAV_EXTENSIONS = {".csv", ".json", ".txt"}

# Anomaly Scoring Weights (configurable)
ANOMALY_WEIGHT_CONFIDENCE = float(os.getenv("WEIGHT_CONFIDENCE", 0.60))
ANOMALY_WEIGHT_GEOMETRY = float(os.getenv("WEIGHT_GEOMETRY", 0.20))
ANOMALY_WEIGHT_SHADOW = float(os.getenv("WEIGHT_SHADOW", 0.20))

# CORS Origins
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
