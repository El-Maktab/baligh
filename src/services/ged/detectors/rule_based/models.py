"""Shared models for the rule-based GED subsystem.

NOTE: was made to solve the circular imports problems.

Authors:
    Amir Anwar
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from src.core.schemas import MorphAnalysis, Token
from src.services.ged.confidence import TIER_CONFIDENCE
from src.services.ged.schemas import ErrorCategory, ErrorSource, ProvenanceTier

RuleFn = Callable[
    [str, list[Token], list[list[MorphAnalysis]]],
    list[tuple[int, int, int]],
]


@dataclass
class RuleEntry:
    """Metadata and callable for one rule."""

    rule_id: str
    category: ErrorCategory
    subtype: str
    tier: ProvenanceTier
    explanation: str
    fn: RuleFn
    source: ErrorSource = field(default=ErrorSource.RULE_BASED)

    @property
    def confidence(self) -> float:
        """Confidence derived from the ruls tier."""
        return TIER_CONFIDENCE[self.tier]
