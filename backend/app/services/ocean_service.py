"""
Oceanographic Service Abstraction Layer
Target Phase: Connects to INCOIS (Indian National Centre for Ocean Information Services)
Phase 1: Provides simulated sea-state, wave spectral parameters, and tidal streams.
"""
from typing import Dict, Any

class OceanService:
    def __init__(self, endpoint_url: str = ""):
        self.endpoint_url = endpoint_url

    async def get_ocean_state(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Future implementation: Retrieve INCOIS high-resolution wave model (SWAN/WAVEWATCH III),
        current velocity, swell period, and sea-surface height anomalies.
        """
        return {
            "source": "simulated_incois_osf",
            "lat": lat,
            "lon": lon,
            "significant_wave_height_m": 1.8,
            "swell_height_m": 1.2,
            "swell_period_sec": 9.5,
            "surface_current_velocity_m_s": 0.45,
            "current_direction_deg": 190,
            "sea_state_code": 4  # Moderate
        }

ocean_service = OceanService()
