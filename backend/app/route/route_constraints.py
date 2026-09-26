import math
import logging
from typing import List, Tuple, Dict, Any, Optional

logger = logging.getLogger("marinex.route.constraints")

class RouteConstraints:
    """
    Deterministic spatial constraints and polygon collision detection engine for marine routes.
    Avoids restricted maritime fairways, naval security channels, MPAs, and hazard polygons.
    """

    @staticmethod
    def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Geodesic distance between two points in kilometers."""
        r = 6371.0
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlam = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0)**2
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return round(r * c, 2)

    @staticmethod
    def point_in_polygon(lat: float, lon: float, polygon: List[Tuple[float, float]]) -> bool:
        """
        Ray-casting algorithm to test whether point (lat, lon) is strictly inside a polygon.
        Polygon is a list of (lat, lon) vertices.
        """
        n = len(polygon)
        if n < 3:
            return False

        inside = False
        p1_lat, p1_lon = polygon[0]
        for i in range(1, n + 1):
            p2_lat, p2_lon = polygon[i % n]
            if lon > min(p1_lon, p2_lon):
                if lon <= max(p1_lon, p2_lon):
                    if lat <= max(p1_lat, p2_lat):
                        if p1_lon != p2_lon:
                            lat_inters = (lon - p1_lon) * (p2_lat - p1_lat) / (p2_lon - p1_lon) + p1_lat
                            if p1_lat == p2_lat or lat <= lat_inters:
                                inside = not inside
            p1_lat, p1_lon = p2_lat, p2_lon

        return inside

    @staticmethod
    def _segments_intersect(
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        p3: Tuple[float, float],
        p4: Tuple[float, float]
    ) -> bool:
        """Returns True if line segment p1-p2 intersects line segment p3-p4."""
        def ccw(a, b, c):
            return (c[0] - a[0]) * (b[1] - a[1]) > (b[0] - a[0]) * (c[1] - a[1])

        return (ccw(p1, p3, p4) != ccw(p2, p3, p4)) and (ccw(p1, p2, p3) != ccw(p1, p2, p4))

    @classmethod
    def segment_intersects_polygon(
        cls,
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        polygon: List[Tuple[float, float]]
    ) -> bool:
        """
        Tests whether route segment p1->p2 intersects or crosses any part of the polygon.
        """
        n = len(polygon)
        if n < 3:
            return False

        # Fast bounding box rejection test
        poly_lats = [pt[0] for pt in polygon]
        poly_lons = [pt[1] for pt in polygon]
        min_p_lat, max_p_lat = min(poly_lats), max(poly_lats)
        min_p_lon, max_p_lon = min(poly_lons), max(poly_lons)

        seg_min_lat = min(p1[0], p2[0])
        seg_max_lat = max(p1[0], p2[0])
        seg_min_lon = min(p1[1], p2[1])
        seg_max_lon = max(p1[1], p2[1])

        if (seg_max_lat < min_p_lat or seg_min_lat > max_p_lat or
            seg_max_lon < min_p_lon or seg_min_lon > max_p_lon):
            return False

        # If either endpoint is inside, it intersects
        if cls.point_in_polygon(p1[0], p1[1], polygon) or cls.point_in_polygon(p2[0], p2[1], polygon):
            return True

        # Check edge intersection
        for i in range(n):
            edge_p1 = polygon[i]
            edge_p2 = polygon[(i + 1) % n]
            if cls._segments_intersect(p1, p2, edge_p1, edge_p2):
                return True

        # Sample midpoints for curved or concave penetration
        mid_lat = (p1[0] + p2[0]) / 2.0
        mid_lon = (p1[1] + p2[1]) / 2.0
        if cls.point_in_polygon(mid_lat, mid_lon, polygon):
            return True

        return False

    @classmethod
    def evaluate_route_path(
        cls,
        waypoints: List[List[float]],
        restricted_areas: List[Dict[str, Any]],
        hazard_areas: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluates a complete sequence of waypoints [[lat, lon], ...] against restricted & hazard areas.
        """
        restricted_violations = []
        hazards_intersected = []
        hazards_avoided = []
        restricted_avoided = []

        total_distance = 0.0
        for i in range(len(waypoints) - 1):
            p1 = (waypoints[i][0], waypoints[i][1])
            p2 = (waypoints[i + 1][0], waypoints[i + 1][1])
            total_distance += cls.haversine_km(p1[0], p1[1], p2[0], p2[1])

            # Check restricted areas
            for area in restricted_areas:
                area_name = area.get("name", "Restricted Area")
                poly = area.get("coordinates", [])
                if poly:
                    coords = [(pt[0], pt[1]) for pt in poly]
                    if cls.segment_intersects_polygon(p1, p2, coords):
                        if area_name not in restricted_violations:
                            restricted_violations.append(area_name)
                    else:
                        if area_name not in restricted_avoided and area_name not in restricted_violations:
                            restricted_avoided.append(area_name)

            # Check hazard areas
            for hazard in hazard_areas:
                hazard_name = hazard.get("name", "Hazard Area")
                poly = hazard.get("coordinates", [])
                if poly:
                    coords = [(pt[0], pt[1]) for pt in poly]
                    if cls.segment_intersects_polygon(p1, p2, coords):
                        if hazard_name not in hazards_intersected:
                            hazards_intersected.append(hazard_name)
                    else:
                        if hazard_name not in hazards_avoided and hazard_name not in hazards_intersected:
                            hazards_avoided.append(hazard_name)

        return {
            "total_distance_km": round(total_distance, 2),
            "restricted_violations": restricted_violations,
            "hazards_intersected": hazards_intersected,
            "restricted_avoided": [r for r in restricted_avoided if r not in restricted_violations],
            "hazards_avoided": [h for h in hazards_avoided if h not in hazards_intersected],
            "is_clear_of_restricted": len(restricted_violations) == 0,
            "is_clear_of_hazards": len(hazards_intersected) == 0
        }

route_constraints = RouteConstraints()
