"""
SONAR-AI Anomaly Scoring Engine
Calculates transparent, multi-factor anomaly scores combining AI detection confidence,
geometric regularity, and acoustic shadow evidence.
"""

from typing import Dict, Any
from config import (
    ANOMALY_WEIGHT_CONFIDENCE,
    ANOMALY_WEIGHT_GEOMETRY,
    ANOMALY_WEIGHT_SHADOW
)


def compute_geometry_evidence(bbox: Dict[str, int], obj_class: str) -> float:
    """
    Evaluates whether the candidate bounding box aspect ratio and dimensions
    exhibit non-natural (man-made / artificial) geometric regularity.
    """
    w = max(1, bbox["x2"] - bbox["x1"])
    h = max(1, bbox["y2"] - bbox["y1"])
    aspect_ratio = max(w, h) / float(min(w, h))

    if obj_class == "pipe":
        # Underwater pipelines are linear and highly elongated
        return 0.90 if aspect_ratio >= 2.5 else 0.60
    elif obj_class == "cylinder":
        # Cylindrical tanks have moderate symmetry
        return 0.85 if 1.2 <= aspect_ratio <= 3.0 else 0.65
    elif obj_class == "ghost_net":
        # Lost nets exhibit diffuse, sprawling web-like shapes
        return 0.84 if aspect_ratio < 2.5 else 0.70
    elif obj_class == "shipwreck":
        # Wreckage has large acoustic footprint (>2000 px area)
        area = w * h
        return 0.92 if area > 2000 else 0.75
    else:  # other debris
        return 0.72


def calculate_composite_anomaly_score(
    ai_confidence: float,
    geometry_score: float,
    shadow_score: float,
    w_conf: float = ANOMALY_WEIGHT_CONFIDENCE,
    w_geom: float = ANOMALY_WEIGHT_GEOMETRY,
    w_shadow: float = ANOMALY_WEIGHT_SHADOW
) -> Dict[str, Any]:
    """
    Combines weighted signals into a transparent Composite Anomaly Score.
    """
    total_weight = w_conf + w_geom + w_shadow
    if total_weight <= 0:
        total_weight = 1.0

    raw_score = (
        (ai_confidence * w_conf) +
        (geometry_score * w_geom) +
        (shadow_score * w_shadow)
    ) / total_weight

    clamped_score = round(max(0.0, min(1.0, raw_score)), 3)

    return {
        "anomaly_score": clamped_score,
        "anomaly_score_percent": int(round(clamped_score * 100)),
        "weights": {
            "ai_confidence": w_conf,
            "geometry_evidence": w_geom,
            "acoustic_shadow": w_shadow
        },
        "components": {
            "ai_confidence": round(ai_confidence, 3),
            "geometry_score": round(geometry_score, 3),
            "shadow_score": round(shadow_score, 3)
        }
    }
