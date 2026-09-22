"""
SONAR-AI Sonar Image Preprocessing Module
Implements acoustic enhancement filters: speckle reduction (bilateral),
CLAHE contrast enhancement, dynamic range normalization, and variable resolution preservation.
"""

from typing import Tuple, Dict, Any, Optional
import cv2
import numpy as np


class SonarPreprocessor:
    """
    Configurable image preprocessing pipeline designed specifically for
    Side Scan Sonar acoustic imagery.
    """

    def __init__(
        self,
        target_size: int = 1280,
        enable_denoise: bool = True,
        denoise_strength: float = 7.0,
        enable_clahe: bool = True,
        clahe_clip_limit: float = 2.5,
        clahe_grid_size: Tuple[int, int] = (8, 8)
    ):
        self.target_size = target_size
        self.enable_denoise = enable_denoise
        self.denoise_strength = denoise_strength
        self.enable_clahe = enable_clahe
        self.clahe_clip_limit = clahe_clip_limit
        self.clahe_grid_size = clahe_grid_size

    def resize_preserving_resolution(self, image: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Resizes image maintaining aspect ratio if max dimension exceeds limit.
        Returns (resized_image, scale_factor).
        """
        h, w = image.shape[:2]
        if max(h, w) <= self.target_size:
            return image.copy(), 1.0

        scale = self.target_size / float(max(h, w))
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        return resized, scale

    def denoise_speckle(self, image: np.ndarray) -> np.ndarray:
        """
        Suppresses high-frequency acoustic speckle noise while preserving
        hard acoustic edges of artificial structures and shadow boundaries.
        """
        d = int(self.denoise_strength)
        sigma = self.denoise_strength * 7.0
        if len(image.shape) == 2 or (len(image.shape) == 3 and image.shape[2] == 1):
            return cv2.bilateralFilter(image, d=d, sigmaColor=sigma, sigmaSpace=sigma)
        return cv2.bilateralFilter(image, d=d, sigmaColor=sigma, sigmaSpace=sigma)

    def enhance_clahe(self, image: np.ndarray) -> np.ndarray:
        """
        Contrast Limited Adaptive Histogram Equalization (CLAHE)
        amplifies subtle acoustic shadow gradients and dim reflections.
        """
        clahe = cv2.createCLAHE(
            clipLimit=self.clahe_clip_limit,
            tileGridSize=self.clahe_grid_size
        )

        if len(image.shape) == 3 and image.shape[2] == 3:
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l_chan, a_chan, b_chan = cv2.split(lab)
            cl = clahe.apply(l_chan)
            merged = cv2.merge((cl, a_chan, b_chan))
            return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
        elif len(image.shape) == 3 and image.shape[2] == 4:
            bgr = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
            return self.enhance_clahe(bgr)
        else:
            return clahe.apply(image)

    def normalize_dynamic_range(self, image: np.ndarray) -> np.ndarray:
        """Normalizes pixel range to full 8-bit dynamic window [0, 255]."""
        return cv2.normalize(image, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)

    def process(self, image: np.ndarray, swath_range_m: float = 50.0) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Runs complete preprocessing sequence and computes physical pixel resolution metadata.
        """
        orig_h, orig_w = image.shape[:2]

        # 1. Resize / resolution normalization
        resized, scale = self.resize_preserving_resolution(image)
        proc_h, proc_w = resized.shape[:2]

        processed = resized

        # 2. Speckle noise handling
        if self.enable_denoise:
            processed = self.denoise_speckle(processed)

        # 3. Contrast enhancement
        if self.enable_clahe:
            processed = self.enhance_clahe(processed)

        # 4. Intensity normalization
        processed = self.normalize_dynamic_range(processed)

        # Compute physical pixel resolution (meters per pixel across swath)
        pixel_res_cross_m = round(swath_range_m / max(1, orig_w), 4)
        pixel_res_along_m = round(10.0 / max(1, orig_h), 4)  # approx 10m track length per frame

        meta = {
            "original_width": orig_w,
            "original_height": orig_h,
            "processed_width": proc_w,
            "processed_height": proc_h,
            "scale_factor": round(scale, 4),
            "pixel_resolution_cross_m": pixel_res_cross_m,
            "pixel_resolution_along_m": pixel_res_along_m,
            "swath_range_m": swath_range_m,
            "denoise_applied": self.enable_denoise,
            "denoise_strength": self.denoise_strength,
            "clahe_applied": self.enable_clahe,
            "clahe_clip_limit": self.clahe_clip_limit
        }

        return processed, meta
