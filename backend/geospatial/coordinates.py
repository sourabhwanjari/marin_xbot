"""
SONAR-AI Coordinates Module
Validates latitude/longitude bounds and manages Coordinate Reference Systems (CRS).
"""

from typing import Tuple, Dict, Any, Optional
import math


def validate_coordinates(lat: float, lon: float) -> Tuple[bool, Optional[str]]:
    """Checks whether latitude is in [-90, 90] and longitude is in [-180, 180]."""
    try:
        lat_f = float(lat)
        lon_f = float(lon)
        if not (-90.0 <= lat_f <= 90.0):
            return False, f"Latitude {lat_f} is out of physical range [-90.0, 90.0]."
        if not (-180.0 <= lon_f <= 180.0):
            return False, f"Longitude {lon_f} is out of physical range [-180.0, 180.0]."
        return True, None
    except (ValueError, TypeError) as e:
        return False, f"Non-numeric coordinate: {e}"


def parse_crs_identifier(crs_str: Optional[str]) -> Dict[str, Any]:
    """
    Parses CRS identifier or EPSG code.
    Defaults to EPSG:4326 (WGS 84 geographic).
    """
    if not crs_str:
        return {"code": 4326, "name": "WGS 84", "is_geographic": True}

    crs_upper = crs_str.upper()
    if "4326" in crs_upper or "WGS" in crs_upper:
        return {"code": 4326, "name": "WGS 84", "is_geographic": True}
    elif "3857" in crs_upper or "WEB MERCATOR" in crs_upper:
        return {"code": 3857, "name": "WGS 84 / Pseudo-Mercator", "is_geographic": False}
    elif "UTM" in crs_upper:
        return {"code": None, "name": crs_str, "is_geographic": False}

    return {"code": 4326, "name": crs_str, "is_geographic": True}
