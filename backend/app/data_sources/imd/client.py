import os
import logging
from typing import Optional, Dict, Any
from app.data_sources.imd.schemas import IMDWeatherObservation
from app.data_sources.common.exceptions import (
    ProviderNotConfiguredError,
    ProviderUnavailableError,
    MarineDataFormatError,
)

logger = logging.getLogger("marinex.datasources.imd.client")

class IMDClient:
    """
    Dedicated HTTP Client for the India Meteorological Department (IMD) Marine API.
    Handles authentication, timeouts, and sanitized error reporting.
    Never exposes API secrets in logs.
    """
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout_seconds: float = 6.0
    ):
        self._api_key = api_key
        self._base_url = base_url
        self.timeout = timeout_seconds

    @property
    def api_key(self) -> str:
        return (self._api_key or os.getenv("IMD_API_KEY", "")).strip()

    @property
    def base_url(self) -> str:
        url = (self._base_url or os.getenv("IMD_BASE_URL", "")).strip()
        return url.rstrip("/")

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.base_url)

    def check_availability(self) -> bool:
        """Sanitized ping to verify whether the configured IMD endpoint is reachable."""
        if not self.is_configured:
            return False
        try:
            import httpx
            with httpx.Client(timeout=3.0) as client:
                resp = client.get(f"{self.base_url}/health", headers={"Authorization": f"Bearer {self.api_key}"})
                return resp.status_code in (200, 204)
        except Exception:
            return False

    def fetch_coastal_weather(
        self,
        latitude: float,
        longitude: float,
        station_id: Optional[str] = None
    ) -> IMDWeatherObservation:
        """
        Executes authenticated request to IMD coastal weather endpoint.
        Normalizes raw payload into IMDWeatherObservation schema.
        """
        if not self.is_configured:
            raise ProviderNotConfiguredError("IMD API key or base URL is not configured.")

        url = f"{self.base_url}/coastal/weather"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "User-Agent": "MARINEX-AI-Gateway/5.0"
        }
        params: Dict[str, Any] = {"lat": latitude, "lon": longitude}
        if station_id:
            params["station_id"] = station_id

        logger.info(f"[IMD Client] Requesting coastal weather for ({latitude:.3f}, {longitude:.3f})")

        try:
            import httpx
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(url, params=params, headers=headers)
                if resp.status_code == 200:
                    raw = resp.json()
                    return self._parse_response(raw, latitude, longitude)
                elif resp.status_code in (401, 403):
                    raise ProviderUnavailableError("IMD authentication failed (invalid or expired API key).")
                elif resp.status_code == 404:
                    raise ProviderUnavailableError(f"No IMD coastal station found within operational range of ({latitude}, {longitude}).")
                else:
                    raise ProviderUnavailableError(f"IMD server returned HTTP {resp.status_code}")
        except httpx.TimeoutException:
            logger.warning(f"[IMD Client] Request timed out after {self.timeout}s")
            raise ProviderUnavailableError(f"IMD request timed out after {self.timeout}s.")
        except httpx.RequestError as e:
            logger.warning(f"[IMD Client] Connection error: {e}")
            raise ProviderUnavailableError(f"Failed to connect to IMD service: {str(e)}")

    def _parse_response(self, raw: Dict[str, Any], default_lat: float, default_lon: float) -> IMDWeatherObservation:
        """Parses raw IMD API payload into typed observation model."""
        try:
            return IMDWeatherObservation(
                station_name=raw.get("station_name") or raw.get("location"),
                station_id=raw.get("station_id"),
                latitude=raw.get("latitude", default_lat),
                longitude=raw.get("longitude", default_lon),
                observation_time=raw.get("observation_time") or raw.get("timestamp"),
                air_temperature_c=raw.get("temperature") or raw.get("air_temperature"),
                relative_humidity_percent=raw.get("humidity") or raw.get("relative_humidity"),
                wind_speed_knots=raw.get("wind_speed_knots") or raw.get("wind_speed"),
                wind_direction_deg=raw.get("wind_direction_deg"),
                wind_direction_text=raw.get("wind_direction"),
                pressure_hpa=raw.get("pressure_hpa") or raw.get("pressure"),
                rain_probability_percent=raw.get("rain_probability"),
                precipitation_mm=raw.get("precipitation_mm"),
                visibility_km=raw.get("visibility_km") or raw.get("visibility"),
                weather_condition=raw.get("weather_condition") or raw.get("condition"),
                cyclone_warning=raw.get("cyclone_warning"),
                squall_warning=raw.get("squall_warning"),
                valid_until=raw.get("valid_until"),
                raw_payload=raw
            )
        except Exception as e:
            raise MarineDataFormatError(f"Failed to parse IMD response payload: {str(e)}")
