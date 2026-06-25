"""Runtime access to processed lexicon tries.

Authors:
    Amir Anwar
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import marisa_trie

from src.core.schemas import Token
from src.core.utils.arabic import is_arabic_word, loose_arabic_lookup_key
from src.services.ged.config import LexiconDictionaryConfig, load_ged_config


@dataclass(frozen=True)
class EntityPhraseMatch:
    """Matched named-entity phrase token window."""

    start: int
    end: int

    @property
    def token_refs(self) -> set[int]:
        """Return token indexes covered by this match."""
        return set(range(self.start, self.end))


@dataclass
class LexiconTrieStore:
    """Loaded processed lexicon tries."""

    words: marisa_trie.Trie
    entity_phrases: marisa_trie.Trie
    entity_tokens: marisa_trie.Trie
    metadata: dict[str, Any]

    @classmethod
    def load(
        cls,
        *,
        dictionary_config: LexiconDictionaryConfig | None = None,
        processed_dir: Path | None = None,
    ) -> LexiconTrieStore:
        """Load all processed tries from disk."""
        dictionary_config = dictionary_config or load_ged_config().lexicon.dictionary
        processed_dir = processed_dir or dictionary_config.processed_output_dir

        words = marisa_trie.Trie()
        entity_phrases = marisa_trie.Trie()
        entity_tokens = marisa_trie.Trie()
        words.load(str(processed_dir / dictionary_config.words_trie))
        entity_phrases.load(str(processed_dir / dictionary_config.entity_phrases_trie))
        entity_tokens.load(str(processed_dir / dictionary_config.entity_tokens_trie))

        metadata_path = processed_dir / dictionary_config.metadata
        metadata = (
            json.loads(metadata_path.read_text(encoding="utf-8"))
            if metadata_path.exists()
            else {}
        )
        return cls(
            words=words,
            entity_phrases=entity_phrases,
            entity_tokens=entity_tokens,
            metadata=metadata,
        )

    @property
    def max_entity_phrase_tokens(self) -> int:
        """Maximum entity phrase token length available for window matching."""
        value = self.metadata.get("max_entity_phrase_tokens", 1)
        return max(1, int(value))

    def has_word(self, text: str) -> bool:
        """Return True when text exists in the word trie."""
        key = loose_arabic_lookup_key(text)
        return bool(key) and key in self.words

    def has_entity_phrase(self, text: str) -> bool:
        """Return True when text exists in the entity phrase trie."""
        key = loose_arabic_lookup_key(text)
        return bool(key) and key in self.entity_phrases

    def has_entity_token(self, text: str) -> bool:
        """Return True when text exists in the entity-token trie."""
        key = loose_arabic_lookup_key(text)
        return bool(key) and key in self.entity_tokens

    def match_entity_phrases(self, tokens: list[Token]) -> list[EntityPhraseMatch]:
        """Match longest named-entity phrase windows over token forms."""
        keys = [
            loose_arabic_lookup_key(token.form) if is_arabic_word(token.form) else ""
            for token in tokens
        ]
        matches: list[EntityPhraseMatch] = []
        max_window = min(self.max_entity_phrase_tokens, len(tokens))

        for start in range(len(tokens)):
            for window_size in range(max_window, 1, -1):
                end = start + window_size
                if end > len(tokens) or any(not key for key in keys[start:end]):
                    continue

                phrase_key = " ".join(keys[start:end])
                if phrase_key in self.entity_phrases:
                    matches.append(EntityPhraseMatch(start=start, end=end))
                    break

        return matches


@lru_cache(maxsize=4)
def load_processed_lexicon(
    processed_dir: str | Path | None = None,
) -> LexiconTrieStore:
    """Load processed lexicon tries once."""
    config = load_ged_config().lexicon.dictionary
    return LexiconTrieStore.load(
        dictionary_config=config,
        processed_dir=Path(processed_dir) if processed_dir is not None else None,
    )
