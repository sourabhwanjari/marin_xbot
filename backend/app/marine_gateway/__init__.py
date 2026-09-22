from app.marine_gateway.models import (
    NormalizedWeather,
    NormalizedOcean,
    NormalizedPFZ,
    NormalizedGeospatial,
    MarineEvidence,
)
from app.marine_gateway.cache import marine_cache

__all__ = [
    "marine_gateway",
    "MarineDataGateway",
    "marine_cache",
    "check_all_data_sources",
    "NormalizedWeather",
    "NormalizedOcean",
    "NormalizedPFZ",
    "NormalizedGeospatial",
    "MarineEvidence",
]

def __getattr__(name):
    if name in ("marine_gateway", "MarineDataGateway"):
        from app.marine_gateway.gateway import marine_gateway, MarineDataGateway
        return marine_gateway if name == "marine_gateway" else MarineDataGateway
    if name == "check_all_data_sources":
        from app.marine_gateway.health import check_all_data_sources
        return check_all_data_sources
    raise AttributeError(f"module {__name__} has no attribute {name}")
