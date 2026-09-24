import os
import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("marinex.gateway.cache")

class MarineCache:
    """
    Lightweight in-memory cache with configurable TTLs to avoid redundant
    external requests and respect provider rate limits.
    Phase 5B compliant.
    """
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.weather_ttl = int(os.getenv("WEATHER_CACHE_TTL", "900"))      # 15 mins default
        self.ocean_ttl = int(os.getenv("OCEAN_CACHE_TTL", "1800"))         # 30 mins default
        self.pfz_ttl = int(os.getenv("PFZ_CACHE_TTL", "3600"))             # 1 hr default
        self.satellite_ttl = int(os.getenv("SATELLITE_CACHE_TTL", "3600")) # 1 hr default
        self.default_ttl = 600

    def _get_ttl(self, category: str) -> int:
        cat = category.lower()
        if "weather" in cat:
            return self.weather_ttl
        elif "ocean" in cat:
            return self.ocean_ttl
        elif "pfz" in cat:
            return self.pfz_ttl
        elif "satellite" in cat:
            return self.satellite_ttl
        return self.default_ttl

    def get(self, key: str, category: str = "default") -> Optional[Any]:
        if key in self._cache:
            entry = self._cache[key]
            ttl = self._get_ttl(category)
            if time.time() - entry["timestamp"] < ttl:
                logger.debug(f"[Cache HIT] {category} :: {key}")
                return entry["data"]
            else:
                logger.debug(f"[Cache EXPIRED] {category} :: {key}")
                del self._cache[key]
        return None

    def set(self, key: str, data: Any, category: str = "default") -> None:
        self._cache[key] = {
            "timestamp": time.time(),
            "data": data,
            "category": category
        }
        logger.debug(f"[Cache SET] {category} :: {key}")

    def clear(self) -> None:
        self._cache.clear()

marine_cache = MarineCache()
