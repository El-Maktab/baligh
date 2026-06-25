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


def levenshtein(s1: str, s2: str) -> int:
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row
    return prev_row[-1]


class CharDistanceRule(BaseRule):
    @property
    def name(self) -> str:
        return "R_COST_CHAR_DISTANCE"

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
        dist = levenshtein(original_text, candidate.correction)
        norm = max(len(original_text), len(candidate.correction), 1)
        return -config.edit_cost.W_CHAR_DIST * (dist / norm)


class LengthRatioRule(BaseRule):
    @property
    def name(self) -> str:
        return "R_COST_LENGTH_RATIO"

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
        delta = abs(len(candidate.correction) - len(original_text))
        norm = max(len(original_text), 1)
        return -config.edit_cost.W_LENGTH_RATIO * (delta / norm)


def _get_edit_operation(candidate: GECUnionCandidateEdit) -> str | None:
    if isinstance(candidate, EditTaggerCandidateEdit) and candidate.edit_operation:
        first = candidate.edit_operation[0]
        op_map: dict[EditOperation, str] = {
            EditOperation.KEEP: "keep",
            EditOperation.REPLACE: "replace",
            EditOperation.INSERT: "insert",
            EditOperation.DELETE: "delete",
            EditOperation.MERGE: "merge",
            EditOperation.SPLIT: "split",
        }
        return op_map.get(first)
    return None


class EmptyCorrectionRule(BaseRule):
    @property
    def name(self) -> str:
        return "R_COST_EMPTY_CORRECTION"

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
        if candidate.correction.strip() == "":
            op = _get_edit_operation(candidate)
            if op != "delete":
                return -config.edit_cost.W_EMPTY
        return 0.0
