"""
SONAR-AI Acoustic Shadow Analysis Module
Analyzes acoustic shadow regions (zones of acoustic occlusions/attenuation)
cast along the range axis immediately behind reflective sonar highlights.

SCIENTIFIC INTEGRITY NOTICE:
This module utilizes an acoustic contrast gradient heuristic and is NOT a 3D
hydrodynamic or multi-path sound propagation simulation. It provides supporting evidence
for differentiating 3D protruding man-made objects from flat seafloor textures.
"""

from typing import Dict, Any, Optional
import cv2
import numpy as np


def analyze_acoustic_shadow(
    image: Optional[np.ndarray],
    bbox: Dict[str, int]
) -> Dict[str, Any]:
    """
    Examines the backscatter intensity directly behind the candidate object bounding box.
    Returns shadow_detected, shadow_score (0.0 to 1.0), and shadow_method.
    """
    if image is None:
        return {
            "shadow_detected": False,
            "shadow_score": 0.50,
            "shadow_method": "fallback_no_image",
            "notes": "Image unavailable for shadow region sampling."
        }

    h, w = image.shape[:2]
    x1, y1, x2, y2 = bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"]

    box_w = max(1, x2 - x1)
    box_h = max(1, y2 - y1)

    # In side scan sonar, the acoustic shadow is cast away from nadir (trackline)
    # If object is on right side of swath (x > w/2), shadow extends to the right.
    # If object is on left side of swath (x < w/2), shadow extends to the left.
    mid_x = w / 2.0
    is_starboard = ((x1 + x2) / 2.0) >= mid_x

    if is_starboard:
        shadow_x1 = min(w - 1, x2)
        shadow_x2 = min(w, x2 + int(box_w * 0.9) + 15)
    else:
        shadow_x2 = max(0, x1)
        shadow_x1 = max(0, x1 - int(box_w * 0.9) - 15)

    shadow_y1 = max(0, y1)
    shadow_y2 = min(h, y2)

    # Boundary check
    if shadow_x2 <= shadow_x1 or shadow_y2 <= shadow_y1:
        # Fallback to downward offset
        shadow_x1 = max(0, x1)
        shadow_x2 = min(w, x2)
        shadow_y1 = min(h - 1, y2)
        shadow_y2 = min(h, y2 + int(box_h * 0.8) + 15)

    if shadow_x2 <= shadow_x1 or shadow_y2 <= shadow_y1:
        return {
            "shadow_detected": False,
            "shadow_score": 0.50,
            "shadow_method": "boundary_limit_fallback",
            "notes": "Bounding box too close to frame boundary for shadow context."
        }

    # Grayscale image
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    patch = gray[shadow_y1:shadow_y2, shadow_x1:shadow_x2]
    if patch.size == 0:
        return {
            "shadow_detected": False,
            "shadow_score": 0.50,
            "shadow_method": "empty_patch",
            "notes": "Zero-sized shadow patch."
        }

    mean_shadow = float(np.mean(patch))
    global_mean = float(np.mean(gray))

    # A genuine acoustic shadow is significantly darker than average seabed backscatter
    if mean_shadow < global_mean:
        contrast_ratio = (global_mean - mean_shadow) / max(global_mean, 1.0)
        # Score scaled between 0.50 and 0.95
        score = min(0.95, 0.50 + (contrast_ratio * 0.50))
        detected = contrast_ratio > 0.15
    else:
        # Region behind highlight is brighter or equal to seabed (unlikely to be a proud object)
        score = max(0.15, 0.50 - ((mean_shadow - global_mean) / max(global_mean, 1.0) * 0.30))
        detected = False

    return {
        "shadow_detected": detected,
        "shadow_score": round(float(score), 3),
        "mean_shadow_intensity": round(mean_shadow, 1),
        "seabed_mean_intensity": round(global_mean, 1),
        "shadow_method": "acoustic_gradient_heuristic",
        "notes": "Heuristic pixel luminosity contrast analysis."
    }
