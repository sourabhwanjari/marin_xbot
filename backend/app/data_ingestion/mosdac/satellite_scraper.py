import os
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from app.data_ingestion.common.base_scraper import BaseMarineScraper
from app.data_ingestion.common.scraper_status import ScraperStatus
from app.data_ingestion.normalization.marine_normalizer import MarineNormalizer
from app.data_ingestion.storage.repository import ingestion_repository

logger = logging.getLogger("marinex.ingestion.mosdac")

class MOSDACSatelliteScraper(BaseMarineScraper):
    """
    Collector for official public ISRO MOSDAC Satellite Earth Observation granules.
    Strictly follows official source rules:
    - If credentials (MOSDAC_USERNAME, MOSDAC_PASSWORD) are missing, strictly returns NOT_CONFIGURED.
    - Never bypasses authentication, CAPTCHA, or rate limits.
    """

    def __init__(self):
        default_url = os.getenv("MOSDAC_BASE_URL", "https://api.mosdac.gov.in")
        super().__init__(
            source_name="ISRO MOSDAC Satellite Archival Centre",
            source_url=default_url,
            dataset=os.getenv("MOSDAC_DATASET_ID", "OS3_SST_L3"),
            category="satellite",
            timeout_seconds=8.0,
            max_retries=1
        )

    @property
    def is_enabled(self) -> bool:
        return os.getenv("MOSDAC_INGESTION_ENABLED", "false").lower() in ("true", "1", "yes")

    @property
    def is_configured(self) -> bool:
        user = os.getenv("MOSDAC_USERNAME", "").strip()
        pwd = os.getenv("MOSDAC_PASSWORD", "").strip()
        return bool(user and pwd)

    def parse(self, raw_content: str) -> List[Dict[str, Any]]:
        """Parses satellite earth observation granules if valid JSON is returned."""
        if not raw_content:
            return []

        import json
        records = []
        retrieved_at = datetime.now(timezone.utc).isoformat()
        try:
            data = json.loads(raw_content)
            granules = data.get("granules") or data.get("items") or []
            for g in granules:
                records.append({
                    "source": self.source_name,
                    "dataset_id": self.dataset,
                    "granule_id": g.get("granule_id") or g.get("id", "OS3_GRANULE_01"),
                    "satellite_mission": g.get("satellite", "ISRO Oceansat-3"),
                    "sensor": g.get("sensor", "OCM-3 / SSTM"),
                    "product_name": g.get("product", "Sea Surface Temperature (SST)"),
                    "pass_timestamp": g.get("pass_time") or datetime.now(timezone.utc).isoformat(),
                    "spatial_resolution_km": float(g.get("resolution_km", 1.0)),
                    "cloud_cover_percent": float(g.get("cloud_cover", 15.0)),
                    "sst_c": float(g.get("sst", 28.5)) if g.get("sst") else None,
                    "download_url": g.get("download_url") or "https://www.mosdac.gov.in",
                    "retrieved_at": retrieved_at
                })
        except Exception as e:
            logger.warning(f"[{self.source_name}] Failed to parse satellite catalog payload: {e}")

        return records

    def validate(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [r for r in records if r.get("granule_id")]

    def normalize(self, validated_records: List[Dict[str, Any]]) -> List[Any]:
        return [MarineNormalizer.normalize_satellite_record(r) for r in validated_records]

    def store(self, validated_records: List[Dict[str, Any]]) -> int:
        return ingestion_repository.save_satellite_granules(validated_records)

mosdac_satellite_scraper = MOSDACSatelliteScraper()
