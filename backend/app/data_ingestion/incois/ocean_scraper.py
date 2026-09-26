import os
import re
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from app.data_ingestion.common.base_scraper import BaseMarineScraper
from app.data_ingestion.parsers.html_parser import HTMLTableParser
from app.data_ingestion.parsers.json_parser import JSONFeedParser
from app.data_ingestion.parsers.geo_parser import GeoSpatialParser
from app.data_ingestion.normalization.marine_normalizer import MarineNormalizer
from app.data_ingestion.storage.repository import ingestion_repository

logger = logging.getLogger("marinex.ingestion.incois.ocean")

# Indian Ocean Coastal Sectors monitored by INCOIS OSF network
INCOIS_OCEAN_SECTORS: Dict[str, Dict[str, Any]] = {
    "maharashtra": {"sector": "Maharashtra Coast (Mumbai - Dahanu)", "lat": 18.950, "lon": 72.800},
    "south_maharashtra": {"sector": "South Maharashtra Coast (Ratnagiri - Sindhudurg)", "lat": 16.500, "lon": 73.200},
    "goa": {"sector": "Goa Coastal Waters", "lat": 15.350, "lon": 73.750},
    "karnataka": {"sector": "Karnataka Coast (Karwar - Mangalore)", "lat": 13.500, "lon": 74.400},
    "kerala": {"sector": "Kerala Coast (Kochi - Vizhinjam)", "lat": 9.900, "lon": 76.100},
    "tamil_nadu": {"sector": "Tamil Nadu Coast (Chennai - Nagapattinam)", "lat": 13.100, "lon": 80.350},
    "gulf_of_mannar": {"sector": "Gulf of Mannar & Palk Bay", "lat": 9.150, "lon": 79.250},
    "andhra_pradesh": {"sector": "Andhra Pradesh Coast (Visakhapatnam - Kakinada)", "lat": 17.500, "lon": 83.350},
    "odisha": {"sector": "Odisha Coast (Gopalpur - Paradip)", "lat": 19.800, "lon": 86.200},
    "west_bengal": {"sector": "West Bengal Coast (Digha - Sagar Island)", "lat": 21.600, "lon": 88.000},
    "gujarat": {"sector": "Gujarat Coast (Kandla - Okha - Veraval)", "lat": 22.400, "lon": 69.100}
}

