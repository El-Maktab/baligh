from __future__ import annotations

from src.core.schemas import Token
from src.services.ged.schemas import ErrorSpan
from src.services.gec.schemas import GECUnionCandidateEdit, ModuleName
from src.services.ranker.config import RankerConfig
from src.services.ranker.rules.base import BaseRule


class MultiModuleAgreementRule(BaseRule):
    @property
    def name(self) -> str:
        return "R_AGR_MULTI_MODULE"

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
        other_modules: set[ModuleName] = set()
        for other_name, other_candidate in peer_candidates:
            if other_name != module_name and other_candidate.correction == candidate.correction:
                other_modules.add(other_name)
        if other_modules:
            return config.agreement.W_AGREEMENT
        return 0.0


class GEDMultiSourceRule(BaseRule):
    @property
    def name(self) -> str:
        return "R_AGR_GED_MULTI_SOURCE"

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
        if len(error_span.sources) > 1:
            return config.agreement.W_MULTI_SRC
        return 0.0
