"""
Sonar Noise Filtering and Anomaly Scoring Module
Calculates composite anomaly scores combining AI confidence, geometric regularity,
and acoustic shadow heuristic analysis to suppress false alarms from natural seabed clutter.
"""

import cv2
import numpy as np
from typing import List, Dict, Any, Tuple, Optional


def calculate_iou(box1: Dict[str, int], box2: Dict[str, int]) -> float:
    """Calculates Intersection-over-Union (IoU) between two bounding boxes."""
    x1 = max(box1["x1"], box2["x1"])
    y1 = max(box1["y1"], box2["y1"])
    x2 = min(box1["x2"], box2["x2"])
    y2 = min(box1["y2"], box2["y2"])

    intersection_w = max(0, x2 - x1)
    intersection_h = max(0, y2 - y1)
    intersection_area = intersection_w * intersection_h

    area1 = (box1["x2"] - box1["x1"]) * (box1["y2"] - box1["y1"])
    area2 = (box2["x2"] - box2["x1"]) * (box2["y2"] - box2["y1"])

    union_area = area1 + area2 - intersection_area
    if union_area <= 0:
        return 0.0
    return intersection_area / float(union_area)


def suppress_duplicates(detections: List[Dict[str, Any]], iou_threshold: float = 0.45) -> List[Dict[str, Any]]:
    """Removes overlapping duplicate detections (Non-Maximum Suppression)."""
    if not detections:
        return []

    # Sort descending by confidence
    sorted_dets = sorted(detections, key=lambda d: d.get("confidence", 0.0), reverse=True)
    kept_dets = []

    while sorted_dets:
        current = sorted_dets.pop(0)
        kept_dets.append(current)
        sorted_dets = [
            d for d in sorted_dets
            if calculate_iou(current["bbox"], d["bbox"]) < iou_threshold
        ]

    return kept_dets


def analyze_acoustic_shadow(image: Optional[np.ndarray], bbox: Dict[str, int]) -> Dict[str, Any]:
    """
    Lightweight heuristic acoustic shadow estimator.
    
    SCIENTIFIC NOTE:
    This is an acoustic shadow heuristic based on local pixel luminosity gradient analysis
    and NOT a validated sonar acoustic propagation or bathymetric physics simulation.
    In real Side Scan Sonar, protruding objects block acoustic pulses, casting an acoustic shadow
    (dark / low-backscatter area) immediately behind the bright echo highlight.
    """
    if image is None:
        return {
            "shadow_score": 0.50,
            "method": "neutral_default",
            "note": "Image unavailable for shadow region sampling"
        }

    h, w = image.shape[:2]
    x1, y1, x2, y2 = bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"]

    # Sonar shadows typically extend along the range axis (horizontally or downwards)
    # Sample region to the right or bottom of the detected bounding box
    box_w = max(1, x2 - x1)
    box_h = max(1, y2 - y1)

    # Define candidate shadow inspection window adjacent to bounding box
    shadow_x1 = min(w - 1, x2)
    shadow_x2 = min(w, x2 + int(box_w * 0.8) + 10)
    shadow_y1 = max(0, y1)
    shadow_y2 = min(h, y2)

    if shadow_x2 <= shadow_x1 or shadow_y2 <= shadow_y1:
        # Fallback inspection below
        shadow_x1 = max(0, x1)
        shadow_x2 = min(w, x2)
        shadow_y1 = min(h - 1, y2)
        shadow_y2 = min(h, y2 + int(box_h * 0.8) + 10)

    if shadow_x2 <= shadow_x1 or shadow_y2 <= shadow_y1:
        return {
            "shadow_score": 0.55,
            "method": "edge_boundary_fallback",
            "note": "Bounding box too close to frame boundary for shadow context"
        }

    # Extract shadow candidate patch
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    patch = gray[shadow_y1:shadow_y2, shadow_x1:shadow_x2]
    if patch.size == 0:
        return {"shadow_score": 0.50, "method": "empty_patch"}

    mean_intensity = float(np.mean(patch))
    global_mean = float(np.mean(gray))

    # A shadow has lower intensity (darker) than the surrounding seafloor
    if mean_intensity < global_mean:
        contrast_ratio = (global_mean - mean_intensity) / max(global_mean, 1.0)
        shadow_score = min(0.95, 0.50 + (contrast_ratio * 0.5))
    else:
        shadow_score = max(0.20, 0.50 - ((mean_intensity - global_mean) / max(global_mean, 1.0) * 0.3))

    return {
        "shadow_score": round(float(shadow_score), 2),
        "mean_intensity": round(mean_intensity, 1),
        "global_mean": round(global_mean, 1),
        "method": "acoustic_shadow_heuristic"
    }


