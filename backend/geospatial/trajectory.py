"""
SONAR-AI Trajectory Module
Extracts towfish / survey vessel trackline geometries and computes track statistics.
"""

from typing import List, Dict, Any
import math


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two points in meters."""
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2) + (math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))
    return R * c


def generate_survey_trajectory(nav_points: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Constructs a survey track GeoJSON LineString and summary metrics from navigation points.
    """
    if not nav_points:
        return {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": []},
            "properties": {
                "point_count": 0,
                "total_distance_m": 0.0,
                "bounds": None
            }
        }

    coordinates = []
    total_dist = 0.0
    lats = []
    lons = []

    prev_pt = None
    for pt in nav_points:
        lat = pt.get("latitude")
        lon = pt.get("longitude")
        if lat is not None and lon is not None:
            lats.append(lat)
            lons.append(lon)
            coordinates.append([lon, lat])

            if prev_pt is not None:
                total_dist += haversine_distance_meters(
                    prev_pt["lat"], prev_pt["lon"], lat, lon
                )
            prev_pt = {"lat": lat, "lon": lon}

    bounds = None
    if lats and lons:
        bounds = {
            "min_lat": min(lats),
            "max_lat": max(lats),
            "min_lon": min(lons),
            "max_lon": max(lons)
        }

    return {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": coordinates
        },
        "properties": {
            "point_count": len(coordinates),
            "total_distance_m": round(total_dist, 1),
            "bounds": bounds
        }
    }
