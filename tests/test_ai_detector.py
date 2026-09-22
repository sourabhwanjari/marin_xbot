"""
Unit tests for AI Engine, Detector, Acoustic Shadow, and Filtering
"""

import pytest
import os
import numpy as np

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from ai.model_manager import ModelManager
from ai.detector import SonarDetector
from ai.acoustic_shadow import analyze_acoustic_shadow
from ai.anomaly_scoring import calculate_composite_anomaly_score, compute_geometry_evidence
from ai.postprocessing.filtering import calculate_iou, suppress_duplicates, filter_and_postprocess_detections


def test_model_manager_fallback():
    manager = ModelManager(model_path="non_existent_weights.pt")
    status = manager.get_model_status()
    assert status["mode"] == "demo"
    assert "DEVELOPMENT MODE" in status["label"]
    assert "Evaluation not available" in status["evaluation_metrics"]


def test_detector_inference():
    detector = SonarDetector()
    img = np.full((600, 800, 3), 100, dtype=np.uint8)
    res = detector.detect(img, confidence_threshold=0.50)

    assert "detections" in res
    assert "mode" in res
    for det in res["detections"]:
        assert "id" in det
        assert "class" in det
        assert "confidence" in det
        assert "bbox" in det
        assert "model_version" in det
        assert det["confidence"] >= 0.50


def test_acoustic_shadow_analysis():
    img = np.full((300, 400), 150, dtype=np.uint8)
    # Object on starboard side (x > 200), shadow extends to the right (x2 to x2+width)
    img[50:100, 260:320] = 20  # Dark shadow
    bbox = {"x1": 210, "y1": 50, "x2": 250, "y2": 100}

    shadow_res = analyze_acoustic_shadow(img, bbox)

    assert "shadow_score" in shadow_res
    assert "shadow_method" in shadow_res
    assert shadow_res["shadow_score"] > 0.50  # Strong dark shadow evidence


def test_iou_calculation():
    box1 = {"x1": 10, "y1": 10, "x2": 50, "y2": 50}
    box2 = {"x1": 10, "y1": 10, "x2": 50, "y2": 50}
    assert calculate_iou(box1, box2) == 1.0

    box3 = {"x1": 100, "y1": 100, "x2": 150, "y2": 150}
    assert calculate_iou(box1, box3) == 0.0


def test_composite_anomaly_scoring():
    score = calculate_composite_anomaly_score(
        ai_confidence=0.90,
        geometry_score=0.85,
        shadow_score=0.80
    )
    assert 0.0 <= score["anomaly_score"] <= 1.0
    assert score["anomaly_score_percent"] > 80
