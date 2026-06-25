from __future__ import annotations

from src.services.ranker.aggregator import CandidateAggregator
from src.services.ranker.config import RankerConfig, get_ranker_config
from src.services.ranker.scorer import RuleScorer
from src.services.ranker.selector import CandidateSelector
from src.services.ranker.schemas import RankerInput, RankerOutput, RankingMetadata


class RankerService:
    def __init__(self, config: RankerConfig | None = None) -> None:
        self.config = config or get_ranker_config()
        self.aggregator = CandidateAggregator()
        self.scorer = RuleScorer(self.config)
        self.selector = CandidateSelector()

    def rank(self, inp: RankerInput) -> RankerOutput:
        if not inp.text:
            return RankerOutput(
                text=inp.text,
                ranked_edits=[],
                ranking_metadata=RankingMetadata(
                    global_confidence=0.0, module_utilization={}
                ),
            )

        if not inp.errors_span:
            return RankerOutput(
                text=inp.text,
                ranked_edits=[],
                ranking_metadata=RankingMetadata(
                    global_confidence=1.0, module_utilization={}
                ),
            )

        valid_results = [
            r for r in inp.errors_corrections if r.status.value != "error"
        ]

        aggregated = self.aggregator.aggregate(inp.errors_span, valid_results)

        scored_per_error: dict[int, list] = {}
        for error_id, candidates in aggregated.items():
            if error_id >= len(inp.errors_span):
                continue
            error_span = inp.errors_span[error_id]
            original_text = inp.text[error_span.span[0] : error_span.span[1]]

            filtered: list[tuple] = []
            for mod_name, cand in candidates:
                if cand.correction == original_text:
                    continue
                filtered.append((mod_name, cand))

            if not filtered:
                continue

            scored = self.scorer.score_all(
                candidates=filtered,
                error_span=error_span,
                original_text=original_text,
                tokens=inp.tokens,
            )
            qualified = self.scorer.filter_qualified(scored)
            if qualified:
                sorted_candidates = self.selector.sort_candidates(qualified)
                scored_per_error[error_id] = sorted_candidates

        selected = self.selector.resolve_conflicts(inp.errors_span, scored_per_error)
        ranked_edits, metadata = self.selector.build_output(
            text=inp.text, selected=selected, error_spans=inp.errors_span
        )

        return RankerOutput(
            text=inp.text,
            ranked_edits=ranked_edits,
            ranking_metadata=metadata,
        )
