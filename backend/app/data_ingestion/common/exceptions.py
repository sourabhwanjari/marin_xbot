class IngestionError(Exception):
    """Base exception for marine data ingestion failures."""
    pass

class ScraperUnavailableError(IngestionError):
    """Raised when an official public source endpoint is unreachable or times out."""
    def __init__(self, source_name: str, reason: str = ""):
        self.source_name = source_name
        self.reason = reason
        super().__init__(f"Public source '{source_name}' is unavailable: {reason}" if reason else f"Public source '{source_name}' is unavailable")

class ScraperParsingError(IngestionError):
    """Raised when HTML/JSON/XML payload structure cannot be parsed."""
    def __init__(self, source_name: str, message: str = ""):
        self.source_name = source_name
        super().__init__(f"Failed to parse content from '{source_name}': {message}")

class ScraperValidationError(IngestionError):
    """Raised when parsed data fails validation (invalid coordinates, out-of-bounds metrics)."""
    def __init__(self, source_name: str, field: str, value: any):
        self.source_name = source_name
        self.field = field
        self.value = value
        super().__init__(f"Validation failed for '{source_name}' on field '{field}' with value '{value}'")

class ScraperNotConfiguredError(IngestionError):
    """Raised when scraper requires environment settings or credentials that are missing."""
    def __init__(self, source_name: str, missing: str = ""):
        self.source_name = source_name
        self.missing = missing
        super().__init__(f"Scraper '{source_name}' is not configured: missing {missing}" if missing else f"Scraper '{source_name}' is not configured")
