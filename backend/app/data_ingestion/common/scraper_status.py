from enum import Enum
from datetime import datetime, timezone
from typing import Optional, Tuple

class ScraperStatus(str, Enum):
    """Operational status of a scheduled marine web scraper or collector."""
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    CONNECTED = "CONNECTED"      # Successfully collected and ingested latest data
    SUCCESS = "SUCCESS"
    UNAVAILABLE = "UNAVAILABLE"  # Public site timed out or network error
    ERROR = "ERROR"              # Parsing or schema validation failure
    NOT_CONFIGURED = "NOT_CONFIGURED"  # Missing credentials or disabled in config
    STALE = "STALE"              # Data collected is beyond valid freshness threshold
    NO_DATA = "NO_DATA"          # Source page reachable but contains no new bulletin/records

    def __eq__(self, other):
        if isinstance(other, str):
            return self.value.upper() == other.upper() or self.name.upper() == other.upper()
        return super().__eq__(other)

    def __hash__(self):
        return super().__hash__()


class FreshnessStatus(str, Enum):
    """Categorized data freshness based on observation time and valid window."""
    FRESH = "FRESH"      # Observed within last 3h (weather) or 6h (ocean/PFZ)
    RECENT = "RECENT"    # Observed within last 12h
    STALE = "STALE"      # Older than 12-24h
    EXPIRED = "EXPIRED"  # Exceeded valid_until deadline
    UNKNOWN = "UNKNOWN"  # Missing or unparseable timestamp

    def __eq__(self, other):
        if isinstance(other, str):
            return self.value.upper() == other.upper() or self.name.upper() == other.upper()
        return super().__eq__(other)

    def __hash__(self):
        return super().__hash__()


def parse_iso_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """Safely parses ISO 8601 or common marine bulletin date formats into UTC datetime."""
    if not dt_str or dt_str.upper() in ("UNAVAILABLE", "UNKNOWN", "NONE"):
        return None
    try:
        # Try direct ISO format
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        pass

    # Try common bulletin date formats: YYYY-MM-DD HH:MM:SS, DD-MM-YYYY, etc.
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
        "%d-%m-%Y %H:%M:%S",
        "%d-%m-%Y",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(dt_str, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except Exception:
            continue
    return None


def calculate_freshness(
    observed_at: Optional[str] = None,
    valid_until: Optional[str] = None,
    category: str = "weather"
) -> Tuple[FreshnessStatus, str]:
    """
    Calculates freshness status and human-readable explanation based on
    observation time and validity window.
    """
    now = datetime.now(timezone.utc)

    # 1. Check expiration if valid_until is set
    valid_dt = parse_iso_datetime(valid_until)
    if valid_dt and now > valid_dt:
        hours_expired = round((now - valid_dt).total_seconds() / 3600.0, 1)
        return FreshnessStatus.EXPIRED, f"Bulletin validity expired {hours_expired}h ago (Valid until: {valid_until})"

    # 2. Check observation age
    obs_dt = parse_iso_datetime(observed_at)
    if not obs_dt:
        return FreshnessStatus.UNKNOWN, "Observation timestamp unavailable from source bulletin"

    age_hours = (now - obs_dt).total_seconds() / 3600.0

    # Category-specific thresholds
    if category.lower() in ("weather", "meteorological"):
        fresh_thresh = 3.0
        recent_thresh = 8.0
        stale_thresh = 24.0
    elif category.lower() in ("ocean", "hydrodynamic"):
        fresh_thresh = 6.0
        recent_thresh = 12.0
        stale_thresh = 24.0
    elif category.lower() in ("pfz", "fisheries"):
        fresh_thresh = 12.0
        recent_thresh = 24.0
        stale_thresh = 48.0
    else:  # Satellite, GIS, etc.
        fresh_thresh = 12.0
        recent_thresh = 24.0
        stale_thresh = 72.0

    if age_hours <= fresh_thresh:
        return FreshnessStatus.FRESH, f"Fresh telemetry (Observed {age_hours:.1f}h ago)"
    elif age_hours <= recent_thresh:
        return FreshnessStatus.RECENT, f"Recent telemetry (Observed {age_hours:.1f}h ago)"
    elif age_hours <= stale_thresh:
        return FreshnessStatus.STALE, f"Stale telemetry (Observed {age_hours:.1f}h ago)"
    else:
        return FreshnessStatus.EXPIRED, f"Outdated telemetry (Observed {age_hours:.1f}h ago)"
