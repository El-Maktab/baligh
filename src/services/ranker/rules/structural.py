from __future__ import annotations

from src.core.schemas import Token
from src.services.ged.schemas import ErrorSpan
from src.services.gec.schemas import (
    DictionaryCandidateEdit,
    EditOperation,
    EditTaggerCandidateEdit,
    GECUnionCandidateEdit,
    ModuleName,
)
from src.services.ranker.config import RankerConfig
from src.services.ranker.rules.base import BaseRule

DISQUALIFY_SCORE = float("-inf")


class OOVTokenRule(BaseRule):
    @property
    def name(self) -> str:
        return "R_SAFE_OOV_TOKEN"

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
        for tref in candidate.token_refs:
            if 0 <= tref < len(tokens) and tokens[tref].is_oov:
                return config.structural.W_OOV
        return 0.0


class IdenticalEditRule(BaseRule):
    @property
    def name(self) -> str:
        return "R_SAFE_IDENTICAL"

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
        if candidate.correction == original_text:
            return DISQUALIFY_SCORE
        return 0.0


class DictionaryFirstAltRule(BaseRule):
    @property
    def name(self) -> str:
        return "R_SAFE_DICTIONARY_FIRST_ALT"

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
        if module_name == ModuleName.DICTIONARY and isinstance(
            candidate, DictionaryCandidateEdit
        ):
            alts = candidate.alternatives
            if alts and alts[0] == candidate.correction:
                return config.structural.W_FIRST_ALT
        return 0.0


class OperationMismatchRule(BaseRule):
    @property
    def name(self) -> str:
        return "R_SAFE_OPERATION_MISMATCH"

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
        if isinstance(candidate, EditTaggerCandidateEdit) and candidate.edit_operation:
            first_op = candidate.edit_operation[0]
            if first_op == EditOperation.DELETE and candidate.correction.strip() != "":
                return -config.structural.W_OP_MISMATCH
            if first_op == EditOperation.INSERT and candidate.correction.strip() == "":
                return -config.structural.W_OP_MISMATCH
        return 0.0
