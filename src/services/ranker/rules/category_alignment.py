from __future__ import annotations

from src.core.schemas import Token
from src.services.ged.schemas import ErrorCategory, ErrorSpan
from src.services.gec.schemas import GECUnionCandidateEdit, ModuleName
from src.services.ranker.config import RankerConfig
from src.services.ranker.rules.base import BaseRule


class SpellingDictRule(BaseRule):
    @property
    def name(self) -> str:
        return "R_CAT_SPELLING_DICT"

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
        if error_span.category == ErrorCategory.ORTHOGRAPHY and module_name == ModuleName.DICTIONARY:
            return config.category_alignment.W_SPELL_DICT
        return 0.0


class GrammarOntologyRule(BaseRule):
    @property
    def name(self) -> str:
        return "R_CAT_GRAMMAR_ONTOLOGY"

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
        if error_span.category in (ErrorCategory.SYNTAX, ErrorCategory.MORPHOLOGY) and module_name == ModuleName.ONTOLOGY:
            return config.category_alignment.W_GRAM_ONT
        return 0.0


class ExplanationBonusRule(BaseRule):
    @property
    def name(self) -> str:
        return "R_CAT_HAS_EXPLANATION"

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
        if error_span.explanation_eligible and module_name == ModuleName.ONTOLOGY:
            return config.category_alignment.W_EXPLAIN
        return 0.0
