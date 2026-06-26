"""Singleton service for Baligh."""

from functools import lru_cache

from src.services.baligh import Baligh


@lru_cache(maxsize=1)
def get_baligh() -> Baligh:
    """Build the shared Baligh service once per process."""
    return Baligh()
