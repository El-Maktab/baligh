"""Models for lexicon GED patterns.

Authors:
    Amir Anwar
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from src.services.ged.confidence import TIER_CONFIDENCE
from src.services.ged.schemas import ErrorCategory, ProvenanceTier

LexiconMatchType = Literal["token", "split", "merge"]


class LexiconPattern(BaseModel):
    """A lexicon pattern."""

    model_config = ConfigDict(extra="forbid")

    id: str
    match_type: LexiconMatchType
    category: ErrorCategory
    subtype: str
    tier: ProvenanceTier
    explanation: str
    wrong: str | None = None
    wrong_tokens: list[str] | None = None
    correct: str | None = None
    correct_tokens: list[str] | None = None

    @model_validator(mode="after")
    def validate_shape(self) -> LexiconPattern:
        """Ensure fields match the selected pattern shape."""
        if self.match_type in {"token", "merge"}:
            if self.wrong is None:
                raise ValueError("token and merge patterns require wrong")
            if self.wrong_tokens is not None:
                raise ValueError("token and merge patterns cannot use wrong_tokens")

        if self.match_type == "split":
            if not self.wrong_tokens:
                raise ValueError("split patterns require wrong_tokens")
            if self.wrong is not None:
                raise ValueError("split patterns cannot use wrong")

        return self

    @property
    def confidence(self) -> float:
        """Confidence."""
        return TIER_CONFIDENCE[self.tier]
