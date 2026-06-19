"""Tier 1 - Static Arabic idioms cache.

Loads a hand-written YAML file mapping normalized context keys to
ranked suggestion lists. This cache is read-only at runtime.

The YAML file format is:
    - key: "ضرب عصفورين"
      suggestions:
        - word: "بحجر"
          score: 0.99

References:
- docs/contracts/nws-contract.md

Authors:
    - Akram Hany
"""

from pathlib import Path

import yaml

from src.services.nws.features.cache.base import BaseCacheLayer
from src.services.nws.schemas import NWSSource, Suggestion


class IdiomsCache(BaseCacheLayer):
    """Tier 1 static cache loaded from a hand-written idioms YAML file.

    At first the entire YAML file is loaded into an in-memory
    dict keyed on the normalized context string. All lookups are O(1).
    """

    @property
    def source_tag(self) -> str:
        """Source tag for idiom cache suggestions."""
        return NWSSource.IDIOM_CACHE

    def __init__(self, idioms_path: Path) -> None:
        """Initialize and load the idioms cache from disk.

        Args:
            idioms_path: Path to the idioms YAML file.
        """
        self._cache: dict[str, list[Suggestion]] = {}
        if idioms_path.exists():
            self._load(idioms_path)

    def _load(self, path: Path) -> None:
        """Parse the YAML file and populate the in-memory cache.

        Args:
            path: Path to the idioms YAML file.
        """
        with path.open(encoding="utf-8") as fh:
            entries = yaml.safe_load(fh) or []

        for entry in entries:
            key = entry["key"]
            suggestions = [
                Suggestion(
                    rank=i,
                    word=s["word"],
                    score=s.get("score", 1.0),
                    source=NWSSource.IDIOM_CACHE,
                )
                for i, s in enumerate(entry.get("suggestions", []))
            ]
            if suggestions:
                self._cache[key] = suggestions

    def lookup(self, key: str) -> list[Suggestion] | None:
        """Return suggestions if the key matches a known idiom context.

        Args:
            key: Normalized cache key string.

        Returns:
            A list of Suggestion objects, or None if no match.
        """
        return self._cache.get(key)
