"""Kneser-Ney Smoothing for Word N-Gram Models.

Applies Absolute Discounting and Backoff computation to integerized n-grams.
"""

import logging
from collections import defaultdict
from typing import Any

from src.services.nws.features.nwp.word_ngram.counter import NGramCounter

logger = logging.getLogger(__name__)


class KneserNeySmoother:
    """Computes Kneser-Ney smoothed probabilities from raw integer counts."""

    def __init__(self, counter: NGramCounter):
        self.counter = counter
        self.discounts = counter.calculate_discounts()
        self.max_n = counter.max_n

    def build_model(
        self, min_count: int = 3, min_n_to_prune: int = 3
    ) -> dict[int, Any]:
        """Build the final smoothed model parameters with aggressive pruning.

        Args:
            min_count: The minimum frequency required to keep an n-gram.
            min_n_to_prune: Only prune n-grams of this order and higher.

        Returns:
            Dictionary mapped for serialization.
        """
        model_data: dict[int, Any] = {}
        vocab: set[int] = set()

        for n in range(1, self.max_n + 1):
            for ctx, target_counts in self.counter.counts[n].items():
                vocab.update(ctx)
                vocab.update(target_counts.keys())

        # 1. Base case (Unigram): Continuation Probabilities
        # Number of distinct bigram contexts that precede a word
        cont_counts: dict[int, int] = defaultdict(int)
        if self.max_n >= 2:
            for context, target_counts in self.counter.counts[2].items():
                for target in target_counts.keys():
                    cont_counts[target] += 1

        total_cont = sum(cont_counts.values())
        p_continuation: dict[int, float] = {}

        for word_id in vocab:
            if total_cont > 0 and cont_counts[word_id] > 0:
                p_continuation[word_id] = cont_counts[word_id] / total_cont
            else:
                p_continuation[word_id] = 1e-10

        # Normalize to strictly sum to 1.0
        total_p = sum(p_continuation.values())
        if total_p > 0:
            p_continuation = {k: v / total_p for k, v in p_continuation.items()}

        model_data[1] = p_continuation

        # 2. Higher order models
        for n in range(2, self.max_n + 1):
            order_data: dict[tuple[int, ...], dict[str, Any]] = {}
            d = self.discounts[n]

            for context, target_counts in self.counter.counts[n].items():
                total_count = sum(target_counts.values())
                if total_count == 0:
                    continue

                num_distinct = len(target_counts)
                lambd = (d * num_distinct) / total_count if total_count > 0 else 1.0

                probs: dict[int, float] = {}
                for target, count in target_counts.items():
                    # Pruning: skip adding the exact discounted prob if freq < min_count
                    if n >= min_n_to_prune and count < min_count:
                        continue

                    discounted_p = max(count - d, 0.0) / total_count
                    if discounted_p > 0:
                        probs[target] = discounted_p

                # Keep context for backoff weights even if words were pruned
                if probs or lambd < 1.0:
                    order_data[context] = {"lambda": lambd, "probs": probs}

            model_data[n] = order_data

        return model_data
