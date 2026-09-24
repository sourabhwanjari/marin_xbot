import os
import logging
from typing import Optional, Dict, Any, List
from app.data_sources.incois.schemas import INCOISOceanObservation, INCOISPFZResponse, INCOISPFZRecord
from app.data_sources.common.exceptions import (
    ProviderNotConfiguredError,
    ProviderUnavailableError,
    MarineDataFormatError,
)

logger = logging.getLogger("marinex.datasources.incois.client")

class INCOISClient:
    """
    Dedicated HTTP Client for the Indian National Centre for Ocean Information Services (INCOIS).
    Communicates with hydrodynamic wave forecast systems and PFZ thermal front services.
    Never exposes API secrets in logs.
    """
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout_seconds: float = 6.0
    ):
        self._api_key = api_key
        self._base_url = base_url
        self._username = username
        self._password = password
        self.timeout = timeout_seconds

    @property
    def api_key(self) -> str:
        return (self._api_key or os.getenv("INCOIS_API_KEY", "")).strip()

    @property
    def base_url(self) -> str:
        url = (self._base_url or os.getenv("INCOIS_BASE_URL", "")).strip()
        return url.rstrip("/")

    @property
    def username(self) -> str:
        return (self._username or os.getenv("INCOIS_USERNAME", "")).strip()

    @property
    def password(self) -> str:
        return (self._password or os.getenv("INCOIS_PASSWORD", "")).strip()

    @property
    def is_configured(self) -> bool:
        has_url = bool(self.base_url)
        has_auth = bool(self.api_key or (self.username and self.password))
        return has_url and has_auth

    def _get_auth_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/json",
            "User-Agent": "MARINEX-AI-Gateway/5.0"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        elif self.username and self.password:
            import base64
            token = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
            headers["Authorization"] = f"Basic {token}"
        return headers

    def check_availability(self) -> bool:
        """Sanitized ping to verify whether the configured INCOIS endpoint is reachable."""
        if not self.is_configured:
            return False
        try:
            import httpx
            with httpx.Client(timeout=3.0) as client:
                resp = client.get(f"{self.base_url}/health", headers=self._get_auth_headers())
                return resp.status_code in (200, 204)
        except Exception:
            return False

    def fetch_ocean_conditions(self, latitude: float, longitude: float) -> INCOISOceanObservation:
        """Fetches live hydrodynamic wave, swell, and SST telemetry."""
        if not self.is_configured:
            raise ProviderNotConfiguredError("INCOIS API credentials or base URL not configured.")

        url = f"{self.base_url}/ocean/conditions"
        params = {"lat": latitude, "lon": longitude}

        logger.info(f"[INCOIS Client] Requesting ocean conditions for ({latitude:.3f}, {longitude:.3f})")

        try:
            import httpx
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(url, params=params, headers=self._get_auth_headers())
                if resp.status_code == 200:
                    raw = resp.json()
                    return self._parse_ocean_response(raw, latitude, longitude)
                elif resp.status_code in (401, 403):
                    raise ProviderUnavailableError("INCOIS authentication failed (invalid API credentials).")
                elif resp.status_code == 404:
                    raise ProviderUnavailableError(f"No INCOIS ocean buoy or model grid at ({latitude}, {longitude}).")
                else:
                    raise ProviderUnavailableError(f"INCOIS ocean service returned HTTP {resp.status_code}")
        except httpx.TimeoutException:
            logger.warning(f"[INCOIS Client] Request timed out after {self.timeout}s")
            raise ProviderUnavailableError(f"INCOIS ocean request timed out after {self.timeout}s.")
        except httpx.RequestError as e:
            logger.warning(f"[INCOIS Client] Connection error: {e}")
            raise ProviderUnavailableError(f"Failed to connect to INCOIS service: {str(e)}")

    def fetch_pfz_advisories(self, latitude: float, longitude: float) -> INCOISPFZResponse:
        """Fetches active Potential Fishing Zone (PFZ) advisory records."""
        if not self.is_configured:
            raise ProviderNotConfiguredError("INCOIS PFZ credentials or base URL not configured.")

        url = f"{self.base_url}/pfz/advisories"
        params = {"lat": latitude, "lon": longitude}

        logger.info(f"[INCOIS Client] Requesting PFZ advisories for ({latitude:.3f}, {longitude:.3f})")

        try:
            import httpx
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(url, params=params, headers=self._get_auth_headers())
                if resp.status_code == 200:
                    raw = resp.json()
                    return self._parse_pfz_response(raw, latitude, longitude)
                elif resp.status_code in (401, 403):
                    raise ProviderUnavailableError("INCOIS PFZ authentication failed (invalid credentials).")
                else:
                    raise ProviderUnavailableError(f"INCOIS PFZ service returned HTTP {resp.status_code}")
        except httpx.TimeoutException:
            raise ProviderUnavailableError(f"INCOIS PFZ request timed out after {self.timeout}s.")
        except httpx.RequestError as e:
            raise ProviderUnavailableError(f"Failed to connect to INCOIS PFZ service: {str(e)}")

    def _parse_ocean_response(self, raw: Dict[str, Any], default_lat: float, default_lon: float) -> INCOISOceanObservation:
        try:
            return INCOISOceanObservation(
                sector_name=raw.get("sector") or raw.get("location"),
                latitude=raw.get("latitude", default_lat),
                longitude=raw.get("longitude", default_lon),
                observation_time=raw.get("observation_time") or raw.get("timestamp"),
                valid_until=raw.get("valid_until"),
                sea_surface_temperature_c=raw.get("sst") or raw.get("sea_surface_temperature"),
                significant_wave_height_m=raw.get("wave_height") or raw.get("significant_wave_height"),
                swell_wave_period_s=raw.get("swell_period") or raw.get("swell_wave_period"),
                swell_wave_direction_deg=raw.get("swell_direction_deg"),
                swell_direction_text=raw.get("swell_direction"),
                sea_state=raw.get("sea_state") or raw.get("ocean_condition"),
                current_speed_m_s=raw.get("current_speed"),
                tide_status=raw.get("tide_status") or raw.get("tide"),
                high_wave_alert=raw.get("high_wave_alert"),
                suitability=raw.get("suitability", "Favorable"),
                raw_payload=raw
            )
        except Exception as e:
            raise MarineDataFormatError(f"Failed to parse INCOIS ocean payload: {str(e)}")

    def _parse_pfz_response(self, raw: Dict[str, Any], default_lat: float, default_lon: float) -> INCOISPFZResponse:
        try:
            raw_zones = raw.get("zones", [])
            records: List[INCOISPFZRecord] = []
            for z in raw_zones:
                records.append(
                    INCOISPFZRecord(
                        zone_id=z.get("zone_id") or z.get("id", "PFZ-1"),
                        name=z.get("name", "Oceanic Front"),
                        latitude=z.get("latitude", default_lat),
                        longitude=z.get("longitude", default_lon),
                        sector=z.get("sector", "Coastal"),
                        distance_km=float(z.get("distance_km", 20.0)),
                        direction=z.get("direction", "NE"),
                        sst_c=float(z.get("sst") or z.get("sea_surface_temperature", 28.5)),
                        chlorophyll=str(z.get("chlorophyll", "Moderate")),
                        suitability=z.get("suitability", "Favorable"),
                        dominant_species=z.get("dominant_species", ["Pelagic", "Tuna", "Mackerel"]),
                        depth_meters=int(z.get("depth_meters", 40)),
                        valid_from=z.get("valid_from"),
                        valid_until=z.get("valid_until")
                    )
                )
            nearest = records[0] if records else None
            return INCOISPFZResponse(
                advisory_id=raw.get("advisory_id"),
                advisory_date=raw.get("advisory_date") or raw.get("timestamp"),
                valid_until=raw.get("valid_until"),
                total_active_zones=len(records),
                zones=records,
                nearest_zone=nearest,
                raw_payload=raw
            )
        except Exception as e:
            raise MarineDataFormatError(f"Failed to parse INCOIS PFZ payload: {str(e)}")
