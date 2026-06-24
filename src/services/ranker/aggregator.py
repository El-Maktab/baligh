from collections import defaultdict
from typing import DefaultDict

from pydantic import BaseModel

from src.services.ged.schemas import ErrorSpan
from src.services.gec.schemas import ModuleName, ModuleResult, CandidateEdit

class AggregatedCandidate(BaseModel):
    module_name: ModuleName
    candidate: CandidateEdit
    
class CandidateAggregator:
    """
    Maps GED error spans to valid candidate edits produced by GEC modules.
    """

    def __init__(self) -> None:
        pass

    def aggregate(
        self,
        errors_span: list[ErrorSpan],
        module_results: list[ModuleResult],
    ) -> dict[int, list[AggregatedCandidate]]:

        aggregated: DefaultDict[int, list[AggregatedCandidate]] = defaultdict(list)

        error_span_map = {
            idx: span for idx, span in enumerate(errors_span)
        }

        for module_result in module_results:
            if not module_result.candidate_edits:
                continue
            name = module_result.module_name
            for candidate in module_result.candidate_edits:
                error_id = self._resolve_error_id(candidate, error_span_map)
                if error_id is None:
                    continue

                normalized = AggregatedCandidate(candidate= candidate, module_name=name)
                aggregated[error_id].append(normalized)
        return dict(aggregated)

    def _resolve_error_id(
        self,
        candidate: CandidateEdit,
        error_span_map: dict[int, ErrorSpan],
    ) -> int | None:
        """
        Match a candidate edit to a GED error span.
        """

        for error_id, span in error_span_map.items():
            if self._span_match(candidate.span, span.span) or \
                self._token_overlap(candidate.token_refs, span.token_refs):
                return error_id
        return None

    def _span_match(
        self,
        cand_span: tuple[int, int],
        error_span: tuple[int, int],
    ) -> bool:
        """Check if character spans overlap."""
        c_start, c_end = cand_span
        e_start, e_end = error_span

        return not (c_end <= e_start or c_start >= e_end)

    def _token_overlap(
        self,
        cand_tokens: list[int],
        error_tokens: list[int],
    ) -> bool:
        """Check if token reference sets intersect."""
        return bool(set(cand_tokens) & set(error_tokens))
