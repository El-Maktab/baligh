from __future__ import annotations

from pydantic import BaseModel

from src.core.schemas import Token
from src.services.ged.schemas import ErrorSpan
from src.services.gec.schemas import ModuleResult


class RankedEdit(BaseModel):
    error_id: int
    span: tuple[int, int]
    token_refs: list[int]
    correction: str
    edit_operation: str
    selected_module: str
    final_score: float


class RankingMetadata(BaseModel):
    global_confidence: float
    module_utilization: dict[str, int]


class RankerInput(BaseModel):
    text: str
    tokens: list[Token]
    errors_span: list[ErrorSpan]
    errors_corrections: list[ModuleResult]


class RankerOutput(BaseModel):
    text: str
    ranked_edits: list[RankedEdit]
    ranking_metadata: RankingMetadata