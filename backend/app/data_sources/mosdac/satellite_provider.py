import os
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from app.data_sources.common.base_provider import BaseMarineProvider
from app.data_sources.common.models import ProviderCapability
from app.data_sources.common.provider_status import ProviderStatus
from app.data_sources.common.exceptions import (
    ProviderNotConfiguredError,
    ProviderUnavailableError,
    MarineDataFormatError,
)
from app.data_sources.mosdac.client import MOSDACClient
from app.marine_models.base import (
    Location,
    TimeWindow,
    MarineDataResponse,
    MarineEvidence,
    DataStatus,
)
from app.marine_models.domains import SatelliteData

logger = logging.getLogger("marinex.datasources.mosdac")

class MOSDACSatelliteProvider(BaseMarineProvider):
    """
    ISRO Meteorological and Oceanographic Satellite Data Archival Centre (MOSDAC) Provider.
    Interfaces Oceansat-3, INSAT-3D, and SCATSAT ocean wind vectors, Sea Surface Temperature (SST),
    and ocean color data.
    Phase 5B compliant: delegates to MOSDACClient, normalizes to SatelliteData,
    includes freshness, and strictly returns NOT_CONFIGURED when credentials are absent.
    """
    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        base_url: Optional[str] = None,
        dataset_id: Optional[str] = None
    ):
        super().__init__(
            provider_name="MOSDAC",
            capabilities=[ProviderCapability.SATELLITE]
        )
        self.client = MOSDACClient(
            username=username,
            password=password,
            base_url=base_url,
            dataset_id=dataset_id
        )

    @property
    def is_enabled(self) -> bool:
        return os.getenv("MOSDAC_ENABLED", "false").lower() in ("true", "1", "yes")

    @property
    def is_configured(self) -> bool:
        return self.client.is_configured

    @property
    def status(self) -> ProviderStatus:
        if not self.is_enabled or not self.is_configured:
            return ProviderStatus.NOT_CONFIGURED
        if self.last_error:
            if "unavailable" in self.last_error.lower() or "timeout" in self.last_error.lower():
                return ProviderStatus.UNAVAILABLE
            return ProviderStatus.ERROR
        return ProviderStatus.CONNECTED

    def get_satellite_data(
        self,
        location: Optional[Location] = None,
        product: str = "sst",
        time_window: Optional[TimeWindow] = None
    ) -> MarineDataResponse:
        retrieved_at = datetime.now(timezone.utc).isoformat()
        lat = location.latitude if location else 18.922
        lon = location.longitude if location else 72.834

        logger.info(f"[MOSDAC Provider] get_satellite_data requested for product '{product}' at ({lat:.3f}, {lon:.3f})")

        # Guardrail: Without credentials, strictly return NOT_CONFIGURED
        if not self.is_configured or not self.is_enabled:
            logger.info("[MOSDAC Provider] MOSDAC credentials not configured. Returning NOT_CONFIGURED status.")
            return MarineDataResponse(
                status=DataStatus.NOT_CONFIGURED,
                provider="MOSDAC",
                dataset=self.client.dataset_id,
                parameter=product,
                latitude=lat,
                longitude=lon,
                observed_at="UNAVAILABLE",
                valid_from=None,
                valid_until=None,
                retrieved_at=retrieved_at,
                quality="NOT_CONFIGURED",
                location=location.to_dict() if location else {"latitude": lat, "longitude": lon},
                data={
                    "message": "ISRO MOSDAC satellite API is not configured. Missing credentials (MOSDAC_USERNAME, MOSDAC_PASSWORD, MOSDAC_DATASET_ID). Set in environment to enable live earth observation passes.",
                    "disclaimer": "ISRO MOSDAC satellite API credentials not configured in environment.",
                    "product": product,
                    "satellite_mission": "ISRO Oceansat-3",
                    "available_products": ["sst", "chlorophyll", "ocean_winds", "altimetry"]
                },
                evidence=[
                    MarineEvidence(
                        source="ISRO MOSDAC",
                        provider="MOSDACSatelliteProvider",
                        dataset=self.client.dataset_id,
                        retrieved_at=retrieved_at,
                        quality="UNAVAILABLE",
                        status=DataStatus.NOT_CONFIGURED,
                        evidence_url="https://www.mosdac.gov.in",
                        metadata={"missing_fields": ["MOSDAC_USERNAME", "MOSDAC_PASSWORD"]}
                    )
                ]
            )

        # Configured: invoke client
        try:
            resp = self.client.fetch_granule_catalog(
                latitude=lat,
                longitude=lon,
                product=product
            )
            self.last_retrieved_at = retrieved_at
            self.last_error = None

            granule = resp.latest_granule
            pass_time = granule.pass_timestamp if granule else retrieved_at

            sat_data = SatelliteData(
                product_name=product,
                satellite_mission=granule.satellite_mission if granule else "ISRO Oceansat-3",
                sensor=granule.sensor if granule else "OCM-3",
                spatial_resolution_km=granule.spatial_resolution_km if granule else 1.0,
                pass_time=pass_time,
                granule_id=granule.granule_id if granule else None,
                cloud_cover_percent=granule.cloud_cover_percent if granule else None,
                status=DataStatus.EXTERNAL,
                message=f"Live granule {granule.granule_id if granule else 'detected'} successfully retrieved from ISRO MOSDAC."
            )

            return MarineDataResponse(
                status=DataStatus.EXTERNAL,
                provider="MOSDAC",
                dataset=resp.dataset_id,
                parameter=product,
                latitude=lat,
                longitude=lon,
                observed_at=pass_time,
                valid_from=pass_time,
                valid_until=None,
                retrieved_at=retrieved_at,
                quality="HIGH",
                location=location.to_dict() if location else {},
                data=sat_data.model_dump(),
                evidence=[
                    MarineEvidence(
                        source="ISRO Meteorological & Oceanographic Satellite Data Archival Centre",
                        provider="MOSDACSatelliteProvider",
                        dataset=resp.dataset_id,
                        observed_at=pass_time,
                        retrieved_at=retrieved_at,
                        quality="HIGH",
                        status=DataStatus.EXTERNAL,
                        evidence_url=f"{self.client.base_url}/catalog/{resp.dataset_id}",
                        metadata={
                            "total_granules_found": resp.total_granules,
                            "granule_id": granule.granule_id if granule else None
                        }
                    )
                ]
            )
        except ProviderUnavailableError as e:
            logger.warning(f"[MOSDAC Provider] Live connection failure: {e}")
            self.last_error = str(e)
            return MarineDataResponse(
                status=DataStatus.UNAVAILABLE,
                provider="MOSDAC",
                dataset=self.client.dataset_id,
                parameter=product,
                latitude=lat,
                longitude=lon,
                observed_at="UNAVAILABLE",
                retrieved_at=retrieved_at,
                quality="DEGRADED",
                location=location.to_dict() if location else {},
                data={"error": f"MOSDAC satellite service unavailable: {str(e)}"},
                evidence=[
                    MarineEvidence(
                        source="ISRO MOSDAC",
                        provider="MOSDACSatelliteProvider",
                        dataset=self.client.dataset_id,
                        retrieved_at=retrieved_at,
                        quality="UNAVAILABLE",
                        status=DataStatus.UNAVAILABLE,
                        metadata={"error": str(e)}
                    )
                ]
            )
        except Exception as e:
            logger.error(f"[MOSDAC Provider] Unexpected error: {e}")
            self.last_error = str(e)
            return MarineDataResponse(
                status=DataStatus.ERROR,
                provider="MOSDAC",
                dataset=self.client.dataset_id,
                parameter=product,
                latitude=lat,
                longitude=lon,
                observed_at="UNAVAILABLE",
                retrieved_at=retrieved_at,
                quality="ERROR",
                location=location.to_dict() if location else {},
                data={"error": f"MOSDAC satellite provider failure: {str(e)}"},
                evidence=[]
            )
