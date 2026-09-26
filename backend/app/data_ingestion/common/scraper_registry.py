import logging
from typing import Dict, List, Optional, Any
from app.data_ingestion.common.base_scraper import BaseMarineScraper
from app.data_ingestion.common.scraper_status import ScraperStatus
from app.data_ingestion.storage.repository import ingestion_repository
from app.data_ingestion.imd.scraper import imd_coastal_scraper
from app.data_ingestion.incois.ocean_scraper import incois_ocean_scraper
from app.data_ingestion.incois.pfz_scraper import incois_pfz_scraper
from app.data_ingestion.mosdac.satellite_scraper import mosdac_satellite_scraper

logger = logging.getLogger("marinex.ingestion.registry")

class ScraperRegistry:
    """
    Central Registry for all official public marine web scrapers.
    Orchestrates periodic collection runs, manual testing triggers,
    and reports operational ingestion health to API endpoints.
    """

    def __init__(self):
        self._scrapers: Dict[str, BaseMarineScraper] = {}
        self._bootstrap_scrapers()

    def _bootstrap_scrapers(self):
        self.register_scraper("imd", imd_coastal_scraper)
        self.register_scraper("incois_ocean", incois_ocean_scraper)
        self.register_scraper("incois_pfz", incois_pfz_scraper)
        self.register_scraper("mosdac", mosdac_satellite_scraper)

    def register_scraper(self, key: str, scraper: BaseMarineScraper):
        self._scrapers[key.lower()] = scraper
        logger.info(f"[ScraperRegistry] Registered scraper '{key}' ({scraper.source_name})")

    def get_scraper(self, key: str) -> Optional[BaseMarineScraper]:
        return self._scrapers.get(key.lower())

    def get_all_scrapers(self) -> Dict[str, BaseMarineScraper]:
        return self._scrapers

    def run_scraper(self, key: str) -> Dict[str, Any]:
        """Triggers manual ingestion run for a single scraper."""
        scraper = self.get_scraper(key)
        if not scraper:
            return {"error": f"Scraper '{key}' not found in registry", "status": "ERROR"}
        return scraper.run_ingestion()

    def run_all(self) -> Dict[str, Any]:
        """Triggers collection across all registered scrapers."""
        results = {}
        for key, scraper in self._scrapers.items():
            logger.info(f"[ScraperRegistry] Triggering ingestion for '{key}'")
            results[key] = scraper.run_ingestion()
        return results

    def get_status_report(self) -> Dict[str, Dict[str, Any]]:
        """
        Returns Phase 5B standard operational status report for GET /api/marine/ingestion/status.
        Reports:
        {
          "imd": {"status": "CONNECTED", "last_success": "...", "records_ingested": 12},
          "incois_ocean": {"status": "CONNECTED", "last_success": "..."},
          "incois_pfz": {"status": "CONNECTED", "last_success": "..."},
          "mosdac": {"status": "NOT_CONFIGURED", "reason": "Requires credentials"}
        }
        """
        report: Dict[str, Dict[str, Any]] = {}

        for key, scraper in self._scrapers.items():
            health = scraper.health_check()
            latest_run = ingestion_repository.get_latest_run_for_scraper(scraper.__class__.__name__)

            status_val = health["status"]
            last_success = health["last_success"]
            records_count = latest_run.records_ingested if latest_run else 0

            # If scraper is unconfigured/disabled
            if not scraper.is_enabled or not scraper.is_configured:
                status_val = "NOT_CONFIGURED"

            entry: Dict[str, Any] = {
                "source_name": scraper.source_name,
                "dataset": scraper.dataset,
                "status": status_val,
                "last_run": health["last_run"],
                "last_success": last_success,
                "records_ingested": records_count,
                "source_url": scraper.source_url
            }

            if status_val == "NOT_CONFIGURED":
                if "mosdac" in key:
                    entry["reason"] = "Official ISRO MOSDAC access requires credentials (MOSDAC_USERNAME, MOSDAC_PASSWORD). Automated access without authorization is restricted."
                elif not scraper.is_enabled:
                    entry["reason"] = f"Scraper is disabled in configuration."
                else:
                    entry["reason"] = f"Scraper endpoint or credentials not configured."

            if health.get("last_error"):
                entry["last_error"] = health["last_error"]

            report[key] = entry

        return report

scraper_registry = ScraperRegistry()
