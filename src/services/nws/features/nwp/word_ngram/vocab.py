"""Vocabulary management for the Word N-Gram model.

Maps valid Arabic words to unique integer IDs using the GED LexiconTrieStore.
Reserves negative IDs for special tokens (<UNK>, <BOS>, <EOS>) and punctuation.
"""

from typing import Optional
from src.services.ged.features.subsystems.lexicon.trie_store import load_processed_lexicon

# Fixed IDs for special tokens to avoid clashing with marisa_trie IDs (which are >= 0)
UNK_ID = -1
BOS_ID = -2
EOS_ID = -3

# Map mid-sentence punctuation to fixed negative IDs so the model can learn them
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
        # We load the existing words trie to get instant integer IDs for valid words
        self.trie = load_processed_lexicon().words
        
        self._reverse_punct = {v: k for k, v in PUNCTUATION_MAP.items()}
        self._reverse_special = {
            UNK_ID: "<unk>",
            BOS_ID: "<s>",
            EOS_ID: "</s>",
        }

    def word_to_id(self, word: str) -> int:
        """Convert a string word to its integer ID."""
        if word == "<s>": return BOS_ID
        if word == "</s>": return EOS_ID
        if word == "<unk>": return UNK_ID
        
        if word in PUNCTUATION_MAP:
            return PUNCTUATION_MAP[word]
            
        # The GED Lexicon was built using "loose" normalization (stripping hamzas/alif-maksura).
        # We must align our string identically, otherwise common words like "إلى" or "أحمد"
        # will incorrectly map to UNK_ID.
        from src.core.utils.arabic import loose_arabic_lookup_key
        loose_word = loose_arabic_lookup_key(word)
        
        # Fast C++ Trie lookup
        if loose_word in self.trie:
            return self.trie[loose_word]
            
        # If it's a typo, English, number, etc.
        return UNK_ID
        
    def id_to_word(self, token_id: int) -> str:
        """Convert an integer ID back to its string word."""
        if token_id in self._reverse_special:
            return self._reverse_special[token_id]
            
        if token_id in self._reverse_punct:
            return self._reverse_punct[token_id]
            
        if token_id >= 0:
            try:
                # marisa_trie provides restore_key to reverse lookup IDs
                return self.trie.restore_key(token_id)
            except KeyError:
                return "<unk>"
                
        return "<unk>"
