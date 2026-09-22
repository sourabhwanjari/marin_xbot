import os
import yaml
import logging
from typing import Dict, Any, List, Optional
from app.data_sources.base import DataSource, DataStatus
from app.data_sources.satellite.client import mosdac_client
from app.data_sources.satellite.models import SatelliteQueryResult

logger = logging.getLogger("marinex.datasources.satellite.service")

class SatelliteService(DataSource):
    """
    Satellite Service: Interfaces with ISRO MOSDAC Earth Observation products.
    Returns dataset metadata when configured; explicitly reports 'not_configured'
    when credentials or dataset IDs are missing.
    """
    name: str = "satellite"
    enabled: bool = False

    def __init__(self):
        self.config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "config",
            "datasets.yaml"
        )
        self.datasets_config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.error(f"[SatelliteService] Failed to load datasets.yaml: {e}")
        return {}

    def health_check(self) -> Dict[str, Any]:
        conn = mosdac_client.check_connection()
        return {
            "provider": "ISRO MOSDAC",
            "status": conn["status"],
            "message": conn["message"],
            "is_live": conn["is_live"]
        }

    def fetch(self, **kwargs) -> SatelliteQueryResult:
        return self.get_satellite_product(kwargs.get("product_name", "sst"))

    def get_satellite_product(self, product_name: str = "sst") -> SatelliteQueryResult:
        logger.info(f"[SatelliteService] Querying satellite product: {product_name}")

        if not mosdac_client.is_configured():
            return SatelliteQueryResult(
                status="not_configured",
                message="Satellite data source is not configured. Configure MOSDAC_ENABLED, MOSDAC_USERNAME, and MOSDAC_PASSWORD in .env.",
                provider="ISRO MOSDAC",
                products=[],
                data_status="not_configured"
            )

        # If configured, return discovered products
        sat_conf = self.datasets_config.get("satellite", {})
        products = sat_conf.get("products", {})

        return SatelliteQueryResult(
            status="available",
            message=f"MOSDAC satellite dataset interface active. Found {len(products)} registered products.",
            provider="ISRO MOSDAC",
            products=[{"key": k, **v} for k, v in products.items()],
            data_status="verified"
        )

satellite_service = SatelliteService()
