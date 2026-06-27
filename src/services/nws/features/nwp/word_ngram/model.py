"""The runtime Word N-Gram Language Model.

Authors:
    Akram Hany
"""

import math
from typing import Any

from src.services.nws.features.nwp.word_ngram.vocab import Vocabulary


class WordNGramLM:
    """Language model for word N-grams."""

    def __init__(self, model_data: dict[int, Any]):
        """Initialize the WordNGramLM."""
        self.model_data = model_data
        self.max_n = max(model_data.keys())
        self.p_continuation = model_data[1]
        self.vocab = Vocabulary()

        # Pre-sort unigrams for fallback.
        self._top_unigrams = sorted(
            self.p_continuation.items(), key=lambda x: x[1], reverse=True
        )[:100]  # Keep top 100 for padding.

    def _get_word_prob(self, word_id: int, context: tuple[int, ...]) -> float:
        """Recursively calculate P(word_id | context) using Modified Kneser-Ney."""
        n = len(context) + 1

        if n == 1:
            return self.p_continuation.get(word_id, 1e-10)

        order_data = self.model_data.get(n, {})
        ctx_data = order_data.get(context)

        if not ctx_data:
            return self._get_word_prob(word_id, context[1:])

        discounted_p = ctx_data["probs"].get(word_id, 0.0)
        lambd = ctx_data["lambda"]

        return discounted_p + lambd * self._get_word_prob(word_id, context[1:])

    def score_sequence(self, tokens: list[str]) -> float:
        """Calculate the average log-probability of a token sequence."""
        if not tokens:
            return 0.0

        token_ids = [self.vocab.word_to_id(t) for t in tokens]
        log_prob = 0.0

        max_context_len = self.max_n - 1
        current_ctx: tuple[int, ...] = tuple()

        for token_id in token_ids:
            p = self._get_word_prob(token_id, current_ctx)
            if p <= 0.0:
                p = 1e-10
            log_prob += math.log(p)

            new_ctx = list(current_ctx) + [token_id]
            if len(new_ctx) > max_context_len:
                new_ctx.pop(0)
            current_ctx = tuple(new_ctx)

        return log_prob / len(token_ids)

    def score_token(self, context_tokens: list[str], target_token: str) -> float:
        """Calculate the log-probability of a single target token given a string context."""
        max_context_len = self.max_n - 1
        context_ids = [
            self.vocab.word_to_id(t) for t in context_tokens[-max_context_len:]
        ]
        target_id = self.vocab.word_to_id(target_token)

        p = self._get_word_prob(target_id, tuple(context_ids))
        if p <= 0.0:
            p = 1e-10
        return math.log(p)

    def predict_next(
        self, context_tokens: list[str], top_k: int = 5, debug: bool = False
    ) -> list[str]:
        """Predict the top-k next words given a string context."""
        max_context_len = self.max_n - 1
        context_ids = [
            self.vocab.word_to_id(t) for t in context_tokens[-max_context_len:]
        ]
        current_ctx = tuple(context_ids)

        # Get candidate target IDs from backoff.
        candidates = set()
        ctx_len = len(current_ctx)

        for i in range(ctx_len + 1):
            sub_ctx = current_ctx[i:]
            n = len(sub_ctx) + 1
            if n == 1:
                break

            order_data = self.model_data.get(n, {})
            ctx_data = order_data.get(sub_ctx)
            if ctx_data:
                candidates.update(ctx_data["probs"].keys())
                if debug:
                    pass

        scored = []
        for cand_id in candidates:
            # Skip punctuation and special tokens.
            if cand_id < 0:
                continue
            p = self._get_word_prob(cand_id, current_ctx)
            scored.append((cand_id, p))

        scored.sort(key=lambda x: x[1], reverse=True)

        results = [self.vocab.id_to_word(cid) for cid, p in scored[:top_k]]

        # Pad with top unigrams if needed.
        if len(results) < top_k:
            for cand_id, p in self._top_unigrams:
                if cand_id >= 0:
                    word = self.vocab.id_to_word(cand_id)
                    if word not in results:
                        results.append(word)
                    if len(results) >= top_k:
                        break

        return results
