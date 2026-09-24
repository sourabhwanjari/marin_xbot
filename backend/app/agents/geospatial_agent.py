import logging
from typing import Dict, Any, Optional
from app.tools.geospatial_tools import (
    get_coordinates,
    check_restricted_zone,
    check_protected_area,
    find_nearest_port,
)
from app.marine_models.base import Location
from app.marine_gateway.gateway import marine_gateway
from app.data_sources.pfz.service import pfz_service
from app.models.agent_models import GeospatialResult

logger = logging.getLogger("marinex.agents.geospatial")

class GeospatialAgent:
    """
    Geospatial Agent: Resolves coordinates, verifies restricted shipping channels,
    evaluates proximity to marine sanctuaries/MPAs, finds nearest port facilities,
    and identifies nearest Potential Fishing Zones (PFZs) via the Marine Data Gateway.
    """
    def run(self, location: str = "chennai") -> Dict[str, Any]:
        logger.info(f"[LANGGRAPH] GeospatialAgent executing spatial analysis for {location}")
        try:
            coords_data = get_coordinates.invoke({"location": location})
            lat = coords_data["lat"]
            lon = coords_data["lon"]

            restr = check_restricted_zone.invoke({"lat": lat, "lon": lon})
            prot = check_protected_area.invoke({"lat": lat, "lon": lon})
            port = find_nearest_port.invoke({"lat": lat, "lon": lon})

            # Query PFZ through Marine Data Gateway
            loc_obj = Location(latitude=lat, longitude=lon, name=coords_data["name"])
            logger.info(f"[GATEWAY] Invoking marine_gateway.get_pfz for location='{coords_data['name']}' ({lat}, {lon})")
            pfz_resp = marine_gateway.get_pfz(loc_obj)
            status_str = pfz_resp.status.value if hasattr(pfz_resp.status, "value") else str(pfz_resp.status)
            logger.info(f"[MARINE_DATA] Gateway get_pfz returned provider='{pfz_resp.provider}', status='{status_str}'")

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
            data["pfz_status"] = status_str
            data["pfz_provider"] = pfz_resp.provider

            # Extract nearest PFZ from Gateway response
            nearest_zone_data = None
            if isinstance(pfz_resp.data, dict):
                nearest_zone_data = pfz_resp.data.get("nearest_zone")

            if nearest_zone_data:
                data["nearest_pfz"] = {
                    "id": nearest_zone_data.get("zone_id") or nearest_zone_data.get("id", "PFZ-1"),
                    "name": nearest_zone_data.get("name", "Zone Alpha"),
                    "distance_km": nearest_zone_data.get("distance_km", 25.0),
                    "direction": nearest_zone_data.get("direction", "ENE"),
                    "lat": nearest_zone_data.get("latitude") or nearest_zone_data.get("lat", lat),
                    "lon": nearest_zone_data.get("longitude") or nearest_zone_data.get("lon", lon),
                    "sst": nearest_zone_data.get("sea_surface_temperature") or nearest_zone_data.get("sst", 28.4),
                    "chlorophyll": nearest_zone_data.get("chlorophyll", "High"),
                    "suitability": nearest_zone_data.get("suitability", "Favorable")
                }
            elif status_str in ("not_configured", "unavailable"):
                data["nearest_pfz"] = None
            else:
                # Fallback to legacy service if gateway returned empty
                legacy_pfz = pfz_service.get_nearest_pfz(lat, lon)
                if legacy_pfz:
                    data["nearest_pfz"] = {
                        "id": legacy_pfz.zone_id,
                        "name": legacy_pfz.name,
                        "distance_km": legacy_pfz.distance_km,
                        "direction": legacy_pfz.direction,
                        "lat": legacy_pfz.latitude,
                        "lon": legacy_pfz.longitude,
                        "sst": legacy_pfz.sea_surface_temperature,
                        "chlorophyll": legacy_pfz.chlorophyll,
                        "suitability": legacy_pfz.suitability
                    }

            data["map_data"] = pfz_geojson
            logger.info(f"[LANGGRAPH] GeospatialAgent completed for {location}: port='{port['port_name']}', restricted={restr['is_restricted']}")
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
