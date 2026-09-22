"""
SONAR-AI Spatial Uncertainty Engine
Calculates horizontal and vertical positioning uncertainty bounds
based on GPS quality, towfish altitude, swath offset distance, and attitude telemetry availability.
"""

from typing import Dict, Any


def calculate_spatial_uncertainty(
    nav_data: Dict[str, Any],
    cross_track_m: float,
    motion_status: str,
    swath_range_m: float = 50.0
) -> Dict[str, Any]:
    """
    Computes horizontal and vertical error radii in meters.
    """
    is_demo = nav_data.get("is_demo_gps", False)
    if is_demo:
        return {
            "horizontal_uncertainty_m": 8.5,
            "vertical_uncertainty_m": 2.0,
            "location_quality": "APPROXIMATE",
            "quality_note": "Approximate Image-Level Location (Demo coordinates active)."
        }

    # Base GPS receiver error (commercial marine GNSS ~ 1.5m, RTK/USBL ~ 0.3m)
    base_gps_error = 2.0

    # Cross-track swath error increases linearly with range away from nadir
    slant_ratio = abs(cross_track_m) / max(1.0, swath_range_m / 2.0)
    swath_geometry_error = slant_ratio * 1.8

    # Motion correction penalty
    if motion_status == "FULL":
        motion_error = 0.5
        quality = "EXACT / HIGH QUALITY"
    elif motion_status == "PARTIAL":
        motion_error = 2.5
        quality = "ESTIMATED"
    else:  # UNAVAILABLE
        motion_error = 5.0
        quality = "APPROXIMATE"

    horizontal_error = round(base_gps_error + swath_geometry_error + motion_error, 2)
    vertical_error = round(1.0 + (0.05 * float(nav_data.get("depth", 20.0))), 2)

    return {
        "horizontal_uncertainty_m": horizontal_error,
        "vertical_uncertainty_m": vertical_error,
        "location_quality": quality,
        "quality_note": f"Estimated via GNSS + Swath Offset with {quality.lower()} confidence."
    }
