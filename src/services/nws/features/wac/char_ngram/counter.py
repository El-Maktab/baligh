"""Extracts and stores raw character n-gram counts from text streams.

Authors:
    Akram Hany
"""

from collections import defaultdict
from collections.abc import Iterable


class NGramCounter:
    """Builds frequency tables for n-grams from a stream of characters."""

    def __init__(self, max_n: int = 5):
        """Initialize the counter for up to max_n-grams."""
        if max_n < 1:
            raise ValueError("max_n must be >= 1")
        self.max_n = max_n

        # counts[n][context][char] = count
        # where `context` is a tuple of length n-1
        self.counts: list[dict[tuple[str, ...], dict[str, int]]] = [
            defaultdict(lambda: defaultdict(int)) for _ in range(max_n + 1)
        ]

    def add_sequence(self, sequence: Iterable[str]) -> None:
        """Process a sequence of characters and update counts."""
        history: list[str] = []
        for char in sequence:
            max_possible_n = min(len(history) + 1, self.max_n)

            for n in range(1, max_possible_n + 1):
                context_len = n - 1
                if context_len == 0:
                    context: tuple[str, ...] = tuple()
                else:
                    context = tuple(history[-context_len:])

                self.counts[n][context][char] += 1

            history.append(char)
            if len(history) >= self.max_n:
                history.pop(0)

    def calculate_discounts(self) -> list[float]:
        """Calculate Kneser-Ney discount factor 'd' for each order n."""
        discounts = [0.0] * (self.max_n + 1)
        for n in range(1, self.max_n + 1):
            n1 = 0
            n2 = 0
            for char_counts in self.counts[n].values():
                for count in char_counts.values():
                    if count == 1:
                        n1 += 1
                    elif count == 2:
                        n2 += 1
            if n1 + 2 * n2 > 0:
                discounts[n] = n1 / (n1 + 2 * n2)
            else:
                discounts[n] = 0.0
        return discounts

    def prune(self, min_count: int = 3, min_n_to_prune: int = 3) -> None:
        """Remove low-frequency n-grams to save memory."""
        for n in range(min_n_to_prune, self.max_n + 1):
            contexts_to_delete = []

            for context, char_counts in self.counts[n].items():
                chars_to_delete = [
                    char for char, count in char_counts.items() if count < min_count
                ]
                for char in chars_to_delete:
                    del char_counts[char]

                if not char_counts:
                    contexts_to_delete.append(context)

            for context in contexts_to_delete:
                del self.counts[n][context]

    def to_plain_dicts(self) -> list[dict[tuple[str, ...], dict[str, int]]]:
        """Convert default dictionaries to standard dictionaries."""
        plain_counts: list[dict[tuple[str, ...], dict[str, int]]] = [
            {} for _ in range(self.max_n + 1)
        ]
        for n in range(1, self.max_n + 1):
            for context, char_counts in self.counts[n].items():
                plain_counts[n][context] = dict(char_counts)
        return plain_counts
