"""Pydantic models and schemas for the GEC service.

This module defines the request/response contracts and candidate edits
as specified in docs/contracts/gec-contract.md.
"""

from enum import StrEnum

from pydantic import BaseModel

from src.core.schemas import MorphAnalysis, Token
from src.services.ged.schemas import ErrorSpan


class ModuleName(StrEnum):
    """Submodules inside the GEC service."""

    TAG = "TAG"
    ONTOLOGY = "ONTOLOGY"
    DICTIONARY = "DICTIONARY"


class ModuleStatus(StrEnum):
    """Status returned by each GEC submodule."""

    CORRECT = "correct"
    INCORRECT = "incorrect"
    ERROR = "error"


class CandidateEdit(BaseModel):
    """Base model for any proposed correction edit."""

    span: tuple[int, int]
    token_refs: list[int]
    correction: str
    edit_confidence: float
    explanation: str | None = None
    alternatives: list[str] | None = None


class EditOperation(StrEnum):
    """Operation types for sequence tagging edits."""

    KEEP = "K"
    REPLACE = "R"
    INSERT = "I"
    DELETE = "D"
    MERGE = "M"
    SPLIT = "S"


class ModuleResult(BaseModel):
    """Individual output result from one of the GEC submodules."""

    module_name: ModuleName
    status: ModuleStatus
    candidate_edits: list[CandidateEdit]


class GECInput(BaseModel):
    """Request structure for the GEC pipeline."""

    text: str
    tokens: list[Token]
    morph_features: list[list[MorphAnalysis]]
    errors_span: list[ErrorSpan]


# GECOutput is defined as a list of exactly three ModuleResult objects
# (TAG, ONTOLOGY, DICTIONARY)
GECOutput = list[ModuleResult]
