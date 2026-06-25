from __future__ import annotations

import logging

from src.services.ged.schemas import ErrorSpan
from src.services.gec.schemas import ModuleName
from src.services.ranker.schemas import RankedEdit, RankingMetadata, ScoredCandidate

logger = logging.getLogger(__name__)

_MODULE_PRIORITY: dict[ModuleName, int] = {
    ModuleName.ONTOLOGY: 3,
    ModuleName.TAG: 2,
    ModuleName.DICTIONARY: 1,
}


def _derive_edit_operation(candidate: ScoredCandidate) -> str:
    from src.services.gec.schemas import (
        DictionaryCandidateEdit,
        EditOperation,
        EditTaggerCandidateEdit,
    )

    c = candidate.candidate
    if isinstance(c, EditTaggerCandidateEdit) and c.edit_operation:
        first = c.edit_operation[0]
        op_map: dict[EditOperation, str] = {
            EditOperation.KEEP: "keep",
            EditOperation.REPLACE: "replace",
            EditOperation.INSERT: "insert",
            EditOperation.DELETE: "delete",
            EditOperation.MERGE: "merge",
            EditOperation.SPLIT: "split",
        }
        return op_map.get(first, "replace")
    return "replace"


class CandidateSelector:
    def sort_candidates(self, scored: list[ScoredCandidate]) -> list[ScoredCandidate]:
        return sorted(scored, key=self._sort_key, reverse=True)

    def _sort_key(self, sc: ScoredCandidate) -> tuple:
        return (
            sc.final_score,
            sc.candidate.edit_confidence,
            _MODULE_PRIORITY.get(sc.module_name, 0),
            -len(sc.candidate.correction),
            -ord(sc.candidate.correction[0]) if sc.candidate.correction else 0,
        )

    def resolve_conflicts(
        self,
        error_spans: list[ErrorSpan],
        scored_per_error: dict[int, list[ScoredCandidate]],
    ) -> list[tuple[int, ScoredCandidate]]:
        sorted_ids = sorted(range(len(error_spans)), key=lambda i: error_spans[i].span[0])
        claimed_tokens: set[int] = set()
        selected: list[tuple[int, ScoredCandidate]] = []

        for error_id in sorted_ids:
            candidates = scored_per_error.get(error_id, [])
            for sc in candidates:
                if not (set(sc.candidate.token_refs) & claimed_tokens):
                    selected.append((error_id, sc))
                    claimed_tokens.update(sc.candidate.token_refs)
                    break
            else:
                pass

        return selected

    def build_output(
        self,
        text: str,
        selected: list[tuple[int, ScoredCandidate]],
        error_spans: list[ErrorSpan],
    ) -> tuple[list[RankedEdit], RankingMetadata]:
        ranked_edits: list[RankedEdit] = []
        module_utilization: dict[str, int] = {}

        for error_id, sc in selected:
            span = error_spans[error_id].span
            re = RankedEdit(
                error_id=error_id,
                span=span,
                token_refs=sc.candidate.token_refs,
                correction=sc.candidate.correction,
                edit_operation=_derive_edit_operation(sc),
                selected_module=sc.module_name.value,
                final_score=sc.final_score,
            )
            ranked_edits.append(re)
            mod = sc.module_name.value
            module_utilization[mod] = module_utilization.get(mod, 0) + 1

        if ranked_edits:
            global_confidence = sum(re.final_score for re in ranked_edits) / len(
                ranked_edits
            )
        else:
            global_confidence = 0.0

        metadata = RankingMetadata(
            global_confidence=global_confidence,
            module_utilization=module_utilization,
        )
        return ranked_edits, metadata
