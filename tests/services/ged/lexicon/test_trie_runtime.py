"""Runtime tests for trie-backed lexicon lookup.

Authors:
    Amir Anwar
"""

from __future__ import annotations

import marisa_trie
from src.services.ged.features.subsystems.lexicon.detector import LexiconDetector
from src.services.ged.features.subsystems.lexicon.trie_store import LexiconTrieStore
from src.services.ged.schemas import ErrorCategory, ProvenanceTier

from tests.services.ged.rule_based.conftest import make_morph, make_token


def _store(
    *,
    words: list[str] | None = None,
    entity_phrases: list[str] | None = None,
    entity_tokens: list[str] | None = None,
) -> LexiconTrieStore:
    phrases = entity_phrases or []
    return LexiconTrieStore(
        words=marisa_trie.Trie(words or []),
        entity_phrases=marisa_trie.Trie(phrases),
        entity_tokens=marisa_trie.Trie(entity_tokens or []),
        metadata={
            "max_entity_phrase_tokens": max(
                (len(phrase.split(" ")) for phrase in phrases),
                default=1,
            )
        },
    )


def _detector(store: LexiconTrieStore) -> LexiconDetector:
    return LexiconDetector(patterns=[], trie_store=store)


def test_entity_phrase_suppresses_spelling_suspicion():
    """Tokens inside a matched entity phrase should be protected."""
    detector = _detector(_store(entity_phrases=["احمد السيد"]))
    tokens = [
        make_token("أحمد", (0, 4), 0),
        make_token("السيد", (5, 10), 1),
    ]

    spans = detector.detect("أحمد السيد", "أحمد السيد", tokens, [[], []])

    assert spans == []


def test_entity_token_fallback_suppresses_spelling_suspicion():
    """Single entity tokens should suppress spelling suspicion."""
    detector = _detector(_store(entity_tokens=["تيرنياوز"]))
    tokens = [make_token("تيرنياوز", (0, 8), 0)]

    spans = detector.detect("تيرنياوز", "تيرنياوز", tokens, [[]])

    assert spans == []


def test_dictionary_hit_suppresses_spelling_suspicion():
    """Dictionary hits should not emit spelling spans."""
    detector = _detector(_store(words=["مدرسه"]))
    tokens = [make_token("مدرسة", (0, 5), 0)]

    spans = detector.detect("مدرسة", "مدرسة", tokens, [[]])

    assert spans == []


def test_dictionary_miss_emits_spelling_suspicion():
    """Arabic dictionary misses without morphology should emit OT/spelling."""
    detector = _detector(_store(words=["مدرسه"]))
    tokens = [make_token("مدرثه", (0, 5), 0)]

    spans = detector.detect("مدرثه", "مدرثه", tokens, [[]])

    assert len(spans) == 1
    assert spans[0].category == ErrorCategory.ORTHOGRAPHY
    assert spans[0].subtype == "spelling"
    assert spans[0].provenance_tier == ProvenanceTier.TIER_2_RULE_SUPPORTED


def test_plausible_morphology_suppresses_spelling_suspicion():
    """Morphological analyses should block dictionary miss suspicion."""
    detector = _detector(_store(words=[]))
    tokens = [make_token("مدرثه", (0, 5), 0)]
    morph_features = [[make_morph(0, "NOUN", lemma="مدرثة")]]

    spans = detector.detect("مدرثه", "مدرثه", tokens, morph_features)

    assert spans == []


def test_punctuation_and_non_arabic_tokens_are_skipped():
    """Non-Arabic and punctuation tokens should never emit spelling spans."""
    detector = _detector(_store(words=[]))
    tokens = [
        make_token("،", (0, 1), 0),
        make_token("Python", (2, 8), 1),
    ]

    spans = detector.detect("، Python", "، Python", tokens, [[], []])

    assert spans == []
