from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Dict, Any

from src.services.ged.schemas import ErrorSpan
from src.services.preprocessing.schemas import Token
from src.services.gec.schemas import GECOutput


@dataclass
class RankedEdit:
    error_id: int
    span: Tuple[int, int]
    token_refs: List[int]
    correction: str
    edit_operation: str
    selected_module: str
    final_score: float


@dataclass
class RankingMetadata:
    global_confidence: float
    module_utilization: Dict[str, int]


@dataclass
class RankerInput:
    text: str
    tokens: List[Token]
    errors_span: List[ErrorSpan]
    errors_corrections: GECOutput


@dataclass
class RankerOutput:
    text: str
    ranked_edits: List[RankedEdit]
    ranking_metadata: RankingMetadata