"""Build processed lexicon tries from raw dictionary assets.

Authors:
    Amir Anwar
"""

from __future__ import annotations

import argparse
import json
import re
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import marisa_trie
from src.core.utils.arabic import (
    is_arabic_word,
    loose_arabic_lookup_key,
    normalize_arabic_surface,
)
from src.services.ged.config import LexiconDictionaryConfig, load_ged_config

_WIKIFANE_RE = re.compile(r"^<(?P<tag>[^>]+)>(?P<entity>.*)</(?P=tag)>$")


@dataclass(frozen=True)
class ProcessedLexiconMetadata:
    """Metadata for generated trie assets."""

    generated_at: str
    word_count: int
    entity_phrase_count: int
    entity_token_count: int
    max_entity_phrase_tokens: int
    sources: dict[str, str]


def iter_clean_words(path: Path) -> Iterable[str]:
    """Yield cleaned lookup keys from the Arabic wordlist."""
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            key = loose_arabic_lookup_key(line)
            if key and is_arabic_word(key):
                yield key


def parse_wikifane_line(line: str) -> tuple[str, str] | None:
    """Parse one WIKIFANE entity line into ``(tag, phrase)``."""
    cleaned = normalize_arabic_surface(line, collapse_whitespace=True)
    match = _WIKIFANE_RE.fullmatch(cleaned)
    if match is None:
        return None

    phrase = normalize_arabic_surface(
        match.group("entity").replace("_", " "),
        collapse_whitespace=True,
    )
    if not phrase:
        return None
    return match.group("tag"), phrase


def iter_entity_phrases(path: Path) -> Iterable[str]:
    """Yield cleaned loose entity phrase keys from WIKIFANE."""
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            parsed = parse_wikifane_line(line)
            if parsed is None:
                continue

            _, phrase = parsed
            key = loose_arabic_lookup_key(phrase)
            tokens = [token for token in key.split(" ") if is_arabic_word(token)]
            if tokens:
                yield " ".join(tokens)


def write_trie(values: Iterable[str], path: Path) -> int:
    """Write unique sorted values to a marisa trie and return the count."""
    unique_values = sorted(set(values))
    trie = marisa_trie.Trie(unique_values)
    trie.save(str(path))
    return len(unique_values)


def build_processed_lexicon(
    *,
    words_path: Path,
    entities_path: Path,
    output_dir: Path,
    dictionary_config: LexiconDictionaryConfig | None = None,
) -> ProcessedLexiconMetadata:
    """Build word, entity phrase, and entity token tries."""
    dictionary_config = dictionary_config or load_ged_config().lexicon.dictionary
    output_dir.mkdir(parents=True, exist_ok=True)

    words = set(iter_clean_words(words_path))
    phrases = set(iter_entity_phrases(entities_path))
    entity_tokens = {
        token
        for phrase in phrases
        for token in phrase.split(" ")
        if token and is_arabic_word(token)
    }
    max_phrase_tokens = max((len(phrase.split(" ")) for phrase in phrases), default=0)

    word_count = write_trie(words, output_dir / dictionary_config.words_trie)
    phrase_count = write_trie(
        phrases,
        output_dir / dictionary_config.entity_phrases_trie,
    )
    token_count = write_trie(
        entity_tokens,
        output_dir / dictionary_config.entity_tokens_trie,
    )

    metadata = ProcessedLexiconMetadata(
        generated_at=datetime.now(UTC).isoformat(),
        word_count=word_count,
        entity_phrase_count=phrase_count,
        entity_token_count=token_count,
        max_entity_phrase_tokens=max_phrase_tokens,
        sources={
            "words": str(words_path),
            "entities": str(entities_path),
        },
    )
    (output_dir / dictionary_config.metadata).write_text(
        json.dumps(asdict(metadata), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return metadata


def main() -> None:
    """Run the dictionary processing command."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--words", type=Path)
    parser.add_argument("--entities", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()

    config = load_ged_config(args.config) if args.config else load_ged_config()
    dictionary_config = config.lexicon.dictionary
    metadata = build_processed_lexicon(
        words_path=args.words or dictionary_config.words_path,
        entities_path=args.entities or dictionary_config.entities_path,
        output_dir=args.output_dir or dictionary_config.processed_output_dir,
        dictionary_config=dictionary_config,
    )
    print(json.dumps(asdict(metadata), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
