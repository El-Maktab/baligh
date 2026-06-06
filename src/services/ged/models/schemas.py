"""Pydantic models for the GED service.

This module defines the Pydantic models used by the GED service.

References:
- docs/contracts/ged-contract.md
- src/services/ged/contracts.py

Author:
    Amir Anwar
"""

from pydantic import BaseModel

#######################################################################
# Preprocessing Structures (Referenced in preprocessing contract)     #
#######################################################################


class Token(BaseModel):
    """Represents a token used by the GED service.

    Attributes:
        index (int): Position of this token in the token list (0-based).
        form (str): Surface form of the token as it appears in the text.
        span (tuple[int, int]): Start and end character offsets on the
            original text.
        norm_span (tuple[int, int]): Start and end character offsets on the
            normalized text. This may differ from span when normalization
            changes character length (for example, when multi-character
            Unicode sequences are collapsed to a single character).
        is_clitic (bool): Whether this token is a clitic segmented off a
            host word.
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
        token_index (int): Index of the corresponding Token.
        lemma (str | None): Base/root form of the token; None for
            punctuation and non-Arabic tokens.
        pos (str): Part-of-speech tag.
        gender (str | None): "masculine", "feminine", or None if not
            applicable.
        number (str | None): "singular", "dual", "plural", or None if
            not applicable.
        person (str | None): "first", "second", "third", or None if not
            applicable.
        definiteness (str | None): "definite", "indefinite", or None if
            not applicable.
        case (str | None): "nominative", "accusative", "genitive", or
            None if undetermined.
        tense (str | None): "past", "present", "imperative", or None
            for non-verbs.
        voice (str | None): "active", "passive", or None for non-verbs.
        mood (str | None): "indicative", "subjunctive", "jussive", or
            None for non-verbs.
        diacritized (str | None): The token form with full diacritics as
            resolved by disambiguation; None for punctuation and
            non-Arabic tokens.
        affix_structure (str | None): Encoded prefix/suffix breakdown (for
            example CONJ+PREP+DET+STEM).
        is_disambiguated (bool): True for the candidate selected by the
            disambiguator; False otherwise.
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


class GEDInput(BaseModel):
    """The input for the GED service and the output of the preprocessing service.

    References:
    - docs/contracts/preprocessing-contract.md

    Removed fields related to next ward suggestions they are not relevant for GED.

    Attributes:
        text (str): Original input text.
        normalized_text (str): Normalized input text.
        tokens (list[Token]): List of tokens.
        morph_features (list[list[MorphAnalysis]]): Per-token morphological candidates;
            outer list is indexed by token, inner list holds all candidates with the
            disambiguated one always first (is_disambiguated: true)
    """

    text: str
    normalized_text: str
    tokens: list[Token]
    morph_features: list[list[MorphAnalysis]]
