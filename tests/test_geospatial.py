"""
Unit tests for Geospatial Georeferencing, Trajectory, and Uncertainty
"""

import pytest
import os

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from geospatial.coordinates import validate_coordinates, parse_crs_identifier
from geospatial.trajectory import generate_survey_trajectory
from geospatial.uncertainty import calculate_spatial_uncertainty
from geospatial.georeferencing import SonarGeoreferencer


def test_coordinate_validation():
    ok, err = validate_coordinates(18.9220, 72.8347)
    assert ok is True
    assert err is None

    bad_lat, err1 = validate_coordinates(95.0, 72.8)
    assert bad_lat is False
    assert "Latitude" in err1

    bad_lon, err2 = validate_coordinates(18.0, 195.0)
    assert bad_lon is False
    assert "Longitude" in err2


def test_survey_trajectory():
    nav_pts = [
        {"latitude": 18.9220, "longitude": 72.8347},
        {"latitude": 18.9230, "longitude": 72.8357},
        {"latitude": 18.9240, "longitude": 72.8367}
    ]
    traj = generate_survey_trajectory(nav_pts)
    assert traj["geometry"]["type"] == "LineString"
    assert len(traj["geometry"]["coordinates"]) == 3
    assert traj["properties"]["total_distance_m"] > 0
    assert traj["properties"]["bounds"]["min_lat"] == 18.9220


def test_spatial_uncertainty():
    unc = calculate_spatial_uncertainty(
        nav_data={"depth": 30.0, "is_demo_gps": False},
        cross_track_m=20.0,
        motion_status="FULL"
    )
    assert unc["location_quality"] == "EXACT / HIGH QUALITY"
    assert unc["horizontal_uncertainty_m"] > 0
    assert unc["vertical_uncertainty_m"] > 0


def test_sonar_georeferencer():
    georef = SonarGeoreferencer(swath_range_m=50.0)
    nav_data = {
        "latitude": 18.9220,
        "longitude": 72.8347,
        "heading": 90.0,
        "depth": 25.0,
        "is_demo_gps": False
    }
    det = {"bbox": {"x1": 800, "y1": 400, "x2": 850, "y2": 450}}

    res = georef.georeference_detection(
        det=det,
        nav_data=nav_data,
        img_width=1280,
        img_height=800
    )
    assert res["latitude"] != nav_data["latitude"] or res["longitude"] != nav_data["longitude"]
    assert "location_quality" in res
    assert "horizontal_uncertainty_m" in res
