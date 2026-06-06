"""Pydantic models for the GED service.

This module defines the Pydantic models used by the GED service.

References:
- docs/contracts/ged-contract.md
- src/services/ged/contracts.py

Author:
    Amir Anwar
"""

from enum import StrEnum

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


#######################################################################
# GED structures (Referenced in ged contract)                         #
#######################################################################
class ErrorCategory(StrEnum):
    """GED error categories."""

    ORTHOGRAPHY = "OT"
    MORPHOLOGY = "MO"
    SYNTAX = "SY"
    SEMANTICS = "SE"
    PUNCTUATION = "PC"
    MERGE = "MG"
    SPLIT = "SP"


class ErrorSource(StrEnum):
    """Subsystems that can flag an error span."""

    RULE_BASED = "rule_based"
    LEXICON_MATCHER = "lexicon_matcher"
    SEQUENCE_LABELER = "sequence_labeler"


class ProvenanceTier(StrEnum):
    """Provenance tiers assigned to error spans."""

    TIER_1_RULE_DERIVED = "tier_1_rule_derived"
    TIER_2_RULE_SUPPORTED = "tier_2_rule_supported"
    TIER_3_STATISTICAL = "tier_3_statistical"


class ErrorSpan(BaseModel):
    """A span of text flagged as a GED error.

    An error span captures the character offsets of the offending region,
    the affected token indices, the error classification, and supporting
    metadata used for ranking and explanation.

    Attributes:
        span (tuple[int, int]): Start and end character offsets on the
            original text.
        token_refs (list[int]): Indices of the affected tokens.
        category (ErrorCategory): Top-level error category.
        subtype (str): Specific error subtype, such as hamza, ta_marbuta,
            or verb_subject_agreement.
        confidence (float): Score in the range [0.0, 1.0].
        sources (list[ErrorSource]): Subsystems that flagged this span.
        provenance_tier (ProvenanceTier): Provenance tier for the span.
        explanation_eligible (bool): Whether a human-readable explanation
            can be attached.
        explanation_text (str | None): Arabic explanation string for tier 1
            and tier 2 spans, None for tier 3.
    """

    span: tuple[int, int]
    token_refs: list[int]
    category: ErrorCategory
    subtype: str
    confidence: float
    sources: list[ErrorSource]
    provenance_tier: ProvenanceTier
    explanation_eligible: bool
    explanation_text: str | None


class GEDOutput(BaseModel):
    """The output of the GED service.

    Attributes:
        text (str): Original input text.
        errors (list[ErrorSpan]): List of detected error spans with metadata.
    """

    text: str
    errors: list[ErrorSpan]
