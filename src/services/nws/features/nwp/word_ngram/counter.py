"""Word N-Gram counter for integerized sequences.

Authors:
    Akram Hany
"""

import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class NGramCounter:
    """Counts integer sequence frequencies."""

    def __init__(self, max_n: int = 3):
        """Initialize the counter with a maximum n-gram order."""
        self.max_n = max_n

        # Structure: counts[n][context_tuple][target_int] = freq
        # Unigram: counts[1][()][402] = freq
        # Trigram: counts[3][(14, 89)][402] = freq
        self.counts: dict[int, dict[tuple[int, ...], dict[int, int]]] = {
            i: defaultdict(lambda: defaultdict(int)) for i in range(1, max_n + 1)
        }

    def add_sequence(self, sequence: list[int]):
        """Count all n-grams in a sequence of word IDs."""
        seq_len = len(sequence)
        for n in range(1, self.max_n + 1):
            for i in range(seq_len - n + 1):
                ngram = sequence[i : i + n]
                context = tuple(ngram[:-1])
                target = ngram[-1]
                self.counts[n][context][target] += 1

    def calculate_discounts(self) -> dict[int, float]:
        """Calculate Kneser-Ney absolute discount parameters for each order."""
        discounts: dict[int, float] = {}

        for n in range(2, self.max_n + 1):
            n1 = 0
            n2 = 0
            for ctx_counts in self.counts[n].values():
                for count in ctx_counts.values():
                    if count == 1:
                        n1 += 1
                    elif count == 2:
                        n2 += 1

            if n1 + 2 * n2 > 0:
                d = n1 / (n1 + 2 * n2)
                # Keep discount within bounds.
                discounts[n] = min(max(d, 0.01), 0.99)
            else:
                discounts[n] = 0.75  # Fallback discount.

        return discounts
