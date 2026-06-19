"""Pydantic models for the NWS service.

This module defines the Pydantic models used by the Next-Word Suggestion (NWS) service.

References:
- docs/contracts/nws-contract.md
- docs/contracts/preprocessing-contract.md

Authors:
    - Akram Hany
"""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel

from src.core.schemas import MorphAnalysis, Token


class NWSSource(StrEnum):
    """Sources that can produce a suggestion."""

    IDIOM_CACHE = "idiom_cache"
    PHRASE_CACHE = "phrase_cache"
    USER_CACHE = "user_cache"
    MODEL = "model"
    TRIE = "trie"


class Suggestion(BaseModel):
    """A ranked suggestion candidate.

    Attributes:
        rank: 0-based position in the ranked list (0 = best).
        word: The full suggested word. In NWP: the predicted next word.
            In WAC: the full word completing the current fragment.
        score: Confidence score in [0.0, 1.0].
        source: Which subsystem produced this suggestion.
    """

    rank: int
    word: str
    score: float
    source: NWSSource


class NWSInput(BaseModel):
    """Input for the NWS service.

    Attributes:
        tokens: Completed tokens from preprocessing, used as context window.
        morph_features: Per-token morphological candidates, outer list is indexed
            by token, inner list holds all candidates with the disambiguated one
            always first.
        current_fragment: Incomplete word being typed, None in NWP mode.
        mode: Routing signal ("NWP" or "WAC").
        top_k: Maximum number of suggestions to return (defult 5), note that sometimes
            we might return fewer results than 5 if no more values exist.
    """

    tokens: list[Token]
    morph_features: list[list[MorphAnalysis]]
    current_fragment: str | None = None
    mode: Literal["NWP", "WAC"]
    top_k: int = 5


class NWSOutput(BaseModel):
    """Output of the NWS service.

    Attributes:
        mode: mode from the input.
        suggestions: Ranked list of suggestion candidates.
    """

    mode: Literal["NWP", "WAC"]
    suggestions: list[Suggestion]
