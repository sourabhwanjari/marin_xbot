"""
Sonar Image Preprocessing Module
Implements acoustic enhancement filters: denoising (speckle reduction),
CLAHE contrast enhancement, and intensity normalization for Side Scan Sonar (SSS) imagery.
"""

import cv2
import numpy as np
from typing import Tuple, Dict, Any


def read_image_from_bytes(image_bytes: bytes) -> np.ndarray:
    """Decodes raw image bytes into an OpenCV BGR/Grayscale image."""
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError("Failed to decode image. Ensure uploaded file is a valid image (JPG, PNG).")
    return img


def resize_image(image: np.ndarray, max_dimension: int = 1280) -> Tuple[np.ndarray, float]:
    """
    Resizes image maintaining aspect ratio if max dimension exceeds limit.
    Returns (resized_image, scale_factor).
    """
    h, w = image.shape[:2]
    if max(h, w) <= max_dimension:
        return image, 1.0

    scale = max_dimension / float(max(h, w))
    new_w = int(w * scale)
    new_h = int(h * scale)
    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return resized, scale


def denoise_image(image: np.ndarray, h_param: float = 7.0) -> np.ndarray:
    """
    Reduces acoustic speckle noise using bilateral or non-local means filtering
    while preserving edge boundaries of structural debris.
    """
    if len(image.shape) == 2 or (len(image.shape) == 3 and image.shape[2] == 1):
        # Grayscale acoustic data
        denoised = cv2.bilateralFilter(image, d=7, sigmaColor=50, sigmaSpace=50)
    else:
        # 3-channel image
        denoised = cv2.bilateralFilter(image, d=7, sigmaColor=50, sigmaSpace=50)
    return denoised


def enhance_contrast(image: np.ndarray, clip_limit: float = 2.5, tile_grid_size: Tuple[int, int] = (8, 8)) -> np.ndarray:
    """
    Applies Contrast Limited Adaptive Histogram Equalization (CLAHE)
    to enhance acoustic shadows and highlight bright debris returns against seafloor sediment.
    """
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    if len(image.shape) == 3 and image.shape[2] == 3:
        # Convert to LAB color space, apply CLAHE to L channel, convert back
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l_chan, a_chan, b_chan = cv2.split(lab)
        cl = clahe.apply(l_chan)
        limg = cv2.merge((cl, a_chan, b_chan))
        enhanced = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
    elif len(image.shape) == 3 and image.shape[2] == 4:
        # Handle RGBA
        bgr = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
        enhanced = enhance_contrast(bgr, clip_limit, tile_grid_size)
    else:
        # Single channel grayscale
        enhanced = clahe.apply(image)
    return enhanced


def normalize_image(image: np.ndarray) -> np.ndarray:
    """Normalizes pixel range to [0, 255] for consistent dynamic range."""
    norm = cv2.normalize(image, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)
    return norm


def preprocess_sonar_pipeline(
    image: np.ndarray,
    target_size: int = 1280,
    enable_denoise: bool = True,
    enable_clahe: bool = True
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Complete configurable sonar preprocessing pipeline:
    1. Size validation and scaling
    2. Speckle noise reduction
    3. CLAHE acoustic contrast enhancement
    4. Dynamic range normalization
    """
    orig_h, orig_w = image.shape[:2]
    
    # Resize
    processed, scale = resize_image(image, max_dimension=target_size)
    
    # Denoise
    if enable_denoise:
        processed = denoise_image(processed)
        
    # Contrast
    if enable_clahe:
        processed = enhance_contrast(processed)
        
    # Normalization
    processed = normalize_image(processed)

    metadata = {
        "original_width": orig_w,
        "original_height": orig_h,
        "processed_width": processed.shape[1],
        "processed_height": processed.shape[0],
        "scale_factor": scale,
        "denoise_applied": enable_denoise,
        "clahe_applied": enable_clahe,
    }
    
    return processed, metadata
