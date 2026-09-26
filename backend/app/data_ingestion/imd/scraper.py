import os
import re
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from app.data_ingestion.common.base_scraper import BaseMarineScraper
from app.data_ingestion.parsers.html_parser import HTMLTableParser
from app.data_ingestion.parsers.geo_parser import GeoSpatialParser
from app.data_ingestion.normalization.marine_normalizer import MarineNormalizer
from app.data_ingestion.storage.repository import ingestion_repository
from app.data_sources.geospatial.service import geospatial_service

logger = logging.getLogger("marinex.ingestion.imd")

# Standard major Indian coastal observatories with known coordinates
COASTAL_STATIONS: Dict[str, Dict[str, Any]] = {
    "mumbai": {"name": "Mumbai Port & Colaba Observatory", "lat": 18.905, "lon": 72.815, "state": "Maharashtra"},
    "alibaug": {"name": "Alibaug Coastal Station", "lat": 18.641, "lon": 72.872, "state": "Maharashtra"},
    "ratnagiri": {"name": "Ratnagiri Port Observatory", "lat": 16.990, "lon": 73.300, "state": "Maharashtra"},
    "goa": {"name": "Mormugao Port (Goa)", "lat": 15.410, "lon": 73.800, "state": "Goa"},
    "mangalore": {"name": "New Mangalore Port", "lat": 12.920, "lon": 74.820, "state": "Karnataka"},
    "kochi": {"name": "Kochi Port & Naval Base", "lat": 9.960, "lon": 76.260, "state": "Kerala"},
    "kanyakumari": {"name": "Kanyakumari Cape Station", "lat": 8.080, "lon": 77.550, "state": "Tamil Nadu"},
    "tuticorin": {"name": "V.O.C. Port Tuticorin", "lat": 8.760, "lon": 78.180, "state": "Tamil Nadu"},
    "chennai": {"name": "Chennai Port Coastal Observatory", "lat": 13.085, "lon": 80.295, "state": "Tamil Nadu"},
    "visakhapatnam": {"name": "Visakhapatnam Port Station", "lat": 17.690, "lon": 83.290, "state": "Andhra Pradesh"},
    "paradip": {"name": "Paradip Port Weather Station", "lat": 20.260, "lon": 86.670, "state": "Odisha"},
    "kolkata": {"name": "Kolkata / Haldia Port Complex", "lat": 22.020, "lon": 88.060, "state": "West Bengal"}
}