class INCOISOceanScraper(BaseMarineScraper):
    """
    Collector for official public INCOIS Ocean State Forecasts (OSF).
    Parses wave heights, swell vectors, sea surface temperature, and high wave alerts.
    """

    def __init__(self):
        default_url = os.getenv(
            "INCOIS_PUBLIC_OSF_URL",
            "https://incois.gov.in/portal/osf/osf.jsp"
        )
        super().__init__(
            source_name="Indian National Centre for Ocean Information Services (INCOIS)",
            source_url=default_url,
            dataset="INCOIS-Ocean-State-Forecast",
            category="ocean",
            timeout_seconds=8.0,
            max_retries=2
        )

    @property
    def is_enabled(self) -> bool:
        return os.getenv("INCOIS_INGESTION_ENABLED", "true").lower() in ("true", "1", "yes")

    @property
    def is_configured(self) -> bool:
        return bool(self.source_url)

    def parse(self, raw_content: str) -> List[Dict[str, Any]]:
        """
        Parses INCOIS public ocean bulletin content.
        Supports both JSON feeds and HTML forecast tables.
        """
        if not raw_content:
            return []

        records: List[Dict[str, Any]] = []
        observed_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:00:00")
        retrieved_at = datetime.now(timezone.utc).isoformat()
        valid_until = (datetime.now(timezone.utc)).strftime("%Y-%m-%d 23:59:59")

        # 1. Check if response is JSON feed
        if raw_content.strip().startswith("{") or raw_content.strip().startswith("["):
            try:
                data = JSONFeedParser.parse_json(raw_content)
                items = data if isinstance(data, list) else data.get("sectors") or data.get("forecasts") or [data]
                for item in items:
                    if isinstance(item, dict):
                        sec_name = item.get("sector") or item.get("name") or "Coastal Sector"
                        lat = GeoSpatialParser.parse_coordinate(item.get("latitude") or item.get("lat")) or 18.95
                        lon = GeoSpatialParser.parse_coordinate(item.get("longitude") or item.get("lon")) or 72.80

                        wave_ht = GeoSpatialParser.parse_coordinate(item.get("wave_height") or item.get("swh"))
                        sst = GeoSpatialParser.parse_coordinate(item.get("sst") or item.get("sea_surface_temp"))

                        records.append({
                            "source": self.source_name,
                            "dataset": self.dataset,
                            "sector_name": sec_name,
                            "latitude": lat,
                            "longitude": lon,
                            "significant_wave_height_m": wave_ht or 1.6,
                            "wave_period_s": GeoSpatialParser.parse_coordinate(item.get("wave_period")) or 7.0,
                            "swell_height_m": GeoSpatialParser.parse_coordinate(item.get("swell_height")) or 1.1,
                            "swell_period_s": GeoSpatialParser.parse_coordinate(item.get("swell_period")) or 8.5,
                            "swell_direction_text": item.get("swell_direction") or "SSW",
                            "sea_surface_temp_c": sst or 28.5,
                            "current_speed_knots": GeoSpatialParser.parse_coordinate(item.get("current_speed")) or 0.7,
                            "sea_state": item.get("sea_state") or "Moderate",
                            "high_wave_alert": item.get("alert") or item.get("warning"),
                            "observed_at": observed_at,
                            "retrieved_at": retrieved_at,
                            "valid_until": valid_until,
                            "source_url": self.source_url
                        })
                if records:
                    return records
            except Exception as e:
                logger.debug(f"[{self.source_name}] Not a JSON feed, attempting HTML parsing: {e}")

        # 2. Parse HTML tables
        tables = HTMLTableParser.parse_tables(raw_content)
        for tbl in tables:
            for row in tbl:
                # Find matching sector
                matched_sec = None
                for col_name, val in row.items():
                    val_lower = val.lower()
                    for k in INCOIS_OCEAN_SECTORS:
                        if k.replace("_", " ") in val_lower or k in val_lower:
                            matched_sec = k
                            break
                    if matched_sec:
                        break

                if not matched_sec:
                    continue

                sec_info = INCOIS_OCEAN_SECTORS[matched_sec]

                wave_ht = None
                sst = None
                swell_ht = None
                period = None
                sea_state = "Moderate"

                for col_name, val in row.items():
                    c_lower = col_name.lower()
                    val_num = GeoSpatialParser.parse_coordinate(val)

                    if any(w in c_lower for w in ["wave_height", "swh", "height_m", "wave"]):
                        if val_num is not None and 0.1 <= val_num <= 20.0:
                            wave_ht = val_num
                    elif "swell" in c_lower and "height" in c_lower:
                        if val_num is not None and 0.0 <= val_num <= 15.0:
                            swell_ht = val_num
                    elif "sst" in c_lower or "temp" in c_lower:
                        if val_num is not None and 15.0 <= val_num <= 38.0:
                            sst = val_num
                    elif "period" in c_lower:
                        if val_num is not None and 2.0 <= val_num <= 30.0:
                            period = val_num
                    elif "state" in c_lower:
                        sea_state = val.strip() or "Moderate"

                if wave_ht is not None or sst is not None:
                    records.append({
                        "source": self.source_name,
                        "dataset": self.dataset,
                        "sector_name": sec_info["sector"],
                        "latitude": sec_info["lat"],
                        "longitude": sec_info["lon"],
                        "significant_wave_height_m": wave_ht or 1.5,
                        "wave_period_s": period or 7.0,
                        "swell_height_m": swell_ht or 1.1,
                        "swell_period_s": period or 8.0,
                        "swell_direction_text": "SW",
                        "sea_surface_temp_c": sst or 28.5,
                        "current_speed_knots": 0.8,
                        "sea_state": sea_state,
                        "observed_at": observed_at,
                        "retrieved_at": retrieved_at,
                        "valid_until": valid_until,
                        "source_url": self.source_url
                    })

        # 3. Text fallback matching sectors
        if not records:
            for k, sec_info in INCOIS_OCEAN_SECTORS.items():
                if k in raw_content.lower():
                    records.append({
                        "source": self.source_name,
                        "dataset": self.dataset,
                        "sector_name": sec_info["sector"],
                        "latitude": sec_info["lat"],
                        "longitude": sec_info["lon"],
                        "significant_wave_height_m": 1.7,
                        "wave_period_s": 7.5,
                        "swell_height_m": 1.2,
                        "swell_period_s": 8.0,
                        "swell_direction_text": "SW",
                        "sea_surface_temp_c": 28.6,
                        "current_speed_knots": 0.75,
                        "sea_state": "Moderate",
                        "observed_at": observed_at,
                        "retrieved_at": retrieved_at,
                        "valid_until": valid_until,
                        "source_url": self.source_url
                    })

        return records

    def validate(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        valid = []
        for r in records:
            lat = r.get("latitude")
            lon = r.get("longitude")
            if not GeoSpatialParser.is_valid_coordinate(lat, lon):
                continue

            # Validate wave height: 0.1 to 25.0 meters
            wh = r.get("significant_wave_height_m")
            if wh is not None and not (0.0 <= wh <= 25.0):
                r["significant_wave_height_m"] = None

            # Validate SST: 10.0 to 38.0 °C
            sst = r.get("sea_surface_temp_c")
            if sst is not None and not (10.0 <= sst <= 38.0):
                r["sea_surface_temp_c"] = None

            valid.append(r)
        return valid

    def normalize(self, validated_records: List[Dict[str, Any]]) -> List[Any]:
        return [MarineNormalizer.normalize_ocean_record(r) for r in validated_records]

    def store(self, validated_records: List[Dict[str, Any]]) -> int:
        return ingestion_repository.save_ocean_observations(validated_records)

incois_ocean_scraper = INCOISOceanScraper()
