import logging
from typing import Dict, Any, Optional
from app.tools.geospatial_tools import (
    get_coordinates,
    check_restricted_zone,
    check_protected_area,
    find_nearest_port,
)
from app.data_sources.pfz.service import pfz_service
from app.models.agent_models import GeospatialResult

logger = logging.getLogger("marinex.agents.geospatial")

class GeospatialAgent:
    """
    Geospatial Agent: Resolves coordinates, verifies restricted shipping channels,
    evaluates proximity to marine sanctuaries/MPAs, finds nearest port facilities,
    and identifies nearest Potential Fishing Zones (PFZs).
    """
    def run(self, location: str = "chennai") -> Dict[str, Any]:
        logger.info(f"[GeospatialAgent] Executing spatial analysis for {location}")
        try:
            coords_data = get_coordinates.invoke({"location": location})
            lat = coords_data["lat"]
            lon = coords_data["lon"]

            restr = check_restricted_zone.invoke({"lat": lat, "lon": lon})
            prot = check_protected_area.invoke({"lat": lat, "lon": lon})
            port = find_nearest_port.invoke({"lat": lat, "lon": lon})

            # Check nearest PFZ
            nearest_pfz = pfz_service.get_nearest_pfz(lat, lon)
            pfz_geojson = pfz_service.get_pfz_geojson(location)

            result = GeospatialResult(
                coordinates={"lat": lat, "lng": lon},
                location_name=coords_data["name"],
                nearest_port=port["port_name"],
                restricted_zone=restr["is_restricted"],
                protected_zone=prot["is_protected"],
                distance_from_coast_km=round(port["distance_km"], 1),
                nearest_hazard=restr["zone_name"] if restr["is_restricted"] else prot.get("area_name"),
                source="GeoJSON Spatial Engine / PostGIS Ready",
                data_status="verified"
            )
            data = result.model_dump()
            data["restriction_details"] = restr.get("restriction") or prot.get("restriction")
            if nearest_pfz:
                data["nearest_pfz"] = {
                    "id": nearest_pfz.zone_id,
                    "name": nearest_pfz.name,
                    "distance_km": nearest_pfz.distance_km,
                    "direction": nearest_pfz.direction,
                    "lat": nearest_pfz.latitude,
                    "lon": nearest_pfz.longitude,
                    "sst": nearest_pfz.sea_surface_temperature,
                    "chlorophyll": nearest_pfz.chlorophyll,
                    "suitability": nearest_pfz.suitability
                }
            data["map_data"] = pfz_geojson
            return data
        except Exception as e:
            logger.error(f"[GeospatialAgent] Error executing geospatial tools: {e}")
            return {
                "coordinates": {"lat": 13.125, "lng": 80.298},
                "location_name": location.title(),
                "nearest_port": "Regional Fishing Wharf",
                "restricted_zone": False,
                "protected_zone": False,
                "distance_from_coast_km": 5.0,
                "source": "Fallback Geospatial Service",
                "data_status": "demo",
                "error": str(e)
            }

geospatial_agent = GeospatialAgent()
