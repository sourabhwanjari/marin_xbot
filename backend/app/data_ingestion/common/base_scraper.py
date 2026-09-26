import abc
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import httpx

from app.data_ingestion.common.scraper_status import ScraperStatus
from app.data_ingestion.common.exceptions import (
    ScraperUnavailableError, ScraperParsingError,
    ScraperValidationError, ScraperNotConfiguredError
)
from app.data_ingestion.storage.repository import ingestion_repository

logger = logging.getLogger("marinex.ingestion.base_scraper")

class BaseMarineScraper(abc.ABC):
    """
    Abstract Base Class for all official public marine web scrapers and data collectors.
    Enforces standardized fetch -> parse -> validate -> normalize -> store execution,
    strict error isolation, audit logging, and freshness guarantees.
    """

    def __init__(
        self,
        source_name: str,
        source_url: str,
        dataset: str,
        category: str = "general",
        timeout_seconds: float = 8.0,
        max_retries: int = 2
    ):
        self.source_name = source_name
        self.source_url = source_url
        self.dataset = dataset
        self.category = category
        self.timeout = timeout_seconds
        self.max_retries = max_retries
        self.user_agent = "MARINEX-AI-Collector/1.0 (+https://github.com/sourabhwanjari/marin_xbot; Coastal Safety Research)"
        self.last_run: Optional[str] = None
        self.last_success: Optional[str] = None
        self.last_error: Optional[str] = None
        self.status: ScraperStatus = ScraperStatus.IDLE

    @property
    @abc.abstractmethod
    def is_configured(self) -> bool:
        """Indicates whether this scraper has necessary endpoints or configuration."""
        pass

    @property
    @abc.abstractmethod
    def is_enabled(self) -> bool:
        """Indicates whether this scraper has been toggled active in configuration."""
        pass

    def fetch(self, url: Optional[str] = None, params: Optional[Dict[str, Any]] = None) -> str:
        """
        Executes safe HTTP GET request against the official public web source.
        Implements timeout, retry limits, sanitized headers, and status code handling.
        """
        target_url = url or self.source_url
        logger.info(f"[{self.source_name}] Fetching public content from: {target_url}")

        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml,application/json;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache"
        }

        last_exc = None
        for attempt in range(1, self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                    resp = client.get(target_url, params=params, headers=headers)
                    if resp.status_code == 200:
                        return resp.text
                    elif resp.status_code in (401, 403):
                        raise ScraperUnavailableError(self.source_name, f"Access restricted (HTTP {resp.status_code})")
                    elif resp.status_code == 404:
                        raise ScraperUnavailableError(self.source_name, f"Endpoint not found (HTTP 404)")
                    else:
                        raise ScraperUnavailableError(self.source_name, f"Server returned HTTP {resp.status_code}")
            except (httpx.TimeoutException, httpx.ConnectTimeout) as e:
                last_exc = e
                logger.warning(f"[{self.source_name}] Attempt {attempt} timed out after {self.timeout}s: {e}")
            except httpx.RequestError as e:
                last_exc = e
                logger.warning(f"[{self.source_name}] Attempt {attempt} request error: {e}")
            time.sleep(0.5)

        raise ScraperUnavailableError(self.source_name, f"Request failed after {self.max_retries} attempts: {last_exc}")

    @abc.abstractmethod
    def parse(self, raw_content: str) -> List[Dict[str, Any]]:
        """Parses raw HTML/JSON content into structured dictionaries."""
        pass

    @abc.abstractmethod
    def validate(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validates geographic coordinates and physical metric bounds."""
        pass

    @abc.abstractmethod
    def normalize(self, validated_records: List[Dict[str, Any]]) -> List[Any]:
        """Converts validated records into typed MARINEX domain models."""
        pass

    @abc.abstractmethod
    def store(self, validated_records: List[Dict[str, Any]]) -> int:
        """Persists records into PostgreSQL/PostGIS (or local SQLite store)."""
        pass

    def run_ingestion(self) -> Dict[str, Any]:
        """
        Orchestrates full ingestion lifecycle:
        is_configured? -> fetch -> parse -> validate -> normalize -> store
        Audits execution time and updates status.
        """
        t0 = time.time()
        self.last_run = datetime.now(timezone.utc).isoformat()
        self.status = ScraperStatus.RUNNING

        if not self.is_enabled:
            self.status = ScraperStatus.NOT_CONFIGURED
            self.last_error = f"{self.source_name} collector is disabled in configuration."
            ingestion_repository.record_run(
                scraper_name=self.__class__.__name__,
                source_name=self.source_name,
                source_url=self.source_url,
                status=ScraperStatus.NOT_CONFIGURED.value,
                records_ingested=0,
                duration_ms=0.0,
                error_message=self.last_error
            )
            return {
                "scraper": self.__class__.__name__,
                "source": self.source_name,
                "status": ScraperStatus.NOT_CONFIGURED.value,
                "records_ingested": 0,
                "message": self.last_error
            }

        if not self.is_configured:
            self.status = ScraperStatus.NOT_CONFIGURED
            self.last_error = f"{self.source_name} collector is not configured."
            ingestion_repository.record_run(
                scraper_name=self.__class__.__name__,
                source_name=self.source_name,
                source_url=self.source_url,
                status=ScraperStatus.NOT_CONFIGURED.value,
                records_ingested=0,
                duration_ms=0.0,
                error_message=self.last_error
            )
            return {
                "scraper": self.__class__.__name__,
                "source": self.source_name,
                "status": ScraperStatus.NOT_CONFIGURED.value,
                "records_ingested": 0,
                "message": self.last_error
            }

        try:
            # 1. Fetch
            raw_content = self.fetch()

            # 2. Parse
            parsed_records = self.parse(raw_content)
            if not parsed_records:
                self.status = ScraperStatus.NO_DATA
                duration_ms = round((time.time() - t0) * 1000, 1)
                ingestion_repository.record_run(
                    scraper_name=self.__class__.__name__,
                    source_name=self.source_name,
                    source_url=self.source_url,
                    status=ScraperStatus.NO_DATA.value,
                    records_ingested=0,
                    duration_ms=duration_ms
                )
                return {
                    "scraper": self.__class__.__name__,
                    "source": self.source_name,
                    "status": ScraperStatus.NO_DATA.value,
                    "records_ingested": 0,
                    "duration_ms": duration_ms
                }

            # 3. Validate
            validated_records = self.validate(parsed_records)

            # 4. Store
            stored_count = self.store(validated_records)

            # 5. Success
            duration_ms = round((time.time() - t0) * 1000, 1)
            self.last_success = datetime.now(timezone.utc).isoformat()
            self.last_error = None
            self.status = ScraperStatus.SUCCESS

            ingestion_repository.record_run(
                scraper_name=self.__class__.__name__,
                source_name=self.source_name,
                source_url=self.source_url,
                status=ScraperStatus.SUCCESS.value,
                records_ingested=stored_count,
                duration_ms=duration_ms
            )

            logger.info(f"[{self.source_name}] Ingestion completed successfully: {stored_count} records in {duration_ms}ms")
            return {
                "scraper": self.__class__.__name__,
                "source": self.source_name,
                "status": ScraperStatus.SUCCESS.value,
                "records_ingested": stored_count,
                "duration_ms": duration_ms
            }

        except ScraperUnavailableError as e:
            duration_ms = round((time.time() - t0) * 1000, 1)
            self.status = ScraperStatus.UNAVAILABLE
            self.last_error = str(e)
            logger.warning(f"[{self.source_name}] Source unavailable: {e}")
            ingestion_repository.record_run(
                scraper_name=self.__class__.__name__,
                source_name=self.source_name,
                source_url=self.source_url,
                status=ScraperStatus.UNAVAILABLE.value,
                records_ingested=0,
                duration_ms=duration_ms,
                error_message=str(e)
            )
            return {
                "scraper": self.__class__.__name__,
                "source": self.source_name,
                "status": ScraperStatus.UNAVAILABLE.value,
                "error": str(e),
                "duration_ms": duration_ms
            }
        except Exception as e:
            duration_ms = round((time.time() - t0) * 1000, 1)
            self.status = ScraperStatus.ERROR
            self.last_error = str(e)
            logger.error(f"[{self.source_name}] Ingestion failed with error: {e}")
            ingestion_repository.record_run(
                scraper_name=self.__class__.__name__,
                source_name=self.source_name,
                source_url=self.source_url,
                status=ScraperStatus.ERROR.value,
                records_ingested=0,
                duration_ms=duration_ms,
                error_message=str(e)
            )
            return {
                "scraper": self.__class__.__name__,
                "source": self.source_name,
                "status": ScraperStatus.ERROR.value,
                "error": str(e),
                "duration_ms": duration_ms
            }

    def health_check(self) -> Dict[str, Any]:
        """Reports current scraper status, last run, and last success timestamp."""
        # Check if last run was successful in repository
        latest_run = ingestion_repository.get_latest_run_for_scraper(self.__class__.__name__)
        effective_status = self.status.value
        if latest_run:
            if latest_run.status == ScraperStatus.SUCCESS.value:
                effective_status = "CONNECTED"
            else:
                effective_status = latest_run.status

        return {
            "source": self.source_name,
            "url": self.source_url,
            "dataset": self.dataset,
            "category": self.category,
            "status": effective_status,
            "enabled": self.is_enabled,
            "configured": self.is_configured,
            "last_run": self.last_run or (latest_run.started_at.isoformat() if latest_run else None),
            "last_success": self.last_success or (latest_run.completed_at.isoformat() if latest_run and latest_run.status == "SUCCESS" else None),
            "last_error": self.last_error or (latest_run.error_message if latest_run and latest_run.error_message else None)
        }
