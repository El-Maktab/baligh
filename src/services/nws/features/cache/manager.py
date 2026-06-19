"""CacheManager - coordinates all three NWS cache tiers.

Responsible for:
    1. Building normalized cache keys from token context and current fragment.
    2. Sequential lookup across Tier 1 -> Tier 2 -> Tier 3.
    3. Writing back model/trie results to Tier 3 after a cache miss.

References:
- docs/contracts/nws-contract.md

Authors:
    - Akram Hany
"""

from src.core.schemas import Token
from src.core.utils.arabic import loose_arabic_lookup_key
from src.services.nws.features.cache.idioms import IdiomsCache
from src.services.nws.features.cache.phrases import PhrasesCache
from src.services.nws.features.cache.user_lru import UserLRUCache
from src.services.nws.schemas import Suggestion


class CacheManager:
    """Coordinates lookup and update across all three NWS cache tiers.

    Tier 1 (idioms) and Tier 2 (phrases) are static read-only caches
    loaded from YAML files at startup. Tier 3 (user LRU) is updated
    dynamically after each cache miss.

    Attributes:
        _tier1: The static idioms cache.
        _tier2: The static famous phrases cache.
        _tier3: The per-user LRU cache.
        _context_window_size: Number of recent tokens used to build the key.
    """

    def __init__(
        self,
        tier1: IdiomsCache,
        tier2: PhrasesCache,
        tier3: UserLRUCache,
        context_window_size: int = 5,
    ) -> None:
        """Initialize the CacheManager.

        Args:
            tier1: IdiomsCache object.
            tier2: PhrasesCache object.
            tier3: UserLRUCache object.
            context_window_size: How many recent tokens to include in the key.
        """
        self._tier1 = tier1
        self._tier2 = tier2
        self._tier3 = tier3
        self._context_window_size = context_window_size

    ####################################################################
    # Key construction
    ####################################################################

    def build_key(
        self,
        tokens: list[Token],
        current_fragment: str | None,
    ) -> str:
        """Build a normalized cache key from a token.

        Applies Alif canonicalization to the last N tokens via
        `loose_arabic_lookup_key`, and joins them with spaces. For WAC
        mode, appends '|' between the tokens and the current_fragment.

        Args:
            tokens: Full token list.
            current_fragment: Incomplete word being typed, or None (NWP mode).

        Returns:
            A normalized string suitable for use as a cache key.

        Examples:
            NWP: tokens[-N:] forms -> "ذهب الطلاب الى"
            WAC: same context -> "ذهب الطلاب الى|المدرس"
        """
        last_N_tokens = tokens[-self._context_window_size :]
        normalized_forms = [loose_arabic_lookup_key(t.form) for t in last_N_tokens]
        key = " ".join(normalized_forms)
        if current_fragment is not None:
            key = f"{key}|{loose_arabic_lookup_key(current_fragment)}"
        return key

    ####################################################################
    # Lookup
    ####################################################################

    def lookup(self, key: str) -> list[Suggestion] | None:
        """Check all tiers in order and return the first hit.

        Checks Tier 1 -> Tier 2 -> Tier 3. Returns None only if all
        three tiers miss.

        Args:
            key: Normalized cache key (the output of *build_key()*).

        Returns:
            A list of Suggestion objects from the first matching tier,
            or None if all tiers miss.
        """
        for tier in (self._tier1, self._tier2, self._tier3):
            result = tier.lookup(key)
            if result is not None:
                return result
        return None

    ####################################################################
    # Update
    ####################################################################

    def update(self, key: str, suggestions: list[Suggestion]) -> None:
        """Write suggestions to Tier 3 (user LRU) after a cache miss.

        Args:
            key: Normalized cache key (output of build_key()).
            suggestions: Suggestions produced by the model.
        """
        self._tier3.update(key, suggestions)
