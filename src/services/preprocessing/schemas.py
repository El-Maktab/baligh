"""Schemas for the preprocessing service.

This module defines the input/output data structures of the preprocessing pipeline.

References:
- docs/contracts/preprocessing-contract.md

Authors:
    - Akram Hany
"""

from typing import Literal

from pydantic import BaseModel

from src.core.schemas import MorphAnalysis, Token


class PreprocessingInput(BaseModel):
    """The input data structure for the preprocessing service.

    Attributes:
        text: Raw Arabic text as typed by the user.
        cursor_offset: Character offset of the cursor in text (None means end of input).
    """

    text: str
    cursor_offset: int | None = None


class PreprocessingOutput(BaseModel):
    """The complete output of the preprocessing service.

    Attributes:
        text: Original text, unmodified.
        normalized_text: Internally normalized text.
        tokens: Completed tokens only, with character offsets on `text`.
        morph_features: Per-token morphological candidates, outer list is indexed
            by token, inner list holds all candidates with the disambiguated one
            always first.
        current_fragment: The incomplete word being typed, or None if input ends
            with a delimiter.
        mode: Detected input mode. "NWP" for Next-Word Prediction, "WAC" for
            Word-Completion.
    """

    text: str
    normalized_text: str
    tokens: list[Token]
    morph_features: list[list[MorphAnalysis]]
    current_fragment: str | None
    mode: Literal["NWP", "WAC"]
