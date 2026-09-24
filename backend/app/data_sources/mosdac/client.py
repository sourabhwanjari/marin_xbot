import os
import logging
from typing import Optional, Dict, Any, List
from app.data_sources.mosdac.schemas import MOSDACGranuleRecord, MOSDACGranuleResponse
from app.data_sources.common.exceptions import (
    ProviderNotConfiguredError,
    ProviderUnavailableError,
    MarineDataFormatError,
)

logger = logging.getLogger("marinex.datasources.mosdac.client")

class MOSDACClient:
    """
    Dedicated HTTP Client for ISRO Meteorological & Oceanographic Satellite Data Archival Centre (MOSDAC).
    Provides authenticated access to Oceansat-3, INSAT-3D, and SCATSAT catalogs.
    Never exposes secrets in logs.
    """
    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        base_url: Optional[str] = None,
        dataset_id: Optional[str] = None,
        timeout_seconds: float = 8.0
    ):
        self._username = username
        self._password = password
        self._base_url = base_url
        self._dataset_id = dataset_id
        self.timeout = timeout_seconds

    @property
    def username(self) -> str:
        return (self._username or os.getenv("MOSDAC_USERNAME", "")).strip()

    @property
    def password(self) -> str:
        return (self._password or os.getenv("MOSDAC_PASSWORD", "")).strip()

    @property
    def base_url(self) -> str:
        url = (self._base_url or os.getenv("MOSDAC_BASE_URL", "https://api.mosdac.gov.in")).strip()
        return url.rstrip("/")

    @property
    def dataset_id(self) -> str:
        return (self._dataset_id or os.getenv("MOSDAC_DATASET_ID", "OS3_SST_L3")).strip()

    @property
    def is_configured(self) -> bool:
        return bool(self.username and self.password and self.base_url)

    def check_availability(self) -> bool:
        """Sanitized ping to verify whether the configured MOSDAC endpoint is reachable."""
        if not self.is_configured:
            return False
        try:
            import httpx
            with httpx.Client(timeout=4.0) as client:
                resp = client.get(f"{self.base_url}/health", auth=(self.username, self.password))
                return resp.status_code in (200, 204)
        except Exception:
            return False

    def fetch_granule_catalog(
        self,
        latitude: float,
        longitude: float,
        product: str = "sst",
        dataset: Optional[str] = None
    ) -> MOSDACGranuleResponse:
        """
        Executes authenticated query against ISRO MOSDAC granule catalog.
        Returns parsed MOSDACGranuleResponse.
        """
        if not self.is_configured:
            raise ProviderNotConfiguredError("MOSDAC credentials (username/password) are not configured.")

        target_dataset = dataset or self.dataset_id
        url = f"{self.base_url}/catalog/granules"
        params = {
            "dataset": target_dataset,
            "lat": latitude,
            "lon": longitude,
            "product": product
        }

        logger.info(f"[MOSDAC Client] Querying catalog for dataset '{target_dataset}', product '{product}' at ({latitude:.3f}, {longitude:.3f})")

        try:
            import httpx
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(url, params=params, auth=(self.username, self.password))
                if resp.status_code == 200:
                    raw = resp.json()
                    return self._parse_catalog_response(raw, target_dataset, product)
                elif resp.status_code in (401, 403):
                    raise ProviderUnavailableError("MOSDAC authentication failed (invalid username or password).")
                elif resp.status_code == 404:
                    raise ProviderUnavailableError(f"MOSDAC dataset '{target_dataset}' not found or no granules available for coordinate.")
                else:
                    raise ProviderUnavailableError(f"MOSDAC service returned HTTP {resp.status_code}")
        except httpx.TimeoutException:
            logger.warning(f"[MOSDAC Client] Request timed out after {self.timeout}s")
            raise ProviderUnavailableError(f"MOSDAC request timed out after {self.timeout}s.")
        except httpx.RequestError as e:
            logger.warning(f"[MOSDAC Client] Connection error: {e}")
            raise ProviderUnavailableError(f"Failed to connect to MOSDAC service: {str(e)}")

    def _parse_catalog_response(self, raw: Dict[str, Any], dataset_id: str, product: str) -> MOSDACGranuleResponse:
        try:
            raw_granules = raw.get("granules", [])
            records: List[MOSDACGranuleRecord] = []
            for g in raw_granules:
                records.append(
                    MOSDACGranuleRecord(
                        granule_id=g.get("granule_id") or g.get("id", "GRANULE-001"),
                        dataset_id=dataset_id,
                        satellite_mission=g.get("mission", "ISRO Oceansat-3"),
                        sensor=g.get("sensor", "OCM-3"),
                        product_name=product,
                        pass_timestamp=g.get("pass_time") or g.get("timestamp"),
                        spatial_resolution_km=float(g.get("spatial_resolution_km", 1.0)),
                        cloud_cover_percent=g.get("cloud_cover_percent"),
                        sst_c=g.get("sst"),
                        chlorophyll_mg_m3=g.get("chlorophyll"),
                        wind_speed_knots=g.get("wind_speed"),
                        download_url=g.get("download_url"),
                        metadata=g.get("metadata", {})
                    )
                )
            latest = records[0] if records else None
            return MOSDACGranuleResponse(
                dataset_id=dataset_id,
                total_granules=len(records),
                granules=records,
                latest_granule=latest,
                query_timestamp=raw.get("query_timestamp"),
                raw_payload=raw
            )
        except Exception as e:
            raise MarineDataFormatError(f"Failed to parse MOSDAC catalog response: {str(e)}")
