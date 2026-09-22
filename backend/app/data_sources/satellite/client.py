import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("marinex.datasources.satellite.client")

class MosdacClient:
    """
    Client for ISRO Meteorological & Oceanographic Satellite Data Archival Centre (MOSDAC).
    Requires registered credentials for Level-3 HDF5/NetCDF Oceansat data downloads.
    """
    def __init__(self):
        self.username = os.getenv("MOSDAC_USERNAME", "")
        self.password = os.getenv("MOSDAC_PASSWORD", "")
        self.base_url = os.getenv("MOSDAC_BASE_URL", "https://www.mosdac.gov.in")
        self.enabled = os.getenv("MOSDAC_ENABLED", "false").lower() == "true"

    def is_configured(self) -> bool:
        return bool(self.enabled and self.username and self.password)

    def check_connection(self) -> Dict[str, Any]:
        if not self.is_configured():
            return {
                "status": "not_configured",
                "message": "MOSDAC credentials (MOSDAC_USERNAME, MOSDAC_PASSWORD) are not configured in environment.",
                "is_live": False
            }
        return {
            "status": "configured",
            "message": "MOSDAC credentials present. Endpoint configured.",
            "is_live": True
        }

mosdac_client = MosdacClient()
