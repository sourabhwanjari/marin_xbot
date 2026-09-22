"""
Verification test for Sonar Image Preprocessing pipeline.
"""

import os
import sys
import cv2

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from preprocessing import preprocess_sonar_pipeline

def test_preprocessing():
    sample_img_path = os.path.join(os.path.dirname(__file__), "..", "sample_data", "sonar_images", "sample_sonar_01.jpg")
    assert os.path.exists(sample_img_path), f"Missing test image at {sample_img_path}"

    img = cv2.imread(sample_img_path)
    assert img is not None, "Failed to load sample image"

    processed, meta = preprocess_sonar_pipeline(img, target_size=1024, enable_denoise=True, enable_clahe=True)

    assert processed is not None, "Preprocessing returned None"
    assert processed.shape[0] > 0 and processed.shape[1] > 0, "Invalid processed shape"
    assert meta["denoise_applied"] is True
    assert meta["clahe_applied"] is True
    print("[PASS] Sonar preprocessing test passed!")
    print("Metadata:", meta)

if __name__ == "__main__":
    test_preprocessing()
