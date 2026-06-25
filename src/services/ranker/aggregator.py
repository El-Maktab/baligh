from collections import defaultdict

from src.services.ged.schemas import ErrorSpan
from src.services.gec.schemas import (
    GECUnionCandidateEdit,
    ModuleName,
    ModuleResult,
    ModuleStatus,
)


class CandidateAggregator:
    def aggregate(
        self,
        errors_span: list[ErrorSpan],
        module_results: list[ModuleResult],
    ) -> dict[int, list[tuple[ModuleName, GECUnionCandidateEdit]]]:
        aggregated: dict[int, list[tuple[ModuleName, GECUnionCandidateEdit]]] = (
            defaultdict(list)
        )

        error_span_map = {idx: span for idx, span in enumerate(errors_span)}

        for module_result in module_results:
            if module_result.status == ModuleStatus.ERROR:
                continue
            if not module_result.candidate_edits:
                continue
            name = module_result.module_name
            for candidate in module_result.candidate_edits:
                error_id = self._resolve_error_id(candidate, error_span_map)
                if error_id is None:
                    continue
                aggregated[error_id].append((name, candidate))

        return dict(aggregated)

    def _resolve_error_id(
        self,
        candidate: GECUnionCandidateEdit,
        error_span_map: dict[int, ErrorSpan],
    ) -> int | None:
        for error_id, span in error_span_map.items():
            if self._span_match(candidate.span, span.span) or self._token_overlap(
                candidate.token_refs, span.token_refs
            ):
                return error_id
        return None

    def _span_match(
        self,
        cand_span: tuple[int, int],
        error_span: tuple[int, int],
    ) -> bool:
        c_start, c_end = cand_span
        e_start, e_end = error_span
        return not (c_end <= e_start or c_start >= e_end)

    def _token_overlap(
        self,
        cand_tokens: list[int],
        error_tokens: list[int],
    ) -> bool:
        return bool(set(cand_tokens) & set(error_tokens))
