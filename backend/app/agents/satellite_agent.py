import logging
from typing import Dict, Any, Optional
from app.marine_models.base import Location
from app.marine_gateway.gateway import marine_gateway
from app.data_sources.geospatial.service import geospatial_service

logger = logging.getLogger("marinex.agents.satellite")

class SatelliteAgent:
    """
    Satellite Agent: Retrieves remote sensing Earth Observation (EO) satellite telemetry
    (SST thermal contours, Ocean Color, MOSDAC telemetry) via the Marine Data Gateway.
    """
    def run(self, location: str = "chennai", product: str = "sst") -> Dict[str, Any]:
        logger.info(f"[LANGGRAPH] SatelliteAgent executing satellite analysis for {location} (product={product})")
        try:
            coords = geospatial_service.get_coordinates_by_name(location)
            lat = coords["lat"]
            lon = coords["lon"]
            loc_obj = Location(latitude=lat, longitude=lon, name=coords["name"])

            logger.info(f"[GATEWAY] Invoking marine_gateway.get_satellite_data for location='{coords['name']}' ({lat}, {lon}) [product={product}]")
            resp = marine_gateway.get_satellite_data(location=loc_obj, product_name=product)
            status_str = resp.status.value if hasattr(resp.status, "value") else str(resp.status)
            logger.info(f"[MARINE_DATA] Gateway get_satellite_data returned provider='{resp.provider}', status='{status_str}'")

            data = {
                "location": coords["name"],
                "coordinates": {"lat": lat, "lon": lon},
                "product": product,
                "provider": resp.provider,
                "data_status": status_str,
                "data": resp.data,
                "evidence": [e.model_dump() if hasattr(e, "model_dump") else e for e in resp.evidence],
                "retrieved_at": resp.retrieved_at
            }
            logger.info(f"[LANGGRAPH] SatelliteAgent completed for {location}: status={status_str}")
            return data
        except Exception as e:
            logger.error(f"[SatelliteAgent] Error executing satellite gateway: {e}")
            return {
                "location": location,
                "product": product,
                "provider": "MOSDAC",
                "data_status": "error",
                "error": str(e),
                "data": {"message": str(e)},
                "evidence": []
            }

satellite_agent = SatelliteAgent()
