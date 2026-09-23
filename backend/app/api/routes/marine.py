from fastapi import APIRouter, Query
from typing import List, Optional
from app.models.schemas import MarineConditions, FishingZone, MarineAlert
from app.services.mock_marine_service import mock_marine_service
from app.marine_models.base import MarineDataResponse, Location, TimeWindow
from app.marine_gateway.gateway import marine_gateway
from app.marine_gateway.schemas import GatewayStatusResponse

router = APIRouter(prefix="/marine", tags=["Marine Intelligence"])

# --- Phase 1–4 Legacy Endpoints (Maintained for full backward compatibility) ---

@router.get("/conditions", response_model=MarineConditions)
async def get_marine_conditions():
    """Returns current simulated marine and oceanographic conditions."""
    return mock_marine_service.get_conditions()

@router.get("/fishing-zones", response_model=List[FishingZone])
async def get_fishing_zones():
    """Returns simulated Potential Fishing Zones (PFZs) with SST and chlorophyll data."""
    return mock_marine_service.get_fishing_zones()

@router.get("/alerts", response_model=List[MarineAlert])
async def get_marine_alerts():
    """Returns active simulated marine alerts, weather warnings, and geofenced zones."""
    return mock_marine_service.get_alerts()

# --- Phase 5A: Marine Data Gateway Endpoints ---

@router.get("/weather", response_model=MarineDataResponse)
async def get_weather_telemetry(
    latitude: Optional[float] = Query(None, ge=-90.0, le=90.0, description="Latitude in decimal degrees"),
    longitude: Optional[float] = Query(None, ge=-180.0, le=180.0, description="Longitude in decimal degrees"),
    radius: Optional[float] = Query(50.0, description="Search radius in kilometers"),
    start_time: Optional[str] = Query(None, description="Start timestamp filter (ISO 8601)"),
    end_time: Optional[str] = Query(None, description="End timestamp filter (ISO 8601)"),
    location: Optional[str] = Query(None, description="Coastal location name (e.g. Mumbai, Chennai)"),
    provider: Optional[str] = Query(None, description="Specific provider override (e.g. IMD, Open-Meteo)")
):
    """
    Retrieves normalized meteorological telemetry through the Marine Data Gateway.
    Routes to configured providers (IMD, Open-Meteo) with evidence preservation.
    """
    loc = Location(
        latitude=latitude if latitude is not None else 18.922,
        longitude=longitude if longitude is not None else 72.834,
        name=location
    )
    tw = TimeWindow(context="current")
    return marine_gateway.get_weather(location=loc, time_window=tw, provider_name=provider)

@router.get("/ocean", response_model=MarineDataResponse)
async def get_ocean_telemetry(
    latitude: Optional[float] = Query(None, ge=-90.0, le=90.0),
    longitude: Optional[float] = Query(None, ge=-180.0, le=180.0),
    radius: Optional[float] = Query(50.0),
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    provider: Optional[str] = Query(None, description="Specific provider override (e.g. INCOIS-Ocean)")
):
    """
    Retrieves normalized oceanographic telemetry (SST, wave height, swell period, sea state)
    through the Marine Data Gateway.
    """
    loc = Location(
        latitude=latitude if latitude is not None else 18.922,
        longitude=longitude if longitude is not None else 72.834,
        name=location
    )
    tw = TimeWindow(context="current")
    return marine_gateway.get_ocean_conditions(location=loc, time_window=tw, provider_name=provider)

@router.get("/pfz", response_model=MarineDataResponse)
async def get_pfz_telemetry(
    latitude: Optional[float] = Query(None, ge=-90.0, le=90.0),
    longitude: Optional[float] = Query(None, ge=-180.0, le=180.0),
    radius: Optional[float] = Query(50.0),
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
    location: Optional[str] = Query(None)
):
    """
    Retrieves normalized Potential Fishing Zone (PFZ) telemetry through the Marine Data Gateway.
    Interprets satellite SST thermal fronts and chlorophyll-a convergence boundaries.
    """
    loc = Location(
        latitude=latitude if latitude is not None else 18.922,
        longitude=longitude if longitude is not None else 72.834,
        name=location
    )
    tw = TimeWindow(context="current")
    res = marine_gateway.get_pfz(location=loc, time_window=tw)
    if isinstance(res, list):
        # Convert legacy list to normalized MarineDataResponse
        from app.marine_models.base import DataStatus
        return MarineDataResponse(
            status=DataStatus.VERIFIED,
            provider="INCOIS-PFZ",
            dataset="INCOIS-PFZ-Telemetry",
            location=loc.to_dict(),
            data={"zones": [z.model_dump() for z in res], "total_active_zones": len(res)},
            retrieved_at=loc.to_dict().get("retrieved_at", "current")
        )
    return res

@router.get("/satellite", response_model=MarineDataResponse)
async def get_satellite_telemetry(
    latitude: Optional[float] = Query(None, ge=-90.0, le=90.0),
    longitude: Optional[float] = Query(None, ge=-180.0, le=180.0),
    product: str = Query("sst", description="Satellite earth observation product (sst, chlorophyll, winds, altimetry)"),
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None)
):
    """
    Retrieves satellite earth observation telemetry from ISRO MOSDAC.
    Strictly returns NOT_CONFIGURED when live ISRO MOSDAC credentials are not present.
    """
    loc = Location(
        latitude=latitude if latitude is not None else 18.922,
        longitude=longitude if longitude is not None else 72.834
    )
    return marine_gateway.get_satellite_data(location=loc, product_name=product)

@router.get("/geospatial", response_model=MarineDataResponse)
async def get_geospatial_telemetry(
    latitude: Optional[float] = Query(None, ge=-90.0, le=90.0),
    longitude: Optional[float] = Query(None, ge=-180.0, le=180.0),
    location: Optional[str] = Query(None, description="Coastal sector name")
):
    """
    Retrieves normalized maritime geospatial boundaries (ports, shipping lanes, MPAs, hazards).
    """
    loc = Location(
        latitude=latitude if latitude is not None else 18.922,
        longitude=longitude if longitude is not None else 72.834,
        name=location
    )
    return marine_gateway.get_geospatial_context(location=loc)

@router.get("/gateway/status", response_model=GatewayStatusResponse)
async def get_gateway_status():
    """
    Reports the operational health, capability routing, and configuration status
    of all registered marine data providers.
    NEVER exposes API keys, tokens, or credentials.
    """
    return marine_gateway.get_gateway_status()
