"""Word N-Gram counter for integerized sequences.

Calculates raw frequencies for n-grams up to max_n.
"""

from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class NGramCounter:
    """Counts integer sequence frequencies."""
    
    def __init__(self, max_n: int = 3):
        self.max_n = max_n
        
        # Structure: counts[n][context_tuple][target_int] = count
        # For a trigram (14, 89, 402): counts[3][(14, 89)][402] = freq
        # For a unigram (402): counts[1][()][402] = freq
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
        """Calculate Kneser-Ney absolute discount parameters for each order.
        
        Formula: D = n1 / (n1 + 2 * n2)
        where n1 is number of ngrams with freq 1, n2 is number with freq 2.
        """
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
                # Keep discount in a mathematically sane range
                discounts[n] = min(max(d, 0.01), 0.99)
            else:
                discounts[n] = 0.75  # Standard fallback
                
        return discounts
