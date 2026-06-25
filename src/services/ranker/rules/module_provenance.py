from __future__ import annotations

from src.core.schemas import Token
from src.services.ged.schemas import ErrorSpan
from src.services.gec.schemas import (
    GECUnionCandidateEdit,
    ModuleName,
    OntologyCandidateEdit,
)
from src.services.ranker.config import RankerConfig
from src.services.ranker.rules.base import BaseRule


class OntologyBonusRule(BaseRule):
    @property
    def name(self) -> str:
        return "R_MOD_ONTOLOGY_BONUS"

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
        if module_name == ModuleName.ONTOLOGY:
            return config.module_provenance.W_ONTOLOGY
        return 0.0


class TagBonusRule(BaseRule):
    @property
    def name(self) -> str:
        return "R_MOD_TAG_BONUS"

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
        if module_name == ModuleName.TAG:
            return config.module_provenance.W_TAG
        return 0.0


class DictionaryBonusRule(BaseRule):
    @property
    def name(self) -> str:
        return "R_MOD_DICTIONARY_BONUS"

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
        if module_name == ModuleName.DICTIONARY:
            return config.module_provenance.W_DICTIONARY
        return 0.0


class OntologyIndependentRule(BaseRule):
    @property
    def name(self) -> str:
        return "R_MOD_ONTOLOGY_INDEPENDENT"

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
        if module_name == ModuleName.ONTOLOGY and isinstance(
            candidate, OntologyCandidateEdit
        ):
            if candidate.is_independent:
                return config.module_provenance.W_INDEPENDENT
        return 0.0


class OntologyGroupRankRule(BaseRule):
    @property
    def name(self) -> str:
        return "R_MOD_ONTOLOGY_GROUP_RANK"

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
        if module_name == ModuleName.ONTOLOGY and isinstance(
            candidate, OntologyCandidateEdit
        ):
            group_rank = candidate.group.group_rank
            if group_rank > 0:
                return config.module_provenance.W_GROUP_RANK / group_rank
        return 0.0
