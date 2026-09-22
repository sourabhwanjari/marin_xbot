"""
SONAR-AI Maps API Router
Provides spatial tracklines, georeferenced anomaly markers, and spatial bounds for GIS Leaflet mapping.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from database import get_db
from models_db import Mission, Detection, NavigationPoint
from geospatial.trajectory import generate_survey_trajectory

router = APIRouter(prefix="/api/maps", tags=["Maps"])


@router.get("/{mission_id}")
def get_mission_map_data(mission_id: int, db: Session = Depends(get_db)):
    """
    Returns spatial GeoJSON trackline and georeferenced anomaly markers
    formatted for interactive Leaflet display.
    """
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail=f"Mission {mission_id} not found.")

    # 1. Fetch navigation telemetry points
    nav_pts = db.query(NavigationPoint).filter(
        NavigationPoint.mission_id == mission_id
    ).order_by(NavigationPoint.id.asc()).all()

    nav_dicts = [p.to_dict() for p in nav_pts]
    trajectory_geojson = generate_survey_trajectory(nav_dicts)

    # 2. Fetch detections
    dets = db.query(Detection).filter(
        Detection.mission_id == mission_id
    ).all()

    markers = []
    lats = []
    lons = []

    for d in dets:
        if d.latitude is not None and d.longitude is not None:
            lats.append(d.latitude)
            lons.append(d.longitude)

            # Map marker category
            if d.verification_status == "VERIFIED":
                category = "Verified"
                color = "#22c55e"  # Green
            elif d.verification_status == "REJECTED":
                category = "Rejected"
                color = "#ef4444"  # Red
            elif d.verification_status == "MODIFIED":
                category = "Modified"
                color = "#06b6d4"  # Cyan
            elif d.ai_confidence >= 0.80:
                category = "AI Detection (High)"
                color = "#00f0ff"  # Bright Cyan
            else:
                category = "Needs Review"
                color = "#eab308"  # Yellow

            markers.append({
                "id": d.id,
                "class_name": d.class_name,
                "label": d.label,
                "latitude": d.latitude,
                "longitude": d.longitude,
                "depth": d.depth,
                "ai_confidence": d.ai_confidence,
                "ai_confidence_percent": int(round(d.ai_confidence * 100)),
                "anomaly_score": d.anomaly_score,
                "anomaly_score_percent": int(round(d.anomaly_score * 100)),
                "location_quality": d.location_quality,
                "horizontal_uncertainty_m": d.horizontal_uncertainty_m,
                "verification_status": d.verification_status,
                "category": category,
                "marker_color": color,
                "bbox": {"x1": d.bbox_x1, "y1": d.bbox_y1, "x2": d.bbox_x2, "y2": d.bbox_y2}
            })

    # Determine center & bounds
    center = [18.9220, 72.8347]  # Default Arabian Sea
    if lats and lons:
        center = [sum(lats) / len(lats), sum(lons) / len(lons)]
    elif nav_dicts:
        center = [nav_dicts[0]["latitude"], nav_dicts[0]["longitude"]]

    bounds = None
    if lats and lons:
        bounds = {
            "min_lat": min(lats) - 0.002,
            "max_lat": max(lats) + 0.002,
            "min_lon": min(lons) - 0.002,
            "max_lon": max(lons) + 0.002
        }
    elif trajectory_geojson["properties"].get("bounds"):
        tb = trajectory_geojson["properties"]["bounds"]
        bounds = {
            "min_lat": tb["min_lat"] - 0.002,
            "max_lat": tb["max_lat"] + 0.002,
            "min_lon": tb["min_lon"] - 0.002,
            "max_lon": tb["max_lon"] + 0.002
        }

    return {
        "mission_id": mission_id,
        "mission_name": mission.name,
        "crs": mission.crs,
        "center": center,
        "bounds": bounds,
        "trajectory": trajectory_geojson,
        "markers": markers,
        "marker_count": len(markers)
    }
