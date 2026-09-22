"""
Sonar Geotagging & Metadata Parser Engine
Extracts navigation headers (latitude, longitude, heading, depth, timestamp)
from uploaded metadata (JSON or CSV) and estimates approximate object coordinates.
"""

import json
import csv
import io
import math
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple


# Default fallback coordinates for demonstration (Arabian Sea / Coastal Survey Zone)
DEFAULT_DEMO_LAT = 18.5204
DEFAULT_DEMO_LON = 73.8567
DEFAULT_DEMO_HEADING = 90.0
DEFAULT_DEMO_DEPTH = 32.5


def parse_metadata_file(content_bytes: bytes, filename: str) -> Dict[str, Any]:
    """
    Parses optional uploaded metadata file (JSON or CSV).
    Returns normalized dictionary of navigation attributes.
    """
    filename_lower = filename.lower()
    
    if filename_lower.endswith(".json"):
        try:
            data = json.loads(content_bytes.decode("utf-8"))
            if isinstance(data, list) and len(data) > 0:
                data = data[0]
            return {
                "latitude": float(data.get("latitude", DEFAULT_DEMO_LAT)),
                "longitude": float(data.get("longitude", DEFAULT_DEMO_LON)),
                "heading": float(data.get("heading", DEFAULT_DEMO_HEADING)),
                "depth": float(data.get("depth", DEFAULT_DEMO_DEPTH)),
                "timestamp": data.get("timestamp", datetime.utcnow().isoformat()),
                "ping_id": data.get("ping_id", 1001),
                "source": "metadata_json",
                "is_demo_gps": False
            }
        except Exception as e:
            print(f"[SONAR-AI] Warning: Failed to parse metadata JSON: {e}")
            
    elif filename_lower.endswith(".csv"):
        try:
            text = content_bytes.decode("utf-8")
            reader = csv.DictReader(io.StringIO(text))
            rows = list(reader)
            if rows:
                row = rows[0]
                return {
                    "latitude": float(row.get("latitude", row.get("lat", DEFAULT_DEMO_LAT))),
                    "longitude": float(row.get("longitude", row.get("lon", row.get("lng", DEFAULT_DEMO_LON)))),
                    "heading": float(row.get("heading", row.get("yaw", DEFAULT_DEMO_HEADING))),
                    "depth": float(row.get("depth", DEFAULT_DEMO_DEPTH)),
                    "timestamp": row.get("timestamp", datetime.utcnow().isoformat()),
                    "ping_id": row.get("ping_id", 1001),
                    "source": "metadata_csv",
                    "is_demo_gps": False
                }
        except Exception as e:
            print(f"[SONAR-AI] Warning: Failed to parse metadata CSV: {e}")

    # Fallback to demo navigation headers
    return {
        "latitude": DEFAULT_DEMO_LAT,
        "longitude": DEFAULT_DEMO_LON,
        "heading": DEFAULT_DEMO_HEADING,
        "depth": DEFAULT_DEMO_DEPTH,
        "timestamp": datetime.utcnow().isoformat(),
        "ping_id": 1001,
        "source": "demo_defaults",
        "is_demo_gps": True
    }


def estimate_object_coordinates(
    nav_data: Dict[str, Any],
    bbox: Dict[str, int],
    img_width: int,
    img_height: int,
    swath_range_meters: float = 50.0
) -> Tuple[float, float, str]:
    """
    Computes approximate spatial coordinates for detected objects relative to towfish trackline.
    
    NOTE:
    In the absence of calibrated slant-range correction and acoustic positioning (USBL),
    this produces an 'Approximate Image-Level Location' offset by swath width and pixel position.
    """
    center_x = (bbox["x1"] + bbox["x2"]) / 2.0
    center_y = (bbox["y1"] + bbox["y2"]) / 2.0

    # Cross-track offset in meters (port vs starboard from center trackline)
    # Center pixel of width corresponds to nadir/towfish path
    rel_x = (center_x - (img_width / 2.0)) / max(1.0, img_width / 2.0)
    cross_track_m = rel_x * (swath_range_meters / 2.0)

    # Along-track offset in meters
    rel_y = (center_y - (img_height / 2.0)) / max(1.0, img_height / 2.0)
    along_track_m = -rel_y * 10.0  # approximate 10m track length per frame

    base_lat = nav_data["latitude"]
    base_lon = nav_data["longitude"]
    heading_rad = math.radians(nav_data.get("heading", 0.0))

    # Simple flat-earth approximation for micro-offsets (~111,111 meters per degree)
    # Rotate by vehicle heading
    offset_north = (along_track_m * math.cos(heading_rad)) - (cross_track_m * math.sin(heading_rad))
    offset_east = (along_track_m * math.sin(heading_rad)) + (cross_track_m * math.cos(heading_rad))

    delta_lat = offset_north / 111111.0
    cos_lat = math.cos(math.radians(base_lat))
    delta_lon = offset_east / (111111.0 * max(0.01, cos_lat))

    obj_lat = round(base_lat + delta_lat, 6)
    obj_lon = round(base_lon + delta_lon, 6)

    if nav_data.get("is_demo_gps", False):
        loc_type = "DEMO LOCATION (Estimated Swath Offset)"
    else:
        loc_type = "Approximate Image-Level Location"

    return obj_lat, obj_lon, loc_type


def geotag_detections(
    detections: List[Dict[str, Any]],
    nav_data: Dict[str, Any],
    img_width: int,
    img_height: int
) -> List[Dict[str, Any]]:
    """Enriches all detections with estimated geographic coordinates and tracking metadata."""
    geotagged = []
    for det in detections:
        det_copy = dict(det)
        lat, lon, loc_type = estimate_object_coordinates(
            nav_data=nav_data,
            bbox=det["bbox"],
            img_width=img_width,
            img_height=img_height
        )
        det_copy.update({
            "latitude": lat,
            "longitude": lon,
            "location_type": loc_type,
            "depth_m": nav_data.get("depth", DEFAULT_DEMO_DEPTH),
            "heading_deg": nav_data.get("heading", DEFAULT_DEMO_HEADING),
            "timestamp": nav_data.get("timestamp", datetime.utcnow().isoformat())
        })
        geotagged.append(det_copy)

    return geotagged
