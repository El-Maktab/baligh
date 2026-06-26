"""The runtime Character N-gram Language Model.

Authors:
    Akram Hany
"""

import math
from typing import Any


class CharNGramLM:
    """A Character-level N-gram Language Model."""

    def __init__(self, model_data: dict[int, Any]):
        """Initialize the model."""
        self.model_data = model_data
        # max_n is the highest order present in the data (e.g., 5 for 5-grams)
        self.max_n = max(model_data.keys())
        self.p_continuation = model_data[1]

    def _get_char_prob(self, char: str, context: tuple[str, ...]) -> float:
        """Recursively calculate the smoothed probability P(char | context)."""
        n = len(context) + 1

        # Base case: Unigram fallback
        if n == 1:
            return self.p_continuation.get(char, 1e-10)

        order_data = self.model_data.get(n, {})
        ctx_data = order_data.get(context)

        if not ctx_data:
            return self._get_char_prob(char, context[1:])

        discounted_p = ctx_data["probs"].get(char, 0.0)
        lambd = ctx_data["lambda"]

        return discounted_p + lambd * self._get_char_prob(char, context[1:])

    def score_word(self, word: str, context_chars: list[str]) -> float:
        """Calculate the log-probability of a word given a context."""
        log_prob = 0.0

        # Need max_n - 1 chars of history
        max_context_len = self.max_n - 1
        current_ctx = (
            tuple(context_chars[-max_context_len:]) if context_chars else tuple()
        )

        # Evaluate word with trailing space for word boundary
        word_with_boundary = word + " "

        for char in word_with_boundary:
            p = self._get_char_prob(char, current_ctx)
            if p <= 0.0:
                p = 1e-10
            log_prob += math.log(p)

            # Slide context window
            new_ctx = list(current_ctx) + [char]
            if len(new_ctx) > max_context_len:
                new_ctx.pop(0)
            current_ctx = tuple(new_ctx)

        # weight with 0.7 (best value found)
        return log_prob / (len(word_with_boundary) ** 0.7) if word else 0.0

    def predict(self, text: str, top_k: int = 5) -> list[tuple[str, float]]:
        """Generate the top-k word completions for a given text context."""
        # Late import to some issues in importing
        from src.services.ged.detectors.lexicon.trie_store import (
            load_processed_lexicon,
        )

        # Extract current word
        parts = text.split(" ")
        current_word_prefix = parts[-1]

        # Extract context
        context_str = " ".join(parts[:-1]) + " " if len(parts) > 1 else " "

        trie = load_processed_lexicon()
        candidates = trie.get_completions(current_word_prefix)

        scored_candidates = []
        for cand in candidates:
            score = self.score_word(cand, list(context_str))
            scored_candidates.append((cand, score))

        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        top_cands = scored_candidates[:top_k]

        if not top_cands:
            return []

        # Softmax normalize top-K
        max_score = top_cands[0][1]
        exp_scores = [math.exp(score - max_score) for _, score in top_cands]
        sum_exp = sum(exp_scores)

        normalized_results = []
        for (cand, _), exp_s in zip(top_cands, exp_scores, strict=True):
            normalized_results.append((cand, exp_s / sum_exp))

        return normalized_results
