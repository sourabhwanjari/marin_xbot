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
from app.data_sources.incois.client import INCOISClient
from app.marine_models.base import (
    Location,
    TimeWindow,
    MarineDataResponse,
    MarineEvidence,
    DataStatus,
)
from app.marine_models.domains import OceanData

logger = logging.getLogger("marinex.datasources.incois.ocean")

class INCOISOceanProvider(BaseMarineProvider):
    """
    Indian National Centre for Ocean Information Services (INCOIS) Ocean Telemetry Provider.
    Retrieves operational wave models, swell direction, Sea Surface Temperature (SST),
    and ocean sea state forecasts when configured.
    Phase 5B compliant: delegates to INCOISClient, normalizes to OceanData,
    includes freshness, and strictly returns NOT_CONFIGURED when unconfigured.
    """
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None
    ):
        super().__init__(
            provider_name="INCOIS-Ocean",
            capabilities=[ProviderCapability.OCEAN]
        )
        self.client = INCOISClient(
            api_key=api_key,
            base_url=base_url,
            username=username,
            password=password
        )

    @property
    def is_enabled(self) -> bool:
        return os.getenv("INCOIS_ENABLED", "false").lower() in ("true", "1", "yes")

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

    def get_ocean_conditions(
        self,
        location: Location,
        time_window: Optional[TimeWindow] = None
    ) -> MarineDataResponse:
        logger.info(f"[INCOIS Ocean] get_ocean_conditions requested for {location.name or 'Coastal Sector'} ({location.latitude:.3f}, {location.longitude:.3f})")
        retrieved_at = datetime.now(timezone.utc).isoformat()

        if not self.is_enabled:
            return MarineDataResponse(
                status=DataStatus.NOT_CONFIGURED,
                provider="INCOIS-Ocean",
                dataset="INCOIS-Wave-Hydrodynamic",
                parameter="ocean_state",
                latitude=location.latitude,
                longitude=location.longitude,
                observed_at="UNAVAILABLE",
                valid_from=None,
                valid_until=None,
                retrieved_at=retrieved_at,
                quality="UNAVAILABLE",
                location=location.to_dict(),
                data={"message": "INCOIS ocean provider is disabled (INCOIS_ENABLED=false)."},
                evidence=[
                    MarineEvidence(
                        source="INCOIS",
                        provider="INCOISOceanProvider",
                        dataset="INCOIS-Wave-Hydrodynamic",
                        retrieved_at=retrieved_at,
                        quality="UNAVAILABLE",
                        status=DataStatus.NOT_CONFIGURED,
                        metadata={"reason": "Provider disabled in configuration."}
                    )
                ]
            )

        if not self.is_configured:
            logger.info("[INCOIS Ocean] INCOIS credentials missing (INCOIS_API_KEY / INCOIS_BASE_URL). Returning NOT_CONFIGURED.")
            return MarineDataResponse(
                status=DataStatus.NOT_CONFIGURED,
                provider="INCOIS-Ocean",
                dataset="INCOIS-Wave-Hydrodynamic",
                parameter="ocean_state",
                latitude=location.latitude,
                longitude=location.longitude,
                observed_at="UNAVAILABLE",
                valid_from=None,
                valid_until=None,
                retrieved_at=retrieved_at,
                quality="NOT_CONFIGURED",
                location=location.to_dict(),
                data={
                    "message": "INCOIS API credentials not configured in environment (INCOIS_API_KEY / INCOIS_BASE_URL). Set credentials in .env to enable live INCOIS hydrodynamic ocean state feeds."
                },
                evidence=[
                    MarineEvidence(
                        source="INCOIS",
                        provider="INCOISOceanProvider",
                        dataset="INCOIS-Wave-Hydrodynamic",
                        retrieved_at=retrieved_at,
                        quality="UNAVAILABLE",
                        status=DataStatus.NOT_CONFIGURED,
                        metadata={"missing_fields": ["INCOIS_API_KEY", "INCOIS_BASE_URL"]}
                    )
                ]
            )

        # Configured: invoke dedicated client
        try:
            obs = self.client.fetch_ocean_conditions(
                latitude=location.latitude,
                longitude=location.longitude
            )
            self.last_retrieved_at = retrieved_at
            self.last_error = None

            observed_time = obs.observation_time or retrieved_at

            ocean_data = OceanData(
                sst=obs.sea_surface_temperature_c,
                chlorophyll="Moderate",
                wave_height=obs.significant_wave_height_m,
                swell_period=obs.swell_wave_period_s,
                swell_direction=obs.swell_direction_text,
                ocean_condition=obs.sea_state or "Moderate",
                tide_status=obs.tide_status or "Normal",
                suitability=obs.suitability
            )

            return MarineDataResponse(
                status=DataStatus.EXTERNAL,
                provider="INCOIS-Ocean",
                dataset="INCOIS-Wave-Hydrodynamic",
                parameter="ocean_state",
                latitude=location.latitude,
                longitude=location.longitude,
                observed_at=observed_time,
                valid_from=observed_time,
                valid_until=obs.valid_until,
                retrieved_at=retrieved_at,
                quality="HIGH",
                location=location.to_dict(),
                data=ocean_data.model_dump(),
                evidence=[
                    MarineEvidence(
                        source="Indian National Centre for Ocean Information Services",
                        provider="INCOISOceanProvider",
                        dataset="INCOIS-Wave-Hydrodynamic",
                        observed_at=observed_time,
                        valid_until=obs.valid_until,
                        retrieved_at=retrieved_at,
                        quality="HIGH",
                        status=DataStatus.EXTERNAL,
                        evidence_url=f"{self.client.base_url}/marine_forecast",
                        metadata={
                            "sector": location.name,
                            "source_reference": "INCOIS Operational Wave Bulletin"
                        }
                    )
                ]
            )
        except ProviderUnavailableError as e:
            logger.warning(f"[INCOIS Ocean] Service unavailable: {e}")
            self.last_error = str(e)
            return MarineDataResponse(
                status=DataStatus.UNAVAILABLE,
                provider="INCOIS-Ocean",
                dataset="INCOIS-Wave-Hydrodynamic",
                parameter="ocean_state",
                latitude=location.latitude,
                longitude=location.longitude,
                observed_at="UNAVAILABLE",
                retrieved_at=retrieved_at,
                quality="DEGRADED",
                location=location.to_dict(),
                data={"error": f"INCOIS ocean service unavailable: {str(e)}"},
                evidence=[
                    MarineEvidence(
                        source="INCOIS",
                        provider="INCOISOceanProvider",
                        dataset="INCOIS-Wave-Hydrodynamic",
                        retrieved_at=retrieved_at,
                        quality="UNAVAILABLE",
                        status=DataStatus.UNAVAILABLE,
                        metadata={"error": str(e)}
                    )
                ]
            )
        except Exception as e:
            logger.error(f"[INCOIS Ocean] Unexpected error: {e}")
            self.last_error = str(e)
            return MarineDataResponse(
                status=DataStatus.ERROR,
                provider="INCOIS-Ocean",
                dataset="INCOIS-Wave-Hydrodynamic",
                parameter="ocean_state",
                latitude=location.latitude,
                longitude=location.longitude,
                observed_at="UNAVAILABLE",
                retrieved_at=retrieved_at,
                quality="ERROR",
                location=location.to_dict(),
                data={"error": f"INCOIS ocean provider failure: {str(e)}"},
                evidence=[]
            )
