import math
from typing import Dict, Any
from langchain_core.tools import tool
from app.data_sources.geospatial.service import geospatial_service, haversine

@tool
def get_coordinates(location: str = "chennai") -> Dict[str, Any]:
    """Resolves a coastal location name to latitude and longitude coordinates."""
    coords = geospatial_service.get_coordinates_by_name(location)
    return {
        "location": location,
        "name": coords["name"],
        "lat": coords["lat"],
        "lon": coords["lon"],
        "port": coords.get("port", "Coastal Harbour")
    }

@tool
def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates the maritime distance in kilometers between two points."""
    return haversine(lat1, lon1, lat2, lon2)

@tool
def check_restricted_zone(lat: float, lon: float) -> Dict[str, Any]:
    """
    Checks if given coordinates fall inside or near restricted naval channels,
    commercial anchorages, or security fairways.
    """
    res = geospatial_service.check_restricted_zone(lat, lon)
    return {
        "is_restricted": res.is_restricted,
        "zone_name": res.zone_name,
        "distance_km": res.distance_km,
        "restriction": res.restriction
    }

@tool
def check_protected_area(lat: float, lon: float) -> Dict[str, Any]:
    """
    Checks if given coordinates intersect with Marine Protected Areas (MPAs),
    coral reef sanctuaries, or estuarine nursery habitats.
    """
    res = geospatial_service.check_protected_area(lat, lon)
    return {
        "is_protected": res.is_protected,
        "area_name": res.area_name,
        "distance_km": res.distance_km,
        "restriction": res.restriction
    }

@tool
def find_nearest_port(lat: float, lon: float) -> Dict[str, Any]:
    """Finds the nearest major port or fish landing center to given coordinates."""
    port = geospatial_service.find_nearest_port(lat, lon)
    return {
        "port_name": port.name,
        "distance_km": port.distance_km,
        "coordinates": {"lat": port.latitude, "lon": port.longitude}
    }
