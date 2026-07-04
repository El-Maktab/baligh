"""Tests for processed lexicon trie generation.

Authors:
    Amir Anwar
"""

from __future__ import annotations

import json

import marisa_trie
from src.runtime_config import load_runtime_config
from src.services.ged.detectors.lexicon.processor import (
    build_processed_lexicon,
    parse_wikifane_line,
)


def test_parse_wikifane_line_cleans_hidden_marks_and_underscores():
    """WIKIFANE tags should parse into clean phrase surfaces."""
    parsed = parse_wikifane_line("<PER_Artist>\u200eجوستاف_لوبون</PER_Artist>")

    assert parsed == ("PER_Artist", "جوستاف لوبون")


def test_build_processed_lexicon_cleans_deduplicates_and_writes_tries(tmp_path):
    """Processor should generate exact lookup tries and metadata."""
    words_path = tmp_path / "words.txt"
    entities_path = tmp_path / "entities.txt"
    output_dir = tmp_path / "processed"
    dictionary_config = load_runtime_config().ged.lexicon.dictionary
    words_path.write_text("أَحمد\nاحمد\nبَيْت\nhello\n\n", encoding="utf-8")
    entities_path.write_text(
        "<PER_Artist>\u200eجوستاف_لوبون</PER_Artist>\n"
        "<GPE_Population-Center>حي_أول_المحلة</GPE_Population-Center>\n",
        encoding="utf-8",
    )

    metadata = build_processed_lexicon(
        words_path=words_path,
        entities_path=entities_path,
        output_dir=output_dir,
        dictionary_config=dictionary_config,
    )

    words = marisa_trie.Trie()
    phrases = marisa_trie.Trie()
    entity_tokens = marisa_trie.Trie()
    words.load(str(output_dir / dictionary_config.words_trie))
    phrases.load(str(output_dir / dictionary_config.entity_phrases_trie))
    entity_tokens.load(str(output_dir / dictionary_config.entity_tokens_trie))
    metadata_json = json.loads(
        (output_dir / dictionary_config.metadata).read_text(encoding="utf-8")
    )

    assert "احمد" in words
    assert "بيت" in words
    assert "hello" not in words
    assert metadata.word_count == 2
    assert "جوستاف لوبون" in phrases
    assert "حي اول المحله" in phrases
    assert "لوبون" in entity_tokens
    assert metadata_json["max_entity_phrase_tokens"] == 3
