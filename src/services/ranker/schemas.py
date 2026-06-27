"""Schemas for the ranker service."""

from __future__ import annotations

from pydantic import BaseModel

from src.core.schemas import Token
from src.services.gec.schemas import ModuleName, ModuleResult
from src.services.ged.schemas import ErrorSpan


class RankedEdit(BaseModel):
    """A single ranked edit with its score and metadata."""

    error_id: int
    span: tuple[int, int]
    token_refs: list[int]
    correction: str
    selected_module: ModuleName
    final_score: float
    edit_confidence: float
    explanation: str | None = None
    alternatives: list[str] | None = None


class RankingMetadata(BaseModel):
    """Aggregated metadata about the ranking decisions."""

    global_confidence: float
    module_utilization: dict[str, int]


class RankerInput(BaseModel):
    """Input to the ranker containing text, tokens, errors, and candidate edits."""

    text: str
    tokens: list[Token]
    errors_span: list[ErrorSpan]
    errors_corrections: list[ModuleResult]


class RankerOutput(BaseModel):
    """Output from the ranker with ranked edits and metadata."""

    text: str
    ranked_edits: list[RankedEdit]
    ranking_metadata: RankingMetadata
