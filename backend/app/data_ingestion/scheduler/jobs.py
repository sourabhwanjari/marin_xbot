import os
import asyncio
import logging
from typing import Dict, Any, Optional
from app.data_ingestion.common.scraper_registry import scraper_registry

logger = logging.getLogger("marinex.ingestion.scheduler")

class IngestionScheduler:
    """
    Asynchronous background scheduler for periodic marine web data ingestion.
    Runs non-blocking tasks respecting each official portal's bulletin publication frequency.
    """

    def __init__(self):
        self._running = False
        self._tasks = []
        # Configurable intervals from environment (seconds)
        self.imd_interval = int(os.getenv("IMD_SCRAPE_INTERVAL", "3600"))          # 1 hour
        self.ocean_interval = int(os.getenv("INCOIS_OCEAN_SCRAPE_INTERVAL", "7200")) # 2 hours
        self.pfz_interval = int(os.getenv("INCOIS_PFZ_SCRAPE_INTERVAL", "14400"))    # 4 hours
        self.mosdac_interval = int(os.getenv("MOSDAC_SCRAPE_INTERVAL", "86400"))    # 24 hours

    @property
    def is_enabled(self) -> bool:
        return os.getenv("INGESTION_SCHEDULER_ENABLED", "true").lower() in ("true", "1", "yes")

    async def _run_scraper_loop(self, scraper_key: str, interval_seconds: int):
        """Periodic execution loop for an individual scraper."""
        logger.info(f"[IngestionScheduler] Starting loop for '{scraper_key}' (Interval: {interval_seconds}s)")
        # Short initial delay to allow FastAPI startup to finish
        await asyncio.sleep(5)

        while self._running:
            try:
                logger.info(f"[IngestionScheduler] Executing scheduled run for '{scraper_key}'")
                loop = asyncio.get_event_loop()
                # Run sync scraper in executor to prevent blocking async event loop
                res = await loop.run_in_executor(None, scraper_registry.run_scraper, scraper_key)
                logger.info(f"[IngestionScheduler] Finished '{scraper_key}': status={res.get('status')}, records={res.get('records_ingested', 0)}")
            except Exception as e:
                logger.error(f"[IngestionScheduler] Error executing scheduled scraper '{scraper_key}': {e}")

            # Wait for next scheduled run
            try:
                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                break

    def start(self):
        """Starts background scheduled ingestion tasks."""
        if self._running:
            return
        if not self.is_enabled:
            logger.info("[IngestionScheduler] Scheduler is disabled via INGESTION_SCHEDULER_ENABLED=false")
            return

        self._running = True
        logger.info("[IngestionScheduler] Launching background marine data ingestion scheduler")

        self._tasks.append(asyncio.create_task(self._run_scraper_loop("imd", self.imd_interval)))
        self._tasks.append(asyncio.create_task(self._run_scraper_loop("incois_ocean", self.ocean_interval)))
        self._tasks.append(asyncio.create_task(self._run_scraper_loop("incois_pfz", self.pfz_interval)))
        self._tasks.append(asyncio.create_task(self._run_scraper_loop("mosdac", self.mosdac_interval)))

    def stop(self):
        """Stops background tasks."""
        if not self._running:
            return
        self._running = False
        for t in self._tasks:
            t.cancel()
        self._tasks.clear()
        logger.info("[IngestionScheduler] Background ingestion scheduler stopped")

ingestion_scheduler = IngestionScheduler()
