"""Rule registry for GED rule-based.

This module provides RuleRegistry, the central dispatch engine for all
rule-based error detection. Both authoring modes (Python decorator and YAML
declarative) ultimately store their rules as RuleEntry objects inside the
same registry instance (rule_registry).

Rule functions must have the signature::

    (text: str,
     tokens: list[Token],
     morph_features: list[list[MorphAnalysis]]
    ) -> list[tuple[int, int, int]]

where each returned tuple is (span_start, span_end, token_index). The
registry assembles the full ErrorSpan from the metadata stored in the
RuleEntry, so rule functions stay focused on *finding* the error location
and nothing else.

Authors:
  Amir Anwar
"""

from __future__ import annotations

from collections.abc import Callable

from loguru import logger

from src.core.schemas import MorphAnalysis, Token
from src.services.ged.detectors.rule_based.models import RuleEntry, RuleFn
from src.services.ged.schemas import (
    ErrorCategory,
    ErrorSource,
    ErrorSpan,
    ProvenanceTier,
)


class RuleRegistry:
    """Central registry for all GED rule functions."""

    def __init__(self) -> None:
        """Initialise an empty rule registry."""
        self._rules: list[RuleEntry] = []

    # #######################################################
    # Registration API (dectorator pattern)
    # https://refactoring.guru/design-patterns/decorator
    # #######################################################

    def register(
        self,
        *,  # NOTE: This forces the caller to use named arguments
        rule_id: str,
        category: ErrorCategory,
        subtype: str,
        tier: ProvenanceTier,
        explanation: str,
        source: ErrorSource = ErrorSource.RULE_BASED,
    ) -> Callable[[RuleFn], RuleFn]:
        """Decorator factory that registers a Python rule function.

        Usage::

            @rule_registry.register(
                rule_id="OT_HAMZA_PREP",
                category=ErrorCategory.ORTHOGRAPHY,
                subtype="hamza",
                tier=ProvenanceTier.TIER_1_RULE_DERIVED,
                explanation="حرف الجر يبدأ بهمزة قطع",
            )
            def check_hamza_prep(text, tokens, morph_features):
                ...
        """

        def decorator(fn: RuleFn) -> RuleFn:
            entry = RuleEntry(
                rule_id=rule_id,
                category=category,
                subtype=subtype,
                tier=tier,
                explanation=explanation,
                fn=fn,
                source=source,
            )
            self._rules.append(entry)
            logger.debug("Registered rule: {}", rule_id)
            return fn

        return decorator

    def register_entry(self, entry: RuleEntry) -> None:
        """Directly register a pre-built RuleEntry.

        Used by the YAML rules to register compiled entries without going
        through the decorator interface.
        """
        self._rules.append(entry)
        logger.debug("Registered entry: {}", entry.rule_id)

    # #######################################################
    # Execution functios
    # #######################################################

    def run_all(
        self,
        text: str,
        tokens: list[Token],
        morph_features: list[list[MorphAnalysis]],
    ) -> list[ErrorSpan]:
        """Run all registered rule and all collected errors.

        Individual rule failures are caught and logged; they do not prevent
        other rules from running.
        """
        spans: list[ErrorSpan] = []
        for entry in self._rules:
            try:
                raw = entry.fn(text, tokens, morph_features)
                spans.extend(self._build_spans(entry, raw))
            except Exception:
                logger.exception(
                    "Rule {} raised an unexpected exception and was skipped.",
                    entry.rule_id,
                )
        return spans

    def run_one(
        self,
        rule_id: str,
        text: str,
        tokens: list[Token],
        morph_features: list[list[MorphAnalysis]],
    ) -> list[ErrorSpan]:
        """Run a single rule by id (mainly used for testing rules)."""
        for entry in self._rules:
            if entry.rule_id == rule_id:
                raw = entry.fn(text, tokens, morph_features)
                return self._build_spans(entry, raw)

        raise KeyError(f"No rule registered with id={rule_id!r}")

    # ####################################################################
    # Info and checking functions.
    # ####################################################################

    def list_rules(self) -> list[RuleEntry]:
        """Return a copy of the current rule list."""
        return list(self._rules)

    def filter_rules(
        self,
        *,
        category: ErrorCategory | None = None,
        tier: ProvenanceTier | None = None,
        id_prefix: str | None = None,
    ) -> list[RuleEntry]:
        """Return rules matching all supplied filters.

        Args:
            category: If set, keep only rules of this category.
            tier: If set, keep only rules at this provenance tier.
            id_prefix: If set, keep only rules whose id starts with this prefix.
        """
        result = list(self._rules)
        if category is not None:
            result = [r for r in result if r.category == category]
        if tier is not None:
            result = [r for r in result if r.tier == tier]
        if id_prefix is not None:
            result = [r for r in result if r.rule_id.startswith(id_prefix)]
        return result

    # ####################################################################
    # Internal helpers
    # ####################################################################

    @staticmethod
    def _build_spans(
        entry: RuleEntry,
        raw: list[tuple[int, int, int]],
    ) -> list[ErrorSpan]:
        """Convert (start, end, token_idx) into ErrorSpans ."""
        return [
            ErrorSpan(
                span=(start, end),
                token_refs=[token_idx],
                category=entry.category,
                subtype=entry.subtype,
                confidence=entry.confidence,
                sources=[entry.source],
                provenance_tier=entry.tier,
                explanation_eligible=True,
                explanation_text=entry.explanation,
            )
            for start, end, token_idx in raw
        ]


# ####################################################################
# Module-level singleton
# ####################################################################

rule_registry = RuleRegistry()
