"""
SONAR-AI Motion Compensation Module
Evaluates and applies motion corrections for towfish attitude dynamics: heave, pitch, roll, and heading.

SCIENTIFIC INTEGRITY RULE:
Do NOT fabricate motion parameters. If vehicle sensor telemetry lacks heave, pitch,
or roll, explicitly return PARTIAL or UNAVAILABLE status with detailed diagnostics.
"""

from typing import Dict, Any, Optional, Tuple
import numpy as np


class MotionCompensationEngine:
    """
    Evaluates towfish/vessel attitude telemetry and computes geometric adjustments
    for side scan sonar imagery when attitude sensors are available.
    """

    def evaluate_motion_availability(self, nav_point: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inspects motion telemetry keys in navigation record.
        Returns explicit parameter availability and diagnostic status.
        """
        has_heave = nav_point.get("heave") is not None
        has_pitch = nav_point.get("pitch") is not None
        has_roll = nav_point.get("roll") is not None
        has_heading = (nav_point.get("heading") is not None) or (nav_point.get("yaw") is not None)

        missing_parameters = []
        if not has_heave:
            missing_parameters.append("heave")
        if not has_pitch:
            missing_parameters.append("pitch")
        if not has_roll:
            missing_parameters.append("roll")
        if not has_heading:
            missing_parameters.append("heading")

        if len(missing_parameters) == 0:
            status = "FULL"
            summary = "Full motion compensation available (heave, pitch, roll, heading active)."
        elif len(missing_parameters) == 4:
            status = "UNAVAILABLE"
            summary = "Motion Compensation: UNAVAILABLE. Attitude sensor telemetry missing from survey dataset."
        else:
            status = "PARTIAL"
            missing_str = ", ".join(missing_parameters)
            summary = f"Motion Compensation: PARTIAL. Missing parameters: {missing_str}."

        return {
            "status": status,
            "summary": summary,
            "has_heave": has_heave,
            "has_pitch": has_pitch,
            "has_roll": has_roll,
            "has_heading": has_heading,
            "missing_parameters": missing_parameters,
            "heave_val": float(nav_point["heave"]) if has_heave else None,
            "pitch_deg": float(nav_point["pitch"]) if has_pitch else None,
            "roll_deg": float(nav_point["roll"]) if has_roll else None,
            "heading_deg": float(nav_point.get("heading") or nav_point.get("yaw") or 0.0) if has_heading else None,
        }

    def compute_geometric_offset(
        self,
        pixel_x: float,
        pixel_y: float,
        img_width: int,
        img_height: int,
        motion_eval: Dict[str, Any],
        slant_range_m: float = 50.0
    ) -> Tuple[float, float, Dict[str, Any]]:
        """
        Computes along-track and cross-track ground offsets adjusted for vehicle attitude.
        If roll/pitch telemetry is missing, reports uncompensated offsets with explicit uncertainty.
        """
        # Center represents nadir trackline
        norm_cross = (pixel_x - (img_width / 2.0)) / max(1.0, (img_width / 2.0))
        norm_along = (pixel_y - (img_height / 2.0)) / max(1.0, (img_height / 2.0))

        # Base nominal offsets (meters)
        raw_cross_track_m = norm_cross * (slant_range_m / 2.0)
        raw_along_track_m = -norm_along * 10.0

        corrected_cross_m = raw_cross_track_m
        corrected_along_m = raw_along_track_m
        corrections_applied = []

        # If roll telemetry exists: correct for roll beam deflection
        if motion_eval.get("has_roll") and motion_eval.get("roll_deg") is not None:
            roll_rad = np.radians(motion_eval["roll_deg"])
            # First order roll lever-arm displacement
            corrected_cross_m = raw_cross_track_m * np.cos(roll_rad)
            corrections_applied.append(f"Roll correction ({motion_eval['roll_deg']:.1f}°)")

        # If pitch telemetry exists: correct for along-track beam sweep
        if motion_eval.get("has_pitch") and motion_eval.get("pitch_deg") is not None:
            pitch_rad = np.radians(motion_eval["pitch_deg"])
            corrected_along_m = raw_along_track_m * np.cos(pitch_rad)
            corrections_applied.append(f"Pitch correction ({motion_eval['pitch_deg']:.1f}°)")

        meta = {
            "motion_status": motion_eval["status"],
            "corrections_applied": corrections_applied,
            "uncompensated_parameters": motion_eval["missing_parameters"],
            "raw_cross_m": round(raw_cross_track_m, 2),
            "raw_along_m": round(raw_along_track_m, 2),
            "corrected_cross_m": round(corrected_cross_m, 2),
            "corrected_along_m": round(corrected_along_m, 2)
        }

        return corrected_cross_m, corrected_along_m, meta
