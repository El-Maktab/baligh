"""Metrics calculation for character n-gram models.

Authors:
    Akram Hany
"""

import math
from collections.abc import Iterable

from src.services.nws.features.wac.char_ngram.model import CharNGramLM


def compute_perplexity(
    model: CharNGramLM, text_stream: Iterable[str]
) -> tuple[float, float, int]:
    """Compute cross-entropy (BPC) and perplexity on raw text stream."""
    total_log_prob = 0.0
    total_chars = 0
    context_len = model.max_n - 1
    current_ctx: list[str] = []

    for chunk in text_stream:
        for char in chunk:
            p = model._get_char_prob(char, tuple(current_ctx))
            if p <= 0.0:
                p = 1e-10
            total_log_prob += math.log2(p)
            total_chars += 1
            current_ctx.append(char)
            if len(current_ctx) > context_len:
                current_ctx.pop(0)

    if total_chars == 0:
        return 0.0, 0.0, 0

    bpc = -total_log_prob / total_chars
    perplexity = 2**bpc
    return bpc, perplexity, total_chars


def top_k_accuracy(
    test_pairs: list[tuple[str, str]], model: CharNGramLM, k: int
) -> float:
    """Calculate the top-k accuracy of the model."""
    hits = 0
    for prefix, true_word in test_pairs:
        predictions = [p[0] for p in model.predict(prefix, top_k=k)]
        if true_word in predictions:
            hits += 1
    return hits / len(test_pairs) if test_pairs else 0.0


def mean_reciprocal_rank(
    test_pairs: list[tuple[str, str]], model: CharNGramLM, max_k: int = 10
) -> float:
    """Calculate the mean reciprocal rank of the model."""
    rr_sum = 0.0
    for prefix, true_word in test_pairs:
        predictions = [p[0] for p in model.predict(prefix, top_k=max_k)]
        if true_word in predictions:
            rank = predictions.index(true_word) + 1
            rr_sum += 1.0 / rank
    return rr_sum / len(test_pairs) if test_pairs else 0.0


def keystroke_savings_rate(
    test_pairs: list[tuple[str, str]], model: CharNGramLM, k: int
) -> float:
    """Calculate the keystroke savings rate."""
    total_without = 0
    total_with = 0
    for prefix, true_word in test_pairs:
        predictions = [p[0] for p in model.predict(prefix, top_k=k)]
        keystrokes_without = len(true_word)
        if true_word in predictions:
            keystrokes_with = len(prefix) + 1
        else:
            keystrokes_with = len(true_word)
        total_without += keystrokes_without
        total_with += keystrokes_with

    if total_without == 0:
        return 0.0
    return 1.0 - (total_with / total_without)
