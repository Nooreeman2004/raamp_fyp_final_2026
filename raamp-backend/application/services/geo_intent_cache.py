# Application Layer - In-Memory TTL Cache for Geo-Intent Engine
# Singleton, thread-safe for asyncio (no locks needed — single event loop).
import logging
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)


class GeoIntentTTLCache:
    """
    Simple in-memory TTL cache designed for the Geo-Intent Marketing Engine.

    Keys are strings (built from location + keywords + radius).
    Values are cached with individual TTL values (seconds).

    Singleton: access via `geo_intent_cache` module-level instance.
    """

    def __init__(self) -> None:
        self._store: dict[str, dict] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, key: str) -> Optional[Any]:
        """Return cached value if present and not expired, else None."""
        entry = self._store.get(key)
        if entry is None:
            return None

        if time.monotonic() > entry["expires_at"]:
            logger.debug("Cache MISS (expired): %s", key)
            del self._store[key]
            return None

        logger.debug("Cache HIT: %s", key)
        return entry["value"]

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        """Store *value* under *key* with a TTL (seconds)."""
        self._store[key] = {
            "value": value,
            "expires_at": time.monotonic() + ttl_seconds,
        }
        logger.debug("Cache SET: %s  TTL=%ds", key, ttl_seconds)

    def invalidate(self, key: str) -> bool:
        """Remove a specific key. Returns True if it existed."""
        existed = key in self._store
        self._store.pop(key, None)
        if existed:
            logger.debug("Cache INVALIDATED: %s", key)
        return existed

    def clear(self) -> int:
        """Flush all entries. Returns number of entries removed."""
        count = len(self._store)
        self._store.clear()
        logger.info("Cache CLEARED — removed %d entries", count)
        return count

    # ------------------------------------------------------------------
    # TTL presets (seconds)
    # ------------------------------------------------------------------

    # Trends change quickly; keep short so velocity stays current.
    TRENDS_TTL: int = 10 * 60        # 10 minutes

    # Place density is stable over hours.
    PLACES_TTL: int = 6 * 60 * 60    # 6 hours

    # Weather changes every ~30 minutes.
    WEATHER_TTL: int = 30 * 60       # 30 minutes

    # ------------------------------------------------------------------
    # Cache-key builder
    # ------------------------------------------------------------------

    @staticmethod
    def build_key(latitude: float, longitude: float, keywords: list[str], radius: int) -> str:
        """Deterministic cache key from geo + intent parameters."""
        kw_part = "_".join(sorted(k.lower() for k in keywords))
        return f"geo:{latitude:.4f}:{longitude:.4f}:r{radius}:{kw_part}"


# ---------------------------------------------------------------------------
# Singleton instance — import this everywhere in the geo-intent module.
# ---------------------------------------------------------------------------
geo_intent_cache = GeoIntentTTLCache()
