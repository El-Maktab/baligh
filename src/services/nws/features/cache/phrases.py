"""Tier 2 - Static famous phrases cache.

Loads a hand-written YAML file mapping normalized context keys to
ranked suggestion lists for common collocations, religious phrases,
and high-frequency Arabic phrases. Read-only at runtime.

The YAML file format is identical to idioms.yaml:
    - key: "بسم الله الرحمن"
      suggestions:
        - word: "الرحيم"
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


class PhrasesCache(BaseCacheLayer):
    """Tier 2 static cache loaded from a hand-written phrases YAML file.

    Identical to the idioms cache part with only soruce_tag being different.
    """

    @property
    def source_tag(self) -> str:
        """Source tag for phrase cache suggestions."""
        return NWSSource.PHRASE_CACHE

    def __init__(self, phrases_path: Path) -> None:
        """Initialize and load the phrases cache from disk.

        Args:
            phrases_path: Path to the phrases YAML file.
        """
        self._cache: dict[str, list[Suggestion]] = {}
        if phrases_path.exists():
            self._load(phrases_path)

    def _load(self, path: Path) -> None:
        """Parse the YAML file and populate the in-memory cache.

        Args:
            path: Path to the phrases YAML file.
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
                    source=NWSSource.PHRASE_CACHE,
                )
                for i, s in enumerate(entry.get("suggestions", []))
            ]
            if suggestions:
                self._cache[key] = suggestions

    def lookup(self, key: str) -> list[Suggestion] | None:
        """Return suggestions via suffix-scan against the known phrase context.

        Iterativly searchs for the key given in the cache, starting by the full key
        length (all words in key), then progressively reduces the key length till
        either we find the key in cache and return the result, or we exit.

        Args:
            key: Normalized cache key string.

        Returns:
            A list of Suggestion objects from the first matching suffix,
            or None if all suffixes miss.
        """
        words = key.split()
        for start in range(len(words)):
            suffix = " ".join(words[start:])
            result = self._cache.get(suffix)
            if result is not None:
                return result
        return None
