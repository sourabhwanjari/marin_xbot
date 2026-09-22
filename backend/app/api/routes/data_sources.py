from fastapi import APIRouter, Query
from typing import Dict, Any, Optional
from app.marine_gateway.health import check_all_data_sources
from app.data_sources.pfz.service import pfz_service
from app.data_sources.geospatial.service import geospatial_service

router = APIRouter(prefix="/data-sources", tags=["Real Marine Data Sources"])

@router.get("/status")
async def get_data_sources_status() -> Dict[str, Any]:
    """
    Returns real-time health, connectivity, and configuration status
    for all marine data providers (Weather, Ocean, PFZ, Satellite, PostGIS/GIS).
    """
    return check_all_data_sources()

@router.get("/pfz")
async def get_pfz_data(location: Optional[str] = Query(None, description="Coastal sector or location name")) -> Dict[str, Any]:
    """
    Returns validated Potential Fishing Zone (PFZ) advisories in GeoJSON FeatureCollection format.
    """
    return pfz_service.get_pfz_geojson(location)

@router.get("/geospatial")
async def get_geospatial_layers() -> Dict[str, Any]:
    """
    Returns registered geospatial layers (ports, restricted fairways, MPAs, hazard sectors).
    """
    return {
        "ports": {
            "type": "FeatureCollection",
            "features": geospatial_service.ports
        },
        "restricted_zones": {
            "type": "FeatureCollection",
            "features": geospatial_service.restricted
        },
        "protected_areas": {
            "type": "FeatureCollection",
            "features": geospatial_service.protected
        },
        "hazard_zones": {
            "type": "FeatureCollection",
            "features": geospatial_service.hazards
        }
    }
