"""
SONAR-AI Georeferencing Engine
Calculates geographic coordinates (latitude, longitude, depth) for detected sonar anomalies
relative to the towfish trackline, heading, swath geometry, and motion compensation.
"""

from typing import List, Dict, Any, Optional
import math
import numpy as np

from .coordinates import validate_coordinates
from .uncertainty import calculate_spatial_uncertainty
from sonar_processing.motion_compensation import MotionCompensationEngine


class SonarGeoreferencer:
    """
    Translates image pixel bounding box centers into geographic WGS84 positions.
    """

    def __init__(self, swath_range_m: float = 50.0):
        self.swath_range_m = swath_range_m
        self.motion_engine = MotionCompensationEngine()

    def georeference_detection(
        self,
        det: Dict[str, Any],
        nav_data: Dict[str, Any],
        img_width: int,
        img_height: int
    ) -> Dict[str, Any]:
        """
        Calculates geodetic coordinates for a single detection bounding box.
        """
        bbox = det["bbox"]
        center_x = (bbox["x1"] + bbox["x2"]) / 2.0
        center_y = (bbox["y1"] + bbox["y2"]) / 2.0

        # Evaluate motion telemetry
        motion_eval = self.motion_engine.evaluate_motion_availability(nav_data)

        # Compute ground offsets with motion compensation
        cross_track_m, along_track_m, motion_meta = self.motion_engine.compute_geometric_offset(
            pixel_x=center_x,
            pixel_y=center_y,
            img_width=img_width,
            img_height=img_height,
            motion_eval=motion_eval,
            slant_range_m=self.swath_range_m
        )

        base_lat = float(nav_data.get("latitude", 18.9220))
        base_lon = float(nav_data.get("longitude", 72.8347))
        heading_deg = float(nav_data.get("heading") or nav_data.get("yaw") or 0.0)
        heading_rad = math.radians(heading_deg)

        # Rotate along-track and cross-track ground offsets into North/East vectors
        offset_north = (along_track_m * math.cos(heading_rad)) - (cross_track_m * math.sin(heading_rad))
        offset_east = (along_track_m * math.sin(heading_rad)) + (cross_track_m * math.cos(heading_rad))

        # WGS84 spherical geodetic displacement (~111,139 meters per degree latitude)
        delta_lat = offset_north / 111139.0
        cos_lat = math.cos(math.radians(base_lat))
        delta_lon = offset_east / (111139.0 * max(0.01, cos_lat))

        obj_lat = round(base_lat + delta_lat, 7)
        obj_lon = round(base_lon + delta_lon, 7)

        # Calculate spatial uncertainty & quality
        uncertainty = calculate_spatial_uncertainty(
            nav_data=nav_data,
            cross_track_m=cross_track_m,
            motion_status=motion_eval["status"],
            swath_range_m=self.swath_range_m
        )

        depth = float(nav_data.get("depth", 25.0))

        return {
            "latitude": obj_lat,
            "longitude": obj_lon,
            "depth": depth,
            "cross_track_m": round(cross_track_m, 2),
            "along_track_m": round(along_track_m, 2),
            "location_quality": uncertainty["location_quality"],
            "horizontal_uncertainty_m": uncertainty["horizontal_uncertainty_m"],
            "vertical_uncertainty_m": uncertainty["vertical_uncertainty_m"],
            "motion_compensation": motion_meta
        }

    def georeference_all(
        self,
        detections: List[Dict[str, Any]],
        nav_data: Dict[str, Any],
        img_width: int,
        img_height: int
    ) -> List[Dict[str, Any]]:
        georeferenced = []
        for det in detections:
            res = self.georeference_detection(
                det=det,
                nav_data=nav_data,
                img_width=img_width,
                img_height=img_height
            )
            enriched = dict(det)
            enriched.update(res)
            georeferenced.append(enriched)
        return georeferenced
