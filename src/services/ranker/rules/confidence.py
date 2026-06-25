from __future__ import annotations

from src.core.schemas import Token
from src.services.ged.schemas import ErrorSpan
from src.services.gec.schemas import GECUnionCandidateEdit, ModuleName
from src.services.ranker.config import RankerConfig
from src.services.ranker.rules.base import BaseRule


class EditConfidenceRule(BaseRule):
    @property
    def name(self) -> str:
        return "R_CONF_EDIT"

    def evaluate(
        self,
        candidate: GECUnionCandidateEdit,
        module_name: ModuleName,
        error_span: ErrorSpan,
        original_text: str,
        tokens: list[Token],
        peer_candidates: list[tuple[ModuleName, GECUnionCandidateEdit]],
        config: RankerConfig,
    ) -> float:
        return config.confidence.W_EDIT_CONF * candidate.edit_confidence


class GEDConfidenceRule(BaseRule):
    @property
    def name(self) -> str:
        return "R_CONF_GED"

    def evaluate(
        self,
        candidate: GECUnionCandidateEdit,
        module_name: ModuleName,
        error_span: ErrorSpan,
        original_text: str,
        tokens: list[Token],
        peer_candidates: list[tuple[ModuleName, GECUnionCandidateEdit]],
        config: RankerConfig,
    ) -> float:
        return config.confidence.W_GED_CONF * error_span.confidence


class LowConfidencePenaltyRule(BaseRule):
    @property
    def name(self) -> str:
        return "R_CONF_LOW_PENALTY"

    def evaluate(
        self,
        candidate: GECUnionCandidateEdit,
        module_name: ModuleName,
        error_span: ErrorSpan,
        original_text: str,
        tokens: list[Token],
        peer_candidates: list[tuple[ModuleName, GECUnionCandidateEdit]],
        config: RankerConfig,
    ) -> float:
        if candidate.edit_confidence < config.confidence.CONF_LOW_THRESHOLD:
            return -config.confidence.W_LOW_CONF
        return 0.0
