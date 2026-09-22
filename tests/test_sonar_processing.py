"""
Unit tests for Sonar Preprocessing, Motion Compensation, and Dropout Detection
"""

import pytest
import os
import numpy as np
import cv2

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from sonar_processing.preprocessing import SonarPreprocessor
from sonar_processing.motion_compensation import MotionCompensationEngine
from sonar_processing.dropout_detection import DropoutDetector


def test_sonar_preprocessor():
    preprocessor = SonarPreprocessor(target_size=1000, enable_denoise=True, enable_clahe=True)

    # 1500x800 image
    raw = np.random.randint(20, 200, (1500, 800, 3), dtype=np.uint8)
    processed, meta = preprocessor.process(raw, swath_range_m=50.0)

    assert meta["original_width"] == 800
    assert meta["original_height"] == 1500
    assert max(processed.shape[:2]) <= 1000
    assert meta["denoise_applied"] is True
    assert meta["clahe_applied"] is True
    assert meta["pixel_resolution_cross_m"] > 0


def test_motion_compensation_honest_evaluation():
    engine = MotionCompensationEngine()

    # Case 1: missing attitude telemetry
    empty_nav = {"latitude": 18.0, "longitude": 72.0}
    eval1 = engine.evaluate_motion_availability(empty_nav)
    assert eval1["status"] in ["UNAVAILABLE", "PARTIAL"]
    assert "heave" in eval1["missing_parameters"]

    # Case 2: full telemetry available
    full_nav = {"latitude": 18.0, "longitude": 72.0, "heading": 90.0, "heave": 0.2, "pitch": 1.5, "roll": -0.8}
    eval2 = engine.evaluate_motion_availability(full_nav)
    assert eval2["status"] == "FULL"
    assert len(eval2["missing_parameters"]) == 0

    # Geometric offset test
    cross_m, along_m, meta = engine.compute_geometric_offset(
        pixel_x=640, pixel_y=400, img_width=1280, img_height=800,
        motion_eval=eval2, slant_range_m=50.0
    )
    assert isinstance(cross_m, float)
    assert isinstance(along_m, float)
    assert len(meta["corrections_applied"]) > 0


def test_dropout_detector():
    detector = DropoutDetector()

    # Create image with artificial acoustic blackout scanlines
    img = np.full((100, 200), 120, dtype=np.uint8)
    # 2-line dropout (recoverable)
    img[20:22, :] = 0
    # 6-line blackout (unrecoverable)
    img[60:66, :] = 0

    res = detector.detect_image_dropouts(img)
    assert res["has_dropouts"] is True
    assert len(res["gaps"]) >= 2
    classifications = [g["classification"] for g in res["gaps"]]
    assert "RECOVERABLE" in classifications
    assert "UNRECOVERABLE" in classifications
    assert res["status"] == "CRITICAL"
