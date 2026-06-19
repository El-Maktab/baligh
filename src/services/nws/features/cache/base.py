"""Abstract base class for NWS cache layers.

Authors:
    - Akram Hany
"""

from abc import ABC, abstractmethod

from src.services.nws.schemas import Suggestion


class BaseCacheLayer(ABC):
    """Abstract base class for a single NWS cache tier.

    Each concrete tier (idioms, phrases, user LRU) must implement
    the *lookup* method. The `update` method is optional as only 
    Tier 3 cache needs it.
    """

    @property
    @abstractmethod
    def source_tag(self) -> str:
        """The NWSSource tag that identifies this tier in suggestions."""

    @abstractmethod
    def lookup(self, key: str) -> list[Suggestion] | None:
        """Look up suggestions for the given cache key.

        Args:
            key: Normalized cache key string.

        Returns:
            A list of Suggestion objects if the key is found,
            or None if it is not in this tier.
        """

    def update(self, key: str, suggestions: list[Suggestion]) -> None:
        """Store suggestions for the given key.

        only Tier 3 (user LRU) overrides this.

        Args:
            key: Normalized cache key string.
            suggestions: Ranked list of suggestions to store.
        """
