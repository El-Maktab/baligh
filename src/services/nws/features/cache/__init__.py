"""NWS cache layer package.

Exposes the CacheManager as the primary interface for cache operations.

Authors:
    - Akram Hany
"""

from src.services.nws.features.cache.manager import CacheManager

__all__ = ["CacheManager"]
