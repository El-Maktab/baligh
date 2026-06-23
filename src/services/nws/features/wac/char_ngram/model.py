"""The runtime Character N-gram Language Model.

Authors:
    - Akram Hany
"""

import math
from typing import Any


class CharNGramLM:
    """A Character-level N-gram Language Model.
    
    Provides word scoring based on character-by-character probabilities.
    """

    def __init__(self, model_data: dict[int, Any]):
        """Initialize the model.
        
        Args:
            model_data: The nested dictionary containing lambdas and discounted
                probabilities (loaded via serializer.py).
        """
        self.model_data = model_data
        # max_n is the highest order present in the data (e.g., 5 for 5-grams)
        self.max_n = max(model_data.keys())
        self.p_continuation = model_data[1]

    def _get_char_prob(self, char: str, context: tuple[str, ...]) -> float:
        """Recursively calculate the smoothed probability P(char | context).
        
        Uses the Modified Kneser-Ney backoff formulation.
        
        Args:
            char: The character to predict.
            context: The preceding characters.
            
        Returns:
            The probability (0.0 to 1.0).
        """
        n = len(context) + 1
        
        # Base case: Unigram fallback
        if n == 1:
            # Provide a very small epsilon for characters completely unseen in the corpus
            return self.p_continuation.get(char, 1e-10)
            
        order_data = self.model_data.get(n, {})
        ctx_data = order_data.get(context)
        
        if not ctx_data:
            # Unseen context! The backoff weight (lambda) is implicitly 1.0,
            # and there are no direct discounted probabilities.
            return self._get_char_prob(char, context[1:])
            
        discounted_p = ctx_data["probs"].get(char, 0.0)
        lambd = ctx_data["lambda"]
        
        return discounted_p + lambd * self._get_char_prob(char, context[1:])

    def score_word(self, word: str, context_chars: list[str]) -> float:
        """Calculate the log-probability of a word given a context.
        
        Args:
            word: The candidate word to score.
            context_chars: The preceding characters up to the start of the word.
                Typically, this ends with a space if starting a fresh word.
                
        Returns:
            The natural log probability of the word. Higher is better.
        """
        log_prob = 0.0
        
        # We only need at most max_n - 1 characters of history
        max_context_len = self.max_n - 1
        current_ctx = tuple(context_chars[-max_context_len:]) if context_chars else tuple()
        
        # We evaluate the word plus a trailing space to force the model to score the "Word Boundary".
        # This heavily penalizes broken fragments (like "المستم") because they never appear followed by a space.
        word_with_boundary = word + " "
        
        for char in word_with_boundary:
            p = self._get_char_prob(char, current_ctx)
            if p <= 0.0:
                p = 1e-10
            log_prob += math.log(p)
            
            # Slide the context window forward
            new_ctx = list(current_ctx) + [char]
            if len(new_ctx) > max_context_len:
                new_ctx.pop(0)
            current_ctx = tuple(new_ctx)
            
        # Use an alpha length penalty of 0.7 to balance the "Length Bias".
        # 1.0 strongly favors long words (Suffix Inflation).
        # 0.0 strongly favors short words (Fragment Bias).
        # We normalize by the physical number of scored characters (len + 1 for the space).
        return log_prob / (len(word_with_boundary) ** 0.7) if word else 0.0

    def predict(self, text: str, top_k: int = 5) -> list[str]:
        """Generate the top-k word completions for a given text context.
        
        This relies on the GED LexiconTrieStore to provide valid candidates,
        and then scores them using the character n-gram model using the preceding
        characters as mathematical context.
        """
        # Late import to prevent circular dependencies or heavy upfront loading
        from src.services.ged.features.subsystems.lexicon.trie_store import load_processed_lexicon
        
        # Extract the current word being typed (everything after the last space)
        parts = text.split(" ")
        current_word_prefix = parts[-1]
        
        # The context is everything before the current word, including the trailing space
        # If there are no spaces, we simulate a word boundary with just a space
        context_str = " ".join(parts[:-1]) + " " if len(parts) > 1 else " "
        print(context_str)
        
        trie = load_processed_lexicon()
        candidates = trie.get_completions(current_word_prefix)
        
        scored_candidates = []
        for cand in candidates:
            # Score the candidate using the actual preceding character context!
            score = self.score_word(cand, list(context_str))
            scored_candidates.append((cand, score))
            
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        return [cand for cand, score in scored_candidates[:top_k]]
