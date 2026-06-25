"""Pydantic models for the GED service.

This module defines the Pydantic models used by the GED service.

References:
- docs/contracts/ged-contract.md
- src/services/ged/contracts.py

Authors:
    Amir Anwar
"""

from enum import StrEnum

from pydantic import BaseModel

import src.core.schemas as core_schemas


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
    tokens: list[core_schemas.Token]
    morph_features: list[list[core_schemas.MorphAnalysis]]


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
