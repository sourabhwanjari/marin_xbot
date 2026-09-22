"""
SONAR-AI Image Adapter
Concrete adapter for standard raster side scan sonar formats: JPG, PNG, TIFF, BMP.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import os
import cv2
import numpy as np

from .base import SonarAdapter, AdapterValidationResult


class ImageAdapter(SonarAdapter):
    SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"}

    def supports(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS

    def validate(self, file_path: Path) -> AdapterValidationResult:
        messages = []
        if not file_path.exists():
            return AdapterValidationResult(
                is_valid=False,
                status="ERROR",
                messages=["File does not exist on disk."]
            )

        file_size = file_path.stat().st_size
        if file_size == 0:
            return AdapterValidationResult(
                is_valid=False,
                status="CRITICAL",
                messages=["Uploaded image is 0 bytes (corrupt or empty payload)."]
            )

        # Attempt to read image header
        try:
            img = cv2.imread(str(file_path), cv2.IMREAD_UNCHANGED)
            if img is None:
                return AdapterValidationResult(
                    is_valid=False,
                    status="CRITICAL",
                    messages=["Image decoder failed. Corrupted image frame or unsupported compression format."]
                )

            h, w = img.shape[:2]
            channels = 1 if len(img.shape) == 2 else img.shape[2]

            messages.append(f"Sonar frame readable ({w}x{h} px, {channels} channel(s)).")

            # Check for abnormal dimensions
            if w < 64 or h < 64:
                return AdapterValidationResult(
                    is_valid=False,
                    status="CRITICAL",
                    messages=[f"Image dimensions ({w}x{h}) are too small for side scan sonar analysis."]
                )

            status = "GOOD"
            aspect_ratio = max(w, h) / float(min(w, h))
            if aspect_ratio > 10.0:
                messages.append(f"Notice: High swath aspect ratio ({aspect_ratio:.1f}:1). Processing will maintain geometry.")

            # Check for pure blank/black frame
            mean_val = float(np.mean(img))
            if mean_val < 1.0 or mean_val > 254.0:
                status = "WARNING"
                messages.append("Warning: Image dynamic range indicates severe sensor saturation or total acoustic blackout.")

            return AdapterValidationResult(
                is_valid=True,
                status=status,
                messages=messages,
                metadata={
                    "width": w,
                    "height": h,
                    "channels": channels,
                    "file_size": file_size,
                    "mean_intensity": round(mean_val, 2)
                }
            )
        except Exception as e:
            return AdapterValidationResult(
                is_valid=False,
                status="ERROR",
                messages=[f"Validation exception: {str(e)}"]
            )

    def extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        val = self.validate(file_path)
        return val.metadata

    def read_data(self, file_path: Path) -> np.ndarray:
        img = cv2.imread(str(file_path), cv2.IMREAD_UNCHANGED)
        if img is None:
            raise ValueError(f"Could not load sonar image from {file_path}")
        return img
