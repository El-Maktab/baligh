"""Tier 3 - Per-user in-memory LRU cache.

Stores the most recent NWS results per normalized context key so that
repeated identical inputs are served from memory without hitting the
model or trie. The cache is in-memory only and resets on service restart.

References:
- docs/contracts/nws-contract.md

Authors:
    - Akram Hany
"""

from collections import OrderedDict

from src.services.nws.features.cache.base import BaseCacheLayer
from src.services.nws.schemas import NWSSource, Suggestion


class UserLRUCache(BaseCacheLayer):
    """Tier 3 in-memory LRU cache for user-specific suggestion patterns.

    Uses the OrderedDict where the most recently accessed key
    is moved to the end. When the cache is full, the least recently used
    entry (at the front) is evicted.

    Attributes:
        _maxsize: Maximum number of entries before eviction.
        _cache: OrderedDict storing key -> suggestions mappings.
    """

    @property
    def source_tag(self) -> str:
        """Source tag for user LRU cache suggestions."""
        return NWSSource.USER_CACHE

    def __init__(self, maxsize: int = 1000) -> None:
        """Initialize the LRU cache.

        Args:
            maxsize: Maximum number of cache entries. When exceeded,
                the least recently used entry is evicted.
        """
        self._maxsize = maxsize
        self._cache: OrderedDict[str, list[Suggestion]] = OrderedDict()

    def lookup(self, key: str) -> list[Suggestion] | None:
        """Return cached suggestions and mark the key as recently used.

        Args:
            key: Normalized cache key string.

        Returns:
            A list of Suggestion objects, or None if not cached.
        """
        if key not in self._cache:
            return None
        # Move to end to mark as most recently used
        self._cache.move_to_end(key)
        return self._cache[key]

    def update(self, key: str, suggestions: list[Suggestion]) -> None:
        """Store suggestions for the key, evicting LRU entry if at capacity.

        Args:
            key: Normalized cache key string.
            suggestions: Ranked list of suggestions to store.
        """
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = suggestions
        if len(self._cache) > self._maxsize:
            # Evict the least recently used entry (front of OrderedDict)
            self._cache.popitem(last=False)

    def __len__(self) -> int:
        """Return the number of entries currently in the cache."""
        return len(self._cache)
