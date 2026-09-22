"""
SONAR-AI Postprocessing & False-Positive Filtering Module
Removes duplicate boxes (IoU), filters candidates below confidence threshold,
validates bounding dimensions, computes acoustic shadow evidence, and calculates composite anomaly scores.
"""

from typing import List, Dict, Any, Optional
import numpy as np

from ..acoustic_shadow import analyze_acoustic_shadow
from ..anomaly_scoring import compute_geometry_evidence, calculate_composite_anomaly_score


def calculate_iou(box1: Dict[str, int], box2: Dict[str, int]) -> float:
    """Calculates Intersection-over-Union (IoU) between two bounding boxes."""
    x1 = max(box1["x1"], box2["x1"])
    y1 = max(box1["y1"], box2["y1"])
    x2 = min(box1["x2"], box2["x2"])
    y2 = min(box1["y2"], box2["y2"])

    intersection_w = max(0, x2 - x1)
    intersection_h = max(0, y2 - y1)
    intersection_area = intersection_w * intersection_h

    area1 = max(1, (box1["x2"] - box1["x1"]) * (box1["y2"] - box1["y1"]))
    area2 = max(1, (box2["x2"] - box2["x1"]) * (box2["y2"] - box2["y1"]))

    union_area = area1 + area2 - intersection_area
    if union_area <= 0:
        return 0.0
    return intersection_area / float(union_area)


def suppress_duplicates(detections: List[Dict[str, Any]], iou_threshold: float = 0.45) -> List[Dict[str, Any]]:
    """Suppresses duplicate/overlapping bounding boxes via Non-Maximum Suppression (NMS)."""
    if not detections:
        return []

    # Sort descending by AI confidence
    sorted_dets = sorted(detections, key=lambda d: d.get("confidence", 0.0), reverse=True)
    kept = []

    while sorted_dets:
        current = sorted_dets.pop(0)
        kept.append(current)
        sorted_dets = [
            d for d in sorted_dets
            if calculate_iou(current["bbox"], d["bbox"]) < iou_threshold
        ]

    return kept


def filter_and_postprocess_detections(
    detections: List[Dict[str, Any]],
    image: Optional[np.ndarray] = None,
    min_confidence: float = 0.50,
    iou_threshold: float = 0.45
) -> List[Dict[str, Any]]:
    """
    Complete post-processing pipeline:
    1. Confidence thresholding
    2. Box boundary and minimum area validation
    3. IoU overlap deduplication
    4. Geometry regularity assessment
    5. Acoustic shadow analysis
    6. Transparent composite anomaly scoring
    7. Verification status categorization
    """
    # 1. Filter by confidence
    valid = [d for d in detections if d.get("confidence", 0.0) >= min_confidence]

    # 2. Box geometry validation (reject tiny artifacts < 10 px)
    size_checked = []
    for d in valid:
        bbox = d.get("bbox", {})
        w = bbox.get("x2", 0) - bbox.get("x1", 0)
        h = bbox.get("y2", 0) - bbox.get("y1", 0)
        if w >= 8 and h >= 8:
            size_checked.append(d)

    # 3. Duplicate suppression
    deduped = suppress_duplicates(size_checked, iou_threshold=iou_threshold)

    processed = []
    for det in deduped:
        conf = det.get("confidence", 0.0)
        obj_class = det.get("class", "debris")
        bbox = det["bbox"]

        # Geometry evidence
        geom_score = compute_geometry_evidence(bbox, obj_class)

        # Acoustic shadow analysis
        shadow_meta = analyze_acoustic_shadow(image, bbox)
        shadow_score = shadow_meta["shadow_score"]

        # Composite anomaly calculation
        composite = calculate_composite_anomaly_score(
            ai_confidence=conf,
            geometry_score=geom_score,
            shadow_score=shadow_score
        )

        anomaly_score = composite["anomaly_score"]
        anomaly_percent = composite["anomaly_score_percent"]

        # Status categorization
        if conf >= 0.80 and anomaly_score >= 0.75:
            verification_status = "AI_DETECTED"
            tier = "high"
        elif conf >= 0.60:
            verification_status = "NEEDS_REVIEW"
            tier = "medium"
        else:
            verification_status = "NEEDS_REVIEW"
            tier = "low"

        det_record = dict(det)
        det_record.update({
            "shape_score": round(geom_score, 3),
            "shadow_score": round(shadow_score, 3),
            "shadow_analysis": shadow_meta,
            "anomaly_score": anomaly_score,
            "anomaly_score_percent": anomaly_percent,
            "anomaly_weights": composite["weights"],
            "verification_status": verification_status,
            "tier": tier
        })
        processed.append(det_record)

    # Sequential re-indexing
    for idx, d in enumerate(processed, 1):
        d["id"] = idx

    return processed
