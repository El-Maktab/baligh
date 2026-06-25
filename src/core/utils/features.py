"""Utility functions for handling morphological features."""

from src.core.schemas import MorphAnalysis


def get_disambiguated_analysis(
    morph_features: list[list[MorphAnalysis]], idx: int
) -> MorphAnalysis | None:
    """Gets the disambiguated morphological analysis for a given index."""
    if idx < 0 or idx >= len(morph_features):
        return None
    candidates = morph_features[idx]
    return candidates[0] if candidates else None
