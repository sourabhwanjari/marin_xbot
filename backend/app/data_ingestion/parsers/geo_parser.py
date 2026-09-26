import re
import math
import logging
from typing import Optional, Tuple, Dict, Any, List

logger = logging.getLogger("marinex.ingestion.parsers.geo")

class GeoSpatialParser:
    """
    Geospatial validation and parsing utilities for marine coordinates,
    distances, and PostGIS/GeoJSON geometries.
    """

    @staticmethod
    def is_valid_coordinate(latitude: Optional[float], longitude: Optional[float]) -> bool:
        """Strict validation of geographic latitude and longitude bounds."""
        if latitude is None or longitude is None:
            return False
        try:
            lat = float(latitude)
            lon = float(longitude)
            return (-90.0 <= lat <= 90.0) and (-180.0 <= lon <= 180.0)
        except (ValueError, TypeError):
            return False

    @staticmethod
    def parse_coordinate(coord_val: Any) -> Optional[float]:
        """
        Parses coordinates from strings with degrees, minutes, direction suffixes:
        e.g., '18.922° N', '72.834 E', '18° 55.3\' N', or simple '18.922'.
        """
        if coord_val is None:
            return None
        if isinstance(coord_val, (int, float)):
            return float(coord_val)

        s = str(coord_val).strip()
        if not s:
            return None

        # Check for direction suffix
        is_negative = False
        upper = s.upper()
        if "S" in upper or "W" in upper:
            is_negative = True

        # Extract decimal float if present
        m = re.search(r"[-+]?\d*\.?\d+", s)
        if m:
            val = float(m.group(0))
            if is_negative and val > 0:
                val = -val
            return val
        return None

    @staticmethod
    def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculates geodesic distance between two points on WGS84 ellipsoid (km)."""
        r = 6371.0  # Earth mean radius in kilometers
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return round(r * c, 2)

    @staticmethod
    def create_geojson_point(latitude: float, longitude: float) -> Dict[str, Any]:
        """Returns standard GeoJSON Point object."""
        return {
            "type": "Point",
            "coordinates": [longitude, latitude]  # GeoJSON is [lon, lat]
        }

    @staticmethod
    def parse_coordinate_string(coord_str: str) -> Tuple[Optional[float], Optional[float]]:
        """Parses coordinate pairs like '18.92N, 72.83E' or '18.92, 72.83'."""
        if not coord_str:
            return None, None
        parts = coord_str.split(",")
        if len(parts) == 2:
            return GeoSpatialParser.parse_coordinate(parts[0]), GeoSpatialParser.parse_coordinate(parts[1])
        return None, None

    @staticmethod
    def validate_coordinates(latitude: Optional[float], longitude: Optional[float]) -> Tuple[bool, Optional[str]]:
        """Validates coordinates and returns (is_valid, error_message)."""
        if latitude is None or longitude is None:
            return False, "Coordinates cannot be None"
        try:
            lat = float(latitude)
            lon = float(longitude)
            if not (-90.0 <= lat <= 90.0):
                return False, f"Latitude {lat} out of valid bounds [-90, 90]"
            if not (-180.0 <= lon <= 180.0):
                return False, f"Longitude {lon} out of valid bounds [-180, 180]"
            return True, None
        except (ValueError, TypeError) as e:
            return False, str(e)

    @staticmethod
    def create_geojson_polygon(coordinates: List[List[float]]) -> Dict[str, Any]:
        """Returns standard GeoJSON Polygon object."""
        return {
            "type": "Polygon",
            "coordinates": [coordinates]
        }

