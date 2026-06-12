"""Core schemas for Baligh.

This module defines the basic data structures shared across all pipeline modules.

References:
- docs/contracts/preprocessing-contract.md

Authors:
    - Akram Hany
"""

from pydantic import BaseModel


class Token(BaseModel):
    """Represents a token used by the Baligh service.

    Attributes:
        index: Position of this token in the token list (0-based).
        form: Original form of the token as it appears in the original text.
        span: Start and end character offsets in the original text.
        norm_span: Start and end character offsets on the normalized text.
        is_clitic: Whether this token is a clitic segmented off a word.
    """

    index: int
    form: str
    span: tuple[int, int]
    norm_span: tuple[int, int]
    is_clitic: bool


class MorphAnalysis(BaseModel):
    """Morphological analysis candidate for a token.

    Represents one candidate analysis produced by a morphological analyzer.

    Attributes:
        token_index: Index of the corresponding Token.
        lemma: Base/root form of the token, None for punctuation and non-Arabic.
        pos: Part-of-speech tag.
        gender: "masculine", "feminine", or None.
        number: "singular", "dual", "plural", or None.
        person: "first", "second", "third", or None.
        definiteness: "definite", "indefinite", or None.
        case: "nominative", "accusative", "genitive", or None if can't be determned.
        tense: "past", "present", "imperative", or None for non verbs.
        voice: "active", "passive", or None for non verbs.
        mood: "indicative", "subjunctive", "jussive", or None for non verbs.
        diacritized: The token form with full diacritics as resolved by disambiguation.
        affix_structure: Encoded prefix/suffix breakdown (ex. CONJ+PREP+DET+STEM).
        is_disambiguated: True for the candidate selected by the disambiguator.
    """

    token_index: int
    lemma: str | None = None
    pos: str
    gender: str | None = None
    number: str | None = None
    person: str | None = None
    definiteness: str | None = None
    case: str | None = None
    tense: str | None = None
    voice: str | None = None
    mood: str | None = None
    diacritized: str | None = None
    affix_structure: str | None = None
    is_disambiguated: bool = False
