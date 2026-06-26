"""Rule-based ranker that scores and selects the best GEC candidate edits."""

from __future__ import annotations

from src.services.gec.schemas import ModuleName, ModuleStatus
from src.services.ranker.config import RankerConfig
from src.services.ranker.schemas import (
    RankedEdit,
    RankerInput,
    RankerOutput,
    RankingMetadata,
)
from src.services.ranker.scoring import score_candidate

_MODULE_PRIORITY = {
    ModuleName.ONTOLOGY: 3,
    ModuleName.TAG: 2,
    ModuleName.DICTIONARY: 1,
}


class RankerService:
    """Scores and selects the best candidate edits from GEC modules."""

    def __init__(self) -> None:
        """Initialize RankerService with a scoring configuration."""
        self.config = RankerConfig()

    def rank(self, inp: RankerInput) -> RankerOutput:
        """Rank candidate edits and return the best corrections."""
        if not inp.text:
            return RankerOutput(
                text=inp.text,
                ranked_edits=[],
                ranking_metadata=RankingMetadata(
                    global_confidence=1.0, module_utilization={}
                ),
            )

        valid_corrections = [
            r for r in inp.errors_corrections if r.status != ModuleStatus.ERROR
        ]

        aggregated: dict[int, list] = {}
        for error_id, _ in enumerate(inp.errors_span, start=1):
            aggregated[error_id] = []

        for module_result in valid_corrections:
            if not module_result.candidate_edits:
                continue
            name = module_result.module_name
            for candidate in module_result.candidate_edits:
                for error_id, error_span in enumerate(inp.errors_span, start=1):
                    if self._matches(candidate, error_span):
                        aggregated[error_id].append((name, candidate))
                        break

        scored_per_error: dict[int, list] = {}
        for error_id, candidates in aggregated.items():
            if error_id >= len(inp.errors_span):
                continue
            error_span = inp.errors_span[error_id]
            original_text = inp.text[error_span.span[0] : error_span.span[1]]

            filtered = []
            for mod_name, cand in candidates:
                if cand.correction != original_text:
                    filtered.append((mod_name, cand))

            if not filtered:
                continue

            scored = []
            for mod_name, cand in filtered:
                score = score_candidate(
                    candidate=cand,
                    module_name=mod_name,
                    error_span=error_span,
                    original_text=original_text,
                    tokens=inp.tokens,
                    peer_candidates=filtered,
                    config=self.config,
                )
                if score != float("-inf"):
                    scored.append((score, mod_name, cand))

            if scored:
                scored.sort(
                    key=lambda x: (
                        x[0],
                        x[2].edit_confidence,
                        _MODULE_PRIORITY.get(x[1], 0),
                        -len(x[2].correction),
                    ),
                    reverse=True,
                )
                scored_per_error[error_id] = scored

        claimed_tokens: set[int] = set()
        selected: list[tuple[int, tuple]] = []

        sorted_ids = sorted(
            scored_per_error.keys(), key=lambda i: inp.errors_span[i].span[0]
        )
        for error_id in sorted_ids:
            for score, mod_name, cand in scored_per_error[error_id]:
                if not (set(cand.token_refs) & claimed_tokens):
                    selected.append((error_id, (score, mod_name, cand)))
                    claimed_tokens.update(cand.token_refs)
                    break

        ranked_edits: list[RankedEdit] = []
        module_utilization: dict[str, int] = {}

        for error_id, (score, mod_name, cand) in selected:
            span = inp.errors_span[error_id].span
            re = RankedEdit(
                error_id=error_id,
                span=span,
                token_refs=cand.token_refs,
                correction=cand.correction,
                selected_module=mod_name.value,
                final_score=score,
                edit_confidence=cand.edit_confidence,
                explanation=cand.explanation,
                alternatives=cand.alternatives,
            )
            ranked_edits.append(re)
            mod = mod_name.value
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

        return RankerOutput(
            text=inp.text,
            ranked_edits=ranked_edits,
            ranking_metadata=metadata,
        )

    def _matches(self, candidate, error_span) -> bool:
        c_start, c_end = candidate.span
        e_start, e_end = error_span.span
        if not (c_end <= e_start or c_start >= e_end):
            return True
        return bool(set(candidate.token_refs) & set(error_span.token_refs))
