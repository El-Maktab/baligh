"""Vocabulary management for the Word N-Gram model.

Authors:
    Akram Hany
"""

from src.services.ged.detectors.lexicon.trie_store import (
    load_processed_lexicon,
)

# Fixed IDs for special tokens.
UNK_ID = -1
BOS_ID = -2
EOS_ID = -3

# Map punctuation to negative IDs.
PUNCTUATION_MAP = {
    ",": -4,
    "،": -5,
    ":": -6,
    ";": -7,
    "؛": -8,
    '"': -9,
    "'": -10,
    "-": -11,
}


class Vocabulary:
    """Integerization engine for Word N-Gram."""

    def __init__(self):
        """Initialize the Vocabulary."""
        # Load lexicon trie.
        self.trie = load_processed_lexicon().words

        self._reverse_punct = {v: k for k, v in PUNCTUATION_MAP.items()}
        self._reverse_special = {
            UNK_ID: "<unk>",
            BOS_ID: "<s>",
            EOS_ID: "</s>",
        }

    def word_to_id(self, word: str) -> int:
        """Convert a string word to its integer ID."""
        if word == "<s>":
            return BOS_ID
        if word == "</s>":
            return EOS_ID
        if word == "<unk>":
            return UNK_ID

        if word in PUNCTUATION_MAP:
            return PUNCTUATION_MAP[word]

        # Align normalization with lexicon.
        from src.core.utils.arabic import loose_arabic_lookup_key

        loose_word = loose_arabic_lookup_key(word)

        # Trie lookup.
        if loose_word in self.trie:
            return self.trie[loose_word]

        # Fallback for OOV.
        return UNK_ID

    def id_to_word(self, token_id: int) -> str:
        """Convert an integer ID back to its string word."""
        if token_id in self._reverse_special:
            return self._reverse_special[token_id]

        if token_id in self._reverse_punct:
            return self._reverse_punct[token_id]

        if token_id >= 0:
            try:
                # Reverse lookup ID.
                return self.trie.restore_key(token_id)
            except KeyError:
                return "<unk>"

        return "<unk>"
