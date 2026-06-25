from __future__ import annotations

import logging

from src.core.schemas import Token
from src.services.ged.schemas import ErrorSpan
from src.services.gec.schemas import GECUnionCandidateEdit, ModuleName
from src.services.ranker.config import RankerConfig
from src.services.ranker.rules import get_all_rules
from src.services.ranker.rules.base import BaseRule
from src.services.ranker.schemas import ScoredCandidate

logger = logging.getLogger(__name__)

DISQUALIFY_SCORE = float("-inf")


class RuleScorer:
    def __init__(self, config: RankerConfig) -> None:
        self.config = config
        self.rules: list[BaseRule] = get_all_rules(config)

    def score_candidate(
        self,
        candidate: GECUnionCandidateEdit,
        module_name: ModuleName,
        error_span: ErrorSpan,
        original_text: str,
        tokens: list[Token],
        peer_candidates: list[tuple[ModuleName, GECUnionCandidateEdit]],
    ) -> ScoredCandidate:
        total = 0.0
        breakdown: dict[str, float] = {}
        disqualified = False

        for rule in self.rules:
            try:
                contribution = rule.evaluate(
                    candidate=candidate,
                    module_name=module_name,
                    error_span=error_span,
                    original_text=original_text,
                    tokens=tokens,
                    peer_candidates=peer_candidates,
                    config=self.config,
                )
            except Exception:
                logger.warning("Rule %s failed, using 0.0", rule.name)
                contribution = 0.0

            breakdown[rule.name] = contribution

            if contribution == DISQUALIFY_SCORE:
                disqualified = True
                total = DISQUALIFY_SCORE
                break

            total += contribution

        return ScoredCandidate(
            candidate=candidate,
            module_name=module_name,
            final_score=total,
            rule_breakdown=breakdown if self.config.debug.log_score_breakdown else {},
        )

    def score_all(
        self,
        candidates: list[tuple[ModuleName, GECUnionCandidateEdit]],
        error_span: ErrorSpan,
        original_text: str,
        tokens: list[Token],
    ) -> list[ScoredCandidate]:
        scored: list[ScoredCandidate] = []
        for module_name, candidate in candidates:
            sc = self.score_candidate(
                candidate=candidate,
                module_name=module_name,
                error_span=error_span,
                original_text=original_text,
                tokens=tokens,
                peer_candidates=candidates,
            )
            scored.append(sc)
        return scored

    def filter_qualified(self, scored: list[ScoredCandidate]) -> list[ScoredCandidate]:
        return [s for s in scored if s.final_score != DISQUALIFY_SCORE]
