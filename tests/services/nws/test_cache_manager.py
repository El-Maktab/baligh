"""Tests for the NWS cache layer (CacheManager and all tiers).

Authors:
    - Akram Hany
"""

from pathlib import Path

import pytest
import yaml

from src.core.schemas import Token
from src.services.nws.features.cache.idioms import IdiomsCache
from src.services.nws.features.cache.manager import CacheManager
from src.services.nws.features.cache.phrases import PhrasesCache
from src.services.nws.features.cache.user_lru import UserLRUCache
from src.services.nws.schemas import NWSSource, Suggestion


#############################################################################
# Helpers
#############################################################################

def _make_token(form: str, index: int = 0) -> Token:
    return Token(index=index, form=form, span=(0, len(form)), norm_span=(0, len(form)))


def _make_suggestion(word: str, rank: int = 0, source: NWSSource = NWSSource.MODEL) -> Suggestion:
    return Suggestion(rank=rank, word=word, score=0.9, source=source)


def _write_yaml(path: Path, entries: list) -> None:
    with path.open("w", encoding="utf-8") as fh:
        yaml.dump(entries, fh, allow_unicode=True)


#############################################################################
# UserLRUCache tests
#############################################################################

def test_user_lru_miss():
    """Lookup on empty cache returns None."""
    cache = UserLRUCache(maxsize=10)
    assert cache.lookup("missing_key") is None


def test_user_lru_hit_after_update():
    """Stored suggestions can be retrieved."""
    cache = UserLRUCache(maxsize=10)
    suggestions = [_make_suggestion("كتاب", source=NWSSource.USER_CACHE)]
    cache.update("ذهب الى", suggestions)
    assert cache.lookup("ذهب الى") == suggestions


def test_user_lru_eviction():
    """LRU evicts the least recently used entry when capacity is exceeded."""
    cache = UserLRUCache(maxsize=2)
    cache.update("key1", [_make_suggestion("a")])
    cache.update("key2", [_make_suggestion("b")])

    # Access key1 to make it recently used
    cache.lookup("key1")

    # Adding key3 should evict key2 (least recently used)
    cache.update("key3", [_make_suggestion("c")])

    assert cache.lookup("key1") is not None
    assert cache.lookup("key2") is None  # evicted
    assert cache.lookup("key3") is not None
    assert len(cache) == 2


def test_user_lru_source_tag():
    """Source tag should be user_cache."""
    assert UserLRUCache().source_tag == NWSSource.USER_CACHE


#############################################################################
# IdiomsCache tests
#############################################################################

def test_idioms_cache_miss_on_missing_file(tmp_path):
    """IdiomsCache on a non-existent file returns None for all lookups."""
    cache = IdiomsCache(tmp_path / "nonexistent.yaml")
    assert cache.lookup("any key") is None


def test_idioms_cache_hit(tmp_path):
    """IdiomsCache correctly loads and returns suggestions from YAML."""
    entries = [
        {
            "key": "ضرب عصفورين",
            "suggestions": [{"word": "بحجر", "score": 0.99}],
        }
    ]
    path = tmp_path / "idioms.yaml"
    _write_yaml(path, entries)

    cache = IdiomsCache(path)
    result = cache.lookup("ضرب عصفورين")

    assert result is not None
    assert len(result) == 1
    assert result[0].word == "بحجر"
    assert result[0].source == NWSSource.IDIOM_CACHE
    assert result[0].score == 0.99


def test_idioms_cache_suffix_scan_hit(tmp_path):
    """IdiomsCache fires when the stored key is a suffix of the full context key."""
    entries = [
        {
            "key": "ضرب عصفورين",
            "suggestions": [{"word": "بحجر", "score": 0.99}],
        }
    ]
    path = tmp_path / "idioms.yaml"
    _write_yaml(path, entries)

    cache = IdiomsCache(path)
    # The runtime key contains 3 preceding words before the stored 2-word key.
    result = cache.lookup("قال لي صديقي ضرب عصفورين")

    assert result is not None
    assert result[0].word == "بحجر"


def test_idioms_cache_suffix_scan_miss(tmp_path):
    """IdiomsCache returns None when no suffix of the key matches any entry."""
    entries = [
        {
            "key": "ضرب عصفورين",
            "suggestions": [{"word": "بحجر", "score": 0.99}],
        }
    ]
    path = tmp_path / "idioms.yaml"
    _write_yaml(path, entries)

    cache = IdiomsCache(path)
    assert cache.lookup("لا يوجد تطابق هنا أبدا") is None


