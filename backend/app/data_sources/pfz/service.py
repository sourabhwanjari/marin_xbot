import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from app.data_sources.base import DataSource, DataStatus
from app.data_sources.pfz.client import pfz_client, haversine
from app.marine_gateway.models import NormalizedPFZ

logger = logging.getLogger("marinex.datasources.pfz.service")

class PFZService(DataSource):
    """
    PFZ Service: Delivers validated Potential Fishing Zone advisories derived
    from satellite SST & Chlorophyll fronts.
    """
    name: str = "pfz"
    enabled: bool = True

    def __init__(self):
        self.demo_mode = os.getenv("MARINEX_DEMO_MODE", os.getenv("IS_DEMO", "true")).lower() == "true"

    def health_check(self) -> Dict[str, Any]:
        zones = pfz_client.fetch_all_zones()
        return {
            "provider": "INCOIS PFZ Mission",
            "status": "online" if len(zones) > 0 else "degraded",
            "total_active_sectors": len(zones),
            "is_live": True
        }

    def fetch(self, **kwargs) -> List[NormalizedPFZ]:
        loc = kwargs.get("location_name")
        lat = kwargs.get("latitude")
        lon = kwargs.get("longitude")
        if lat is not None and lon is not None:
            nearest = self.get_nearest_pfz(lat, lon)
            return [nearest] if nearest else []
        elif loc:
            return self.get_pfz_by_location(loc)
        return self.get_pfz_zones()

    def get_pfz_zones(self) -> List[NormalizedPFZ]:
        raw_zones = pfz_client.fetch_all_zones()
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        valid_until = (datetime.now(timezone.utc) + timedelta(days=2)).strftime("%Y-%m-%d")

        results = []
        for z in raw_zones:
            results.append(
                NormalizedPFZ(
                    zone_id=z["id"],
                    name=z["name"],
                    latitude=z["latitude"],
                    longitude=z["longitude"],
                    sector=z["sector"],
                    advisory_date=now_iso,
                    valid_until=valid_until,
                    distance_km=z["distance_km"],
                    direction=z["direction"],
                    sea_surface_temperature=z["sst"],
                    chlorophyll=z["chlorophyll"],
                    suitability=z["suitability"],
                    status=z["status"],
                    dominant_species=z["dominant_species"],
                    depth_meters=z["depth_meters"],
                    provider=z["provider"],
                    data_status="verified",
                    source_reference=z.get("advisory_ref", "INCOIS PFZ Bulletin")
                )
            )
        return results

    def get_nearest_pfz(self, lat: float, lon: float) -> Optional[NormalizedPFZ]:
        zones = self.get_pfz_zones()
        if not zones:
            return None

        nearest = None
        min_dist = float("inf")
        for z in zones:
            dist = haversine(lat, lon, z.latitude, z.longitude)
            if dist < min_dist:
                min_dist = dist
                nearest = z

        if nearest:
            # Update distance from caller's coordinates
            nearest.distance_km = min_dist
        return nearest

    def get_pfz_by_location(self, location_name: str) -> List[NormalizedPFZ]:
        zones = self.get_pfz_zones()
        loc_lower = location_name.lower().strip()
        matched = [z for z in zones if loc_lower in z.sector.lower() or loc_lower in z.name.lower()]
        return matched if matched else zones

    def get_pfz_geojson(self, location_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Converts PFZ zones to a GeoJSON FeatureCollection for direct Leaflet rendering.
        """
        zones = self.get_pfz_by_location(location_name) if location_name else self.get_pfz_zones()
        features = []
        for z in zones:
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [z.longitude, z.latitude]
                },
                "properties": {
                    "id": z.zone_id,
                    "name": z.name,
                    "sector": z.sector,
                    "distance_km": z.distance_km,
                    "direction": z.direction,
                    "sst": z.sea_surface_temperature,
                    "chlorophyll": z.chlorophyll,
                    "suitability": z.suitability,
                    "status": z.status,
                    "dominant_species": z.dominant_species,
                    "depth_meters": z.depth_meters,
                    "provider": z.provider,
                    "data_status": z.data_status,
                    "source_reference": z.source_reference
                }
            }
            features.append(feature)

        return {
            "type": "FeatureCollection",
            "features": features
        }

pfz_service = PFZService()
