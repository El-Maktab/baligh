"""Kneser-Ney Smoothing for Character N-gram Models.

Authors:
    - Akram Hany
"""

from collections import defaultdict
from typing import Any

from src.services.nws.features.wac.char_ngram.counter import NGramCounter


class KneserNeySmoother:
    """Computes Kneser-Ney smoothed probabilities from raw counts."""

    def __init__(self, counter: NGramCounter):
        """Initialize the smoother with a built counter.
        
        Args:
            counter: NGramCounter that has already processed the training text.
                Must NOT be pruned yet, so discounts and lambdas are accurate.
        """
        self.counter = counter
        self.discounts = counter.calculate_discounts()
        self.max_n = counter.max_n

    def build_model(
        self, min_count: int = 3, min_n_to_prune: int = 3
    ) -> dict[int, Any]:
        """Build the final smoothed model parameters with pruning.
        
        Calculates continuation probabilities for unigrams, and discounted
        probabilities + backoff weights for higher-order n-grams.
        Pruning drops low-frequency n-grams *after* their probability mass
        has been accounted for in the backoff weights.
        
        Args:
            min_count: The minimum frequency required to keep an n-gram.
            min_n_to_prune: Only prune n-grams of this order and higher.
            
        Returns:
            A dictionary representing the model:
            {
                1: {"a": 0.05, "b": 0.02, ...}, # Continuation probabilities
                2: {
                    ("a",): {"lambda": 0.4, "probs": {"b": 0.3, "c": 0.1}},
                    ...
                },
                3: ... up to max_n
            }
        """
        model_data: dict[int, Any] = {}
        vocab: set[str] = set()

        # Gather vocabulary from all counts
        for n in range(1, self.max_n + 1):
            for ctx, char_counts in self.counter.counts[n].items():
                vocab.update(ctx)
                vocab.update(char_counts.keys())

        # 1. Base case (Unigram): Continuation Probabilities
        # Number of distinct bigram contexts that precede a character
        cont_counts: dict[str, int] = defaultdict(int)
        if self.max_n >= 2:
            for context, char_counts in self.counter.counts[2].items():
                for char in char_counts.keys():
                    cont_counts[char] += 1

        total_cont = sum(cont_counts.values())
        p_continuation: dict[str, float] = {}

        for char in vocab:
            if total_cont > 0 and cont_counts[char] > 0:
                p_continuation[char] = cont_counts[char] / total_cont
            else:
                # Small epsilon for characters unseen in bigram contexts
                p_continuation[char] = 1e-10

        # Normalize to strictly sum to 1.0
        total_p = sum(p_continuation.values())
        if total_p > 0:
            p_continuation = {k: v / total_p for k, v in p_continuation.items()}

        model_data[1] = p_continuation

        # 2. Higher order models
        for n in range(2, self.max_n + 1):
            order_data: dict[tuple[str, ...], dict[str, Any]] = {}
            d = self.discounts[n]

            for context, char_counts in self.counter.counts[n].items():
                total_count = sum(char_counts.values())
                if total_count == 0:
                    continue

                num_distinct = len(char_counts)
                lambd = (d * num_distinct) / total_count if total_count > 0 else 1.0

                probs: dict[str, float] = {}
                for char, count in char_counts.items():
                    # Pruning: skip adding the exact discounted prob if freq < min_count
                    # The probability mass falls back to the lower-order model naturally.
                    if n >= min_n_to_prune and count < min_count:
                        continue

                    discounted_p = max(count - d, 0.0) / total_count
                    if discounted_p > 0:
                        probs[char] = discounted_p

                # Even if all chars are pruned, keep the context for its backoff weight
                # unless the lambda is 1.0 (which is the default for unseen contexts anyway)
                if probs or lambd < 1.0:
                    # Convert context tuple to string for more compact storage?
                    # Let's keep it as tuple for now, serializer can stringify.
                    order_data[context] = {"lambda": lambd, "probs": probs}

            model_data[n] = order_data

        return model_data
