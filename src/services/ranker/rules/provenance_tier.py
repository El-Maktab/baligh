from __future__ import annotations

from src.core.schemas import Token
from src.services.ged.schemas import ErrorSpan, ProvenanceTier
from src.services.gec.schemas import GECUnionCandidateEdit, ModuleName
from src.services.ranker.config import RankerConfig
from src.services.ranker.rules.base import BaseRule


class Tier1BoostRule(BaseRule):
    @property
    def name(self) -> str:
        return "R_TIER_1_BOOST"

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
        if error_span.provenance_tier == ProvenanceTier.TIER_1_RULE_DERIVED:
            return config.provenance_tier.W_TIER1
        return 0.0


class Tier2BoostRule(BaseRule):
    @property
    def name(self) -> str:
        return "R_TIER_2_BOOST"

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
        if error_span.provenance_tier == ProvenanceTier.TIER_2_RULE_SUPPORTED:
            return config.provenance_tier.W_TIER2
        return 0.0


class Tier3DampenRule(BaseRule):
    @property
    def name(self) -> str:
        return "R_TIER_3_DAMPEN"

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
        if error_span.provenance_tier == ProvenanceTier.TIER_3_STATISTICAL:
            return config.provenance_tier.W_TIER3
        return 0.0