def compute_shape_score(bbox: Dict[str, int], obj_class: str) -> float:
    """
    Heuristic geometry score assessing whether the aspect ratio and area
    match man-made acoustic profiles (pipes are elongated, cylinders are regular, nets are irregular).
    """
    w = max(1, bbox["x2"] - bbox["x1"])
    h = max(1, bbox["y2"] - bbox["y1"])
    aspect_ratio = max(w, h) / float(min(w, h))

    if obj_class == "pipe":
        # Pipes are characteristically elongated
        return 0.85 if aspect_ratio >= 2.5 else 0.60
    elif obj_class == "cylinder":
        # Cylinders have moderate aspect ratios
        return 0.80 if 1.2 <= aspect_ratio <= 3.0 else 0.65
    elif obj_class == "ghost_net":
        # Nets have spread out, web-like geometry
        return 0.82 if aspect_ratio < 2.5 else 0.70
    elif obj_class == "shipwreck":
        # Shipwrecks are large anomalies
        area = w * h
        return 0.90 if area > 2000 else 0.72
    return 0.70


def filter_and_score_detections(
    detections: List[Dict[str, Any]],
    image: Optional[np.ndarray] = None,
    min_confidence: float = 0.50,
    iou_threshold: float = 0.45
) -> List[Dict[str, Any]]:
    """
    Main noise filtering and anomaly assessment pipeline:
    1. Removes detections with confidence < min_confidence
    2. Suppresses duplicate bounding boxes
    3. Calculates acoustic shadow heuristics
    4. Computes combined Anomaly Score:
       Anomaly Score = 0.6 * AI Confidence + 0.2 * Shape Score + 0.2 * Shadow Score
    5. Categorizes into HIGH / MEDIUM / LOW confidence tiers
    """
    # 1. Filter by threshold
    valid = [d for d in detections if d.get("confidence", 0.0) >= min_confidence]

    # 2. Suppress overlaps
    deduped = suppress_duplicates(valid, iou_threshold=iou_threshold)

    scored_detections = []
    for det in deduped:
        conf = det.get("confidence", 0.0)
        obj_class = det.get("class", "debris")
        bbox = det["bbox"]

        # Shape score
        shape_score = compute_shape_score(bbox, obj_class)

        # Acoustic shadow heuristic
        shadow_analysis = analyze_acoustic_shadow(image, bbox)
        shadow_score = shadow_analysis["shadow_score"]

        # Composite Anomaly Score
        anomaly_score = (0.60 * conf) + (0.20 * shape_score) + (0.20 * shadow_score)
        anomaly_score = round(min(1.0, max(0.0, anomaly_score)), 3)
        anomaly_percent = int(round(anomaly_score * 100))

        # Status tier
        if conf >= 0.80:
            status = "HIGH CONFIDENCE"
            tier = "high"
        elif conf >= 0.60:
            status = "MEDIUM CONFIDENCE"
            tier = "medium"
        else:
            status = "LOW CONFIDENCE"
            tier = "low"

        det_copy = dict(det)
        det_copy.update({
            "shape_score": round(shape_score, 2),
            "shadow_score": round(shadow_score, 2),
            "shadow_analysis": shadow_analysis,
            "anomaly_score": anomaly_score,
            "anomaly_score_percent": anomaly_percent,
            "status": status,
            "tier": tier
        })
        scored_detections.append(det_copy)

    # Re-assign sequential IDs
    for idx, d in enumerate(scored_detections, 1):
        d["id"] = idx

    return scored_detections
