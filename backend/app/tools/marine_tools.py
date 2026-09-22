from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from app.marine_gateway.gateway import marine_gateway

@tool
def get_potential_fishing_zones(lat: Optional[float] = None, lon: Optional[float] = None, location: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieves Potential Fishing Zones (PFZs) delineated by Sea Surface Temperature (SST)
    and chlorophyll-a thermal convergence fronts from the Marine Data Gateway.
    """
    zones = marine_gateway.get_pfz(latitude=lat, longitude=lon, location_name=location)
    return [
        {
            "id": z.zone_id,
            "name": z.name,
            "latitude": z.latitude,
            "longitude": z.longitude,
            "sector": z.sector,
            "distance_km": z.distance_km,
            "direction": z.direction,
            "sst": z.sea_surface_temperature,
            "chlorophyll": z.chlorophyll,
            "suitability": z.suitability,
            "status": z.status,
            "species": z.dominant_species,
            "depth_meters": z.depth_meters,
            "source": z.provider,
            "data_status": z.data_status,
            "advisory_date": z.advisory_date,
            "valid_until": z.valid_until
        }
        for z in zones
    ]

@tool
def get_active_alerts(location: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieves active marine safety alerts, high wave warnings, and squall advisories.
    """
    return marine_gateway.get_marine_alerts(location_name=location)
