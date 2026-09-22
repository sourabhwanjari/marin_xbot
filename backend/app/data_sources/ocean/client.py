import json
import logging
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

logger = logging.getLogger("marinex.datasources.ocean.client")

class OceanClient:
    """
    Client for Open-Meteo Marine / Ocean Dynamics API.
    Provides hydrodynamic wave spectral data, significant wave heights,
    swell periods, and surface currents.
    """
    BASE_URL = "https://marine-api.open-meteo.com/v1/marine"

    def __init__(self, timeout_seconds: int = 5):
        self.timeout = timeout_seconds

    def fetch_ocean_conditions(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        params = (
            f"latitude={lat:.4f}&longitude={lon:.4f}"
            f"&current=wave_height,wave_direction,wave_period,wind_wave_height,swell_wave_height,swell_wave_period,ocean_current_velocity,ocean_current_direction"
        )
        url = f"{self.BASE_URL}?{params}"
        logger.info(f"[OceanClient] Requesting oceanographic conditions for Lat: {lat:.3f}, Lon: {lon:.3f}")

        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "MarineX-AI/1.4.0 (ORCA Marine Decision Platform)"}
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    return data
                else:
                    logger.warning(f"[OceanClient] Marine API returned status {resp.status}")
                    return None
        except urllib.error.URLError as e:
            logger.warning(f"[OceanClient] Network error connecting to Marine API: {e.reason}")
            return None
        except Exception as e:
            logger.error(f"[OceanClient] Unexpected error: {e}")
            return None

ocean_client = OceanClient()