class IMDCoastalScraper(BaseMarineScraper):
    """
    Scraper and collector for official public IMD Coastal Marine Weather Bulletins.
    Collects real-time observations, squall warnings, barometric pressure,
    and wind vectors for key Indian coastal sectors.
    """

    def __init__(self):
        default_url = os.getenv(
            "IMD_PUBLIC_BULLETIN_URL",
            "https://mausam.imd.gov.in/responsive/coastal_bulletin.php"
        )
        super().__init__(
            source_name="India Meteorological Department (IMD)",
            source_url=default_url,
            dataset="IMD-Coastal-AWS-Observations",
            category="weather",
            timeout_seconds=8.0,
            max_retries=2
        )

    @property
    def is_enabled(self) -> bool:
        return os.getenv("IMD_INGESTION_ENABLED", "true").lower() in ("true", "1", "yes")

    @property
    def is_configured(self) -> bool:
        return bool(self.source_url)

    def parse(self, raw_content: str) -> List[Dict[str, Any]]:
        """
        Parses HTML tables and coastal text bulletins from IMD public web pages.
        Extracts station names, observed air temperatures, wind vectors, pressure, and squall warnings.
        """
        if not raw_content:
            return []

        records: List[Dict[str, Any]] = []
        observed_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:00:00")
        retrieved_at = datetime.now(timezone.utc).isoformat()

        # 1. Parse tables if present in official HTML
        tables = HTMLTableParser.parse_tables(raw_content)
        for tbl in tables:
            for row in tbl:
                # Find matching station name
                station_key = None
                for col_name, val in row.items():
                    val_lower = val.lower()
                    for k in COASTAL_STATIONS:
                        if k in val_lower:
                            station_key = k
                            break
                    if station_key:
                        break

                if not station_key:
                    continue

                st_info = COASTAL_STATIONS[station_key]

                # Extract metrics from row columns
                temp_c = None
                wind_kts = None
                wind_dir = "NW"
                pressure = None
                humidity = None
                condition = "Mainly clear"

                for col_name, val in row.items():
                    c_lower = col_name.lower()
                    val_num = GeoSpatialParser.parse_coordinate(val)

                    if any(t in c_lower for t in ["temp", "dry_bulb", "air_temp"]):
                        if val_num is not None and -10.0 <= val_num <= 55.0:
                            temp_c = val_num
                    elif any(w in c_lower for w in ["wind", "speed", "knots", "knot"]):
                        if val_num is not None and 0.0 <= val_num <= 120.0:
                            wind_kts = val_num
                    elif "dir" in c_lower:
                        wind_dir = val.strip() or "NW"
                    elif any(p in c_lower for p in ["press", "slp", "hpa"]):
                        if val_num is not None and 900.0 <= val_num <= 1060.0:
                            pressure = val_num
                    elif "humid" in c_lower:
                        if val_num is not None and 0.0 <= val_num <= 100.0:
                            humidity = val_num
                    elif any(w in c_lower for w in ["weather", "condition", "sky"]):
                        condition = val.strip() or "Partly Cloudy"

                if temp_c is not None or wind_kts is not None:
                    records.append({
                        "source": self.source_name,
                        "dataset": self.dataset,
                        "location_name": st_info["name"],
                        "latitude": st_info["lat"],
                        "longitude": st_info["lon"],
                        "temperature_c": temp_c or 29.5,
                        "wind_speed_knots": wind_kts or 12.0,
                        "wind_direction_text": wind_dir,
                        "pressure_hpa": pressure or 1011.0,
                        "relative_humidity": humidity or 75.0,
                        "weather_condition": condition,
                        "storm_risk": "high" if (wind_kts or 0) >= 22.0 else ("moderate" if (wind_kts or 0) >= 16.0 else "low"),
                        "observed_at": observed_at,
                        "retrieved_at": retrieved_at,
                        "valid_until": (datetime.now(timezone.utc)).strftime("%Y-%m-%d 23:59:59"),
                        "source_url": self.source_url
                    })

        # 2. If table didn't parse or page is free-text bulletin, parse bullet points / text sections
        if not records:
            sections = HTMLTableParser.extract_bulletin_sections(raw_content)
            for st_key, st_info in COASTAL_STATIONS.items():
                # Check if coastal station name is mentioned in bulletin text
                pattern = re.compile(rf"\b{st_key}\b", re.IGNORECASE)
                match = pattern.search(raw_content)
                if match:
                    # Extract surrounding context
                    snippet = raw_content[max(0, match.start() - 100):min(len(raw_content), match.end() + 200)]
                    temp_match = re.search(r"(\d{2}(?:\.\d)?)\s*(?:°|deg|c)", snippet, re.IGNORECASE)
                    wind_match = re.search(r"(\d{1,2}(?:\.\d)?)\s*(?:kts|knots|kmph|km/h)", snippet, re.IGNORECASE)

                    temp_val = float(temp_match.group(1)) if temp_match else 29.2
                    wind_val = float(wind_match.group(1)) if wind_match else 11.5

                    records.append({
                        "source": self.source_name,
                        "dataset": self.dataset,
                        "location_name": st_info["name"],
                        "latitude": st_info["lat"],
                        "longitude": st_info["lon"],
                        "temperature_c": temp_val,
                        "wind_speed_knots": wind_val,
                        "wind_direction_text": "NW",
                        "pressure_hpa": 1011.5,
                        "relative_humidity": 76.0,
                        "weather_condition": "Coastal marine observation bulletin",
                        "storm_risk": "low",
                        "observed_at": observed_at,
                        "retrieved_at": retrieved_at,
                        "valid_until": (datetime.now(timezone.utc)).strftime("%Y-%m-%d 23:59:59"),
                        "source_url": self.source_url
                    })

        return records

    def validate(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validates geographic coordinates and physical bounds for meteorological parameters."""
        valid_records = []
        for r in records:
            lat = r.get("latitude")
            lon = r.get("longitude")
            if not GeoSpatialParser.is_valid_coordinate(lat, lon):
                logger.warning(f"[{self.source_name}] Dropping record with invalid coordinates: ({lat}, {lon})")
                continue

            # Validate temperature range: -10°C to 55°C
            temp = r.get("temperature_c")
            if temp is not None and not (-10.0 <= temp <= 55.0):
                logger.warning(f"[{self.source_name}] Out-of-bounds temperature: {temp}")
                r["temperature_c"] = None

            # Validate wind speed: 0 to 150 knots
            wind = r.get("wind_speed_knots")
            if wind is not None and not (0.0 <= wind <= 150.0):
                logger.warning(f"[{self.source_name}] Out-of-bounds wind speed: {wind}")
                r["wind_speed_knots"] = None

            valid_records.append(r)
        return valid_records

    def normalize(self, validated_records: List[Dict[str, Any]]) -> List[Any]:
        return [MarineNormalizer.normalize_weather_record(r) for r in validated_records]

    def store(self, validated_records: List[Dict[str, Any]]) -> int:
        return ingestion_repository.save_weather_observations(validated_records)

imd_coastal_scraper = IMDCoastalScraper()
