from fastapi import APIRouter
from typing import List
from app.models.schemas import MarineConditions, FishingZone, MarineAlert
from app.services.mock_marine_service import mock_marine_service

router = APIRouter(prefix="/marine", tags=["Marine Intelligence"])

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
