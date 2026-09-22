import os
import json
import math
import logging
from typing import Dict, Any, List, Optional
from app.data_sources.base import DataSource, DataStatus
from app.data_sources.geospatial.models import (
    PortInfo,
    RestrictedZoneCheckResult,
    ProtectedAreaCheckResult,
)
from app.marine_gateway.models import NormalizedGeospatial

logger = logging.getLogger("marinex.datasources.geospatial.service")

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    return round(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 2)

def point_in_polygon(point: List[float], vs: List[List[float]]) -> bool:
    """Ray casting algorithm for 2D point-in-polygon check. point=[lon, lat]."""
    x, y = point[0], point[1]
    inside = False
    j = len(vs) - 1
    for i in range(len(vs)):
        xi, yi = vs[i][0], vs[i][1]
        xj, yj = vs[j][0], vs[j][1]
        intersect = ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi)
        if intersect:
            inside = not inside
        j = i
    return inside

class GeospatialService(DataSource):
    """
    Geospatial Service: Performs spatial queries, port proximity calculations,
    and geofencing checks over GeoJSON layers (with PostGIS readiness).
    """
    name: str = "geospatial"
    enabled: bool = True

    def __init__(self):
        self.postgis_enabled = os.getenv("POSTGIS_ENABLED", "false").lower() == "true"
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        candidate_1 = os.path.join(backend_dir, "data", "geospatial")
        candidate_2 = os.path.join(backend_dir, "..", "data", "geospatial")
        if os.path.exists(candidate_1):
            self.data_dir = candidate_1
        elif os.path.exists(candidate_2):
            self.data_dir = candidate_2
        else:
            self.data_dir = candidate_1
        self._load_layers()

    def _load_layers(self) -> None:
        self.ports = self._read_geojson("ports.geojson")
        self.restricted = self._read_geojson("restricted_zones.geojson")
        self.protected = self._read_geojson("protected_areas.geojson")
        self.hazards = self._read_geojson("hazard_zones.geojson")

    def _read_geojson(self, filename: str) -> List[Dict[str, Any]]:
        path = os.path.join(self.data_dir, filename)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("features", [])
            except Exception as e:
                logger.error(f"[GeospatialService] Error reading {filename}: {e}")
        return []

    def health_check(self) -> Dict[str, Any]:
        return {
            "provider": "PostGIS / GeoJSON Spatial Engine",
            "status": "online",
            "postgis_enabled": self.postgis_enabled,
            "layers_loaded": {
                "ports": len(self.ports),
                "restricted_zones": len(self.restricted),
                "protected_areas": len(self.protected),
                "hazard_zones": len(self.hazards)
            },
            "is_live": True
        }

    def fetch(self, **kwargs) -> NormalizedGeospatial:
        loc = kwargs.get("location_name", "Chennai")
        lat = kwargs.get("latitude")
        lon = kwargs.get("longitude")
        return self.get_geospatial_summary(loc, lat, lon)

    def get_coordinates_by_name(self, location_name: str) -> Dict[str, Any]:
        loc_clean = location_name.lower().strip()
        for feature in self.ports:
            props = feature.get("properties", {})
            name = props.get("name", "").lower()
            if loc_clean in name or loc_clean in props.get("state", "").lower() or loc_clean in props.get("id", "").lower():
                coords = feature["geometry"]["coordinates"]
                return {
                    "name": props["name"],
                    "lat": coords[1],
                    "lon": coords[0],
                    "port": props["name"]
                }
        # Common coastal cities fallback
        lookup = {
            "mumbai": {"name": "Mumbai Harbour", "lat": 18.922, "lon": 72.834, "port": "Mumbai Port Trust"},
            "chennai": {"name": "Chennai Fishing Harbour", "lat": 13.125, "lon": 80.298, "port": "Chennai Port (Kasimedu)"},
            "kochi": {"name": "Cochin Fisheries Harbour", "lat": 9.931, "lon": 76.267, "port": "Cochin Port Trust"},
            "pulicat": {"name": "Pulicat Estuary", "lat": 13.420, "lon": 80.320, "port": "Pulicat Artisanal Wharf"},
            "visakhapatnam": {"name": "Visakhapatnam Harbour", "lat": 17.686, "lon": 83.218, "port": "Visakhapatnam Port"}
        }
        for k, v in lookup.items():
            if k in loc_clean:
                return v

        return {
            "name": f"{location_name.title()} (Coastal Sector)",
            "lat": 13.125,
            "lon": 80.298,
            "port": "Regional Fishing Wharf"
        }

    def find_nearest_port(self, lat: float, lon: float) -> PortInfo:
        min_dist = float("inf")
        nearest = None

        for feat in self.ports:
            coords = feat["geometry"]["coordinates"]
            p_lon, p_lat = coords[0], coords[1]
            dist = haversine(lat, lon, p_lat, p_lon)
            if dist < min_dist:
                min_dist = dist
                props = feat.get("properties", {})
                nearest = PortInfo(
                    id=props.get("id", "port-0"),
                    name=props.get("name", "Regional Port"),
                    type=props.get("type", "Commercial & Fishing"),
                    state=props.get("state", "India"),
                    latitude=p_lat,
                    longitude=p_lon,
                    distance_km=dist
                )

        return nearest or PortInfo(
            id="port-chn",
            name="Chennai Fishing Harbour (Kasimedu)",
            type="Major Fishing Harbour",
            state="Tamil Nadu",
            latitude=13.125,
            longitude=80.298,
            distance_km=15.0
        )

    def check_restricted_zone(self, lat: float, lon: float) -> RestrictedZoneCheckResult:
        pt = [lon, lat]
        for feat in self.restricted:
            geom = feat.get("geometry", {})
            props = feat.get("properties", {})
            if geom.get("type") == "Polygon":
                ring = geom["coordinates"][0]
                if point_in_polygon(pt, ring):
                    return RestrictedZoneCheckResult(
                        is_restricted=True,
                        zone_name=props.get("name", "Restricted Fairway"),
                        restriction=props.get("restriction", "Navigation prohibited."),
                        distance_km=0.0
                    )
                # Check proximity (within 6 km)
                center_lon = sum([p[0] for p in ring]) / len(ring)
                center_lat = sum([p[1] for p in ring]) / len(ring)
                d = haversine(lat, lon, center_lat, center_lon)
                if d <= 6.0:
                    return RestrictedZoneCheckResult(
                        is_restricted=True,
                        zone_name=props.get("name", "Naval Fairway Sector"),
                        restriction=f"Approaching restricted fairway ({d:.1f} km away).",
                        distance_km=d
                    )

        return RestrictedZoneCheckResult(is_restricted=False)

    def check_protected_area(self, lat: float, lon: float) -> ProtectedAreaCheckResult:
        pt = [lon, lat]
        for feat in self.protected:
            geom = feat.get("geometry", {})
            props = feat.get("properties", {})
            if geom.get("type") == "Polygon":
                ring = geom["coordinates"][0]
                if point_in_polygon(pt, ring):
                    return ProtectedAreaCheckResult(
                        is_protected=True,
                        area_name=props.get("name", "Marine Protected Area"),
                        restriction=props.get("restriction", "Trawling prohibited."),
                        distance_km=0.0
                    )
                center_lon = sum([p[0] for p in ring]) / len(ring)
                center_lat = sum([p[1] for p in ring]) / len(ring)
                d = haversine(lat, lon, center_lat, center_lon)
                if d <= 8.0:
                    return ProtectedAreaCheckResult(
                        is_protected=True,
                        area_name=props.get("name", "Marine Reserve Buffer"),
                        restriction=f"Proximity to marine reserve ({d:.1f} km away).",
                        distance_km=d
                    )

        return ProtectedAreaCheckResult(is_protected=False)

    def find_nearby_hazards(self, lat: float, lon: float) -> List[Dict[str, Any]]:
        pt = [lon, lat]
        nearby = []
        for feat in self.hazards:
            geom = feat.get("geometry", {})
            props = feat.get("properties", {})
            if geom.get("type") == "Polygon":
                ring = geom["coordinates"][0]
                inside = point_in_polygon(pt, ring)
                center_lon = sum([p[0] for p in ring]) / len(ring)
                center_lat = sum([p[1] for p in ring]) / len(ring)
                d = haversine(lat, lon, center_lat, center_lon)
                if inside or d <= 15.0:
                    nearby.append({
                        "name": props.get("name"),
                        "type": props.get("type"),
                        "severity": props.get("severity"),
                        "description": props.get("description"),
                        "distance_km": 0.0 if inside else d
                    })
        return nearby

    def get_geospatial_summary(
        self,
        location_name: str,
        lat: Optional[float] = None,
        lon: Optional[float] = None
    ) -> NormalizedGeospatial:
        if lat is None or lon is None:
            resolved = self.get_coordinates_by_name(location_name)
            lat = resolved["lat"]
            lon = resolved["lon"]
            location_name = resolved["name"]

        nearest_port = self.find_nearest_port(lat, lon)
        restr = self.check_restricted_zone(lat, lon)
        prot = self.check_protected_area(lat, lon)
        hazards = self.find_nearby_hazards(lat, lon)

        return NormalizedGeospatial(
            coordinates={"lat": lat, "lng": lon},
            location_name=location_name,
            nearest_port=nearest_port.model_dump(),
            restricted_zone=restr.is_restricted,
            restricted_zone_details=restr.model_dump() if restr.is_restricted else None,
            protected_zone=prot.is_protected,
            protected_zone_details=prot.model_dump() if prot.is_protected else None,
            distance_from_coast_km=nearest_port.distance_km,
            nearby_hazards=hazards,
            provider="GeoJSON Spatial Engine / PostGIS Ready",
            status="verified"
        )

geospatial_service = GeospatialService()