def test_idioms_cache_source_tag(tmp_path):
    """Source tag should be idiom_cache."""
    cache = IdiomsCache(tmp_path / "empty.yaml")
    assert cache.source_tag == NWSSource.IDIOM_CACHE


#############################################################################
# PhrasesCache tests
#############################################################################

def test_phrases_cache_hit(tmp_path):
    """PhrasesCache correctly loads and returns suggestions from YAML."""
    entries = [
        {
            "key": "بسم الله الرحمن",
            "suggestions": [{"word": "الرحيم", "score": 0.99}],
        }
    ]
    path = tmp_path / "phrases.yaml"
    _write_yaml(path, entries)

    cache = PhrasesCache(path)
    result = cache.lookup("بسم الله الرحمن")

    assert result is not None
    assert result[0].word == "الرحيم"
    assert result[0].source == NWSSource.PHRASE_CACHE


def test_phrases_cache_suffix_scan_hit(tmp_path):
    """PhrasesCache fires when the stored key is a suffix of the full context key."""
    entries = [
        {
            "key": "السلام عليكم",
            "suggestions": [{"word": "ورحمه", "score": 1.0}],
        }
    ]
    path = tmp_path / "phrases.yaml"
    _write_yaml(path, entries)

    cache = PhrasesCache(path)
    # Simulates: user typed 3 preceding words then 'السلام عليكم'
    result = cache.lookup("وابدا كلامي السلام عليكم")

    assert result is not None
    assert result[0].word == "ورحمه"
    assert result[0].source == NWSSource.PHRASE_CACHE


def test_phrases_cache_source_tag(tmp_path):
    """Source tag should be phrase_cache."""
    cache = PhrasesCache(tmp_path / "empty.yaml")
    assert cache.source_tag == NWSSource.PHRASE_CACHE


#############################################################################
# CacheManager.build_key tests
#############################################################################

def _make_manager(tmp_path: Path, window: int = 5) -> CacheManager:
    return CacheManager(
        tier1=IdiomsCache(tmp_path / "idioms.yaml"),
        tier2=PhrasesCache(tmp_path / "phrases.yaml"),
        tier3=UserLRUCache(maxsize=100),
        context_window_size=window,
    )


def test_build_key_nwp_mode(tmp_path):
    """NWP key is last-N token forms joined by space, Alif-canonicalized."""
    manager = _make_manager(tmp_path, window=3)
    tokens = [
        _make_token("ذهب", 0),
        _make_token("الطلاب", 1),
        _make_token("إلى", 2),
    ]
    key = manager.build_key(tokens, current_fragment=None)
    assert key == "ذهب الطلاب الي"


def test_build_key_wac_mode(tmp_path):
    """WAC key appends pipe-separated fragment to the context key."""
    manager = _make_manager(tmp_path, window=3)
    tokens = [_make_token("ذهب", 0), _make_token("إلى", 1)]
    key = manager.build_key(tokens, current_fragment="أحمد")
    assert "|" in key
    assert key.endswith("|احمد")


def test_build_key_window_limits_tokens(tmp_path):
    """Only last N tokens are included in the key."""
    manager = _make_manager(tmp_path, window=2)
    tokens = [_make_token("ذهب", 0), _make_token("الطلاب", 1), _make_token("الى", 2)]
    key = manager.build_key(tokens, current_fragment=None)
    assert key == "الطلاب الي"


#############################################################################
# CacheManager lookup / update integration tests
#############################################################################

def test_cache_manager_tier1_hit(tmp_path):
    """Tier 1 (idioms) hit short-circuits before Tier 2 and 3."""
    entries = [{"key": "ضرب عصفورين", "suggestions": [{"word": "بحجر", "score": 0.99}]}]
    _write_yaml(tmp_path / "idioms.yaml", entries)

    manager = _make_manager(tmp_path)
    result = manager.lookup("ضرب عصفورين")

    assert result is not None
    assert result[0].source == NWSSource.IDIOM_CACHE


def test_cache_manager_tier3_miss_then_hit(tmp_path):
    """After a miss, updating Tier 3 enables a subsequent hit."""
    manager = _make_manager(tmp_path)
    key = "ذهب الطلاب"
    suggestions = [_make_suggestion("الى", source=NWSSource.MODEL)]

    assert manager.lookup(key) is None

    # Update Tier 3 and verify hit
    manager.update(key, suggestions)
    result = manager.lookup(key)
    assert result is not None
    assert result[0].word == "الى"


def test_cache_manager_full_miss(tmp_path):
    """Returns None when all three tiers miss."""
    manager = _make_manager(tmp_path)
    assert manager.lookup("لا يوجد هذا") is None
