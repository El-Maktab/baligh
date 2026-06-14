"""Tests for the GED RuleRegistry.

Covers:
- Registration via the @register decorator
- Registration via register_entry() (used by the YAML loader)
- run_all() aggregation
- run_one() isolation
- Per-rule exception isolation (one bad rule does not crash others)
- ErrorSpan metadata is taken from RuleEntry, not from rule functions
- filter_rules() by category, tier, and id_prefix
- Confidence is derived from tier via TIER_CONFIDENCE, not set per-rule

Authors:
    Amir Anwar
"""

from __future__ import annotations

import pytest
from src.services.ged.features.subsystems.rule_based.models import (
    TIER_CONFIDENCE,
    RuleEntry,
)
from src.services.ged.features.subsystems.rule_based.registry import RuleRegistry
from src.services.ged.schemas import ErrorCategory, ErrorSource, ProvenanceTier

from tests.services.ged.rule_based.conftest import make_morph, make_token

# ###########################################################################
# Helpers
# ###########################################################################

_T1 = ProvenanceTier.TIER_1_RULE_DERIVED
_T2 = ProvenanceTier.TIER_2_RULE_SUPPORTED
_OT = ErrorCategory.ORTHOGRAPHY
_SY = ErrorCategory.SYNTAX

_TOKEN = make_token("كتب", (0, 3), 0)
_MORPH = make_morph(0, "VERB")
_TOKENS = [_TOKEN]
_MORPHS = [[_MORPH]]


def _always_hit(text, tokens, morph_features):
    """Rule function that always returns the first token's span."""
    return [(tokens[0].span[0], tokens[0].span[1], tokens[0].index)]


def _never_hit(text, tokens, morph_features):
    """Rule function that never fires."""
    return []


def _crashing_rule(text, tokens, morph_features):
    """Rule function that raises an exception."""
    raise RuntimeError("Intentional crash for testing")


# ###########################################################################
# Tests
# ###########################################################################


class TestDecoratorRegistration:
    """@register decorator creates entries and run_one works."""

    def test_register_and_run_one(self):
        """A decorated rule should register and run through the registry."""
        reg = RuleRegistry()

        @reg.register(
            rule_id="TEST_RULE_A",
            category=_OT,
            subtype="hamza",
            tier=_T1,
            explanation="تفسير",
        )
        def my_rule(text, tokens, morph_features):
            return [(tokens[0].span[0], tokens[0].span[1], tokens[0].index)]

        spans = reg.run_one("TEST_RULE_A", "كتب", _TOKENS, _MORPHS)
        assert len(spans) == 1
        assert spans[0].span == (0, 3)

    def test_register_returns_original_function(self):
        """The decorator must return the unwrapped function (transparent)."""
        reg = RuleRegistry()

        @reg.register(
            rule_id="TEST_TRANSPARENT",
            category=_OT,
            subtype="test",
            tier=_T1,
            explanation="x",
        )
        def my_fn(text, tokens, morph_features):
            return []

        assert callable(my_fn)
        assert my_fn("", [], []) == []


class TestRegisterEntry:
    """register_entry() used by the YAML loader."""

    def test_register_entry_and_run_one(self):
        """A manually registered rule should be callable by id."""
        reg = RuleRegistry()
        entry = RuleEntry(
            rule_id="YAML_RULE_X",
            category=_OT,
            subtype="alif_maqsura",
            tier=_T1,
            explanation="تفسير",
            fn=_always_hit,
        )
        reg.register_entry(entry)

        spans = reg.run_one("YAML_RULE_X", "كتب", _TOKENS, _MORPHS)
        assert len(spans) == 1

    def test_run_one_unknown_id_raises(self):
        """Unknown ids should fail loudly so missing rules are easy to spot."""
        reg = RuleRegistry()
        with pytest.raises(KeyError):
            reg.run_one("NONEXISTENT", "text", _TOKENS, _MORPHS)


class TestRunAll:
    """run_all() aggregates spans from all registered rules."""

    def test_run_all_empty_registry(self):
        """An empty registry should produce no spans."""
        reg = RuleRegistry()
        assert reg.run_all("كتب", _TOKENS, _MORPHS) == []

    def test_run_all_collects_from_all_rules(self):
        """Every registered rule contributes its spans to the aggregate result."""
        reg = RuleRegistry()
        for rule_id in ("R1", "R2"):
            reg.register_entry(
                RuleEntry(
                    rule_id=rule_id,
                    category=_OT,
                    subtype="test",
                    tier=_T1,
                    explanation="x",
                    fn=_always_hit,
                )
            )

        spans = reg.run_all("كتب", _TOKENS, _MORPHS)
        assert len(spans) == 2

    def test_run_all_one_rule_crash_does_not_stop_others(self):
        """A crashing rule is skipped; the remaining rules still run."""
        reg = RuleRegistry()
        reg.register_entry(
            RuleEntry(
                rule_id="CRASH",
                category=_OT,
                subtype="test",
                tier=_T1,
                explanation="x",
                fn=_crashing_rule,
            )
        )
        reg.register_entry(
            RuleEntry(
                rule_id="SAFE",
                category=_OT,
                subtype="test",
                tier=_T1,
                explanation="x",
                fn=_always_hit,
            )
        )

        spans = reg.run_all("كتب", _TOKENS, _MORPHS)
        assert len(spans) == 1
        assert spans[0].span == (0, 3)


class TestErrorSpanMetadata:
    """ErrorSpan metadata must come from the RuleEntry, not the rule fn."""

    def test_span_metadata_from_entry(self):
        """The registry should copy metadata from the entry, not the function."""
        reg = RuleRegistry()
        reg.register_entry(
            RuleEntry(
                rule_id="META_TEST",
                category=_SY,
                subtype="verb_subject_agreement",
                tier=_T1,
                explanation="تفسير النحو",
                fn=_always_hit,
            )
        )
        spans = reg.run_all("كتب", _TOKENS, _MORPHS)
        assert spans[0].category == _SY
        assert spans[0].subtype == "verb_subject_agreement"
        assert spans[0].confidence == pytest.approx(TIER_CONFIDENCE[_T1])
        assert spans[0].provenance_tier == _T1
        assert spans[0].explanation_text == "تفسير النحو"
        assert spans[0].explanation_eligible is True
        assert spans[0].sources == [ErrorSource.RULE_BASED]

    def test_confidence_derives_from_tier(self):
        """Each tier maps to its fixed confidence value."""
        for tier, expected_confidence in TIER_CONFIDENCE.items():
            reg = RuleRegistry()
            reg.register_entry(
                RuleEntry(
                    rule_id="CONF_TEST",
                    category=_OT,
                    subtype="test",
                    tier=tier,
                    explanation="x",
                    fn=_always_hit,
                )
            )
            spans = reg.run_all("كتب", _TOKENS, _MORPHS)
            assert spans[0].confidence == pytest.approx(expected_confidence), (
                f"tier={tier} expected confidence={expected_confidence}"
            )


class TestFilterRules:
    """filter_rules() lets callers select a subset of rules."""

    def _registry_with_mixed_rules(self) -> RuleRegistry:
        reg = RuleRegistry()
        reg.register_entry(RuleEntry("OT_A", _OT, "hamza", _T1, "x", fn=_never_hit))
        reg.register_entry(
            RuleEntry("OT_B", _OT, "ta_marbuta", _T2, "x", fn=_never_hit)
        )
        reg.register_entry(RuleEntry("SY_A", _SY, "agreement", _T1, "x", fn=_never_hit))
        return reg

    @pytest.mark.parametrize(
        "filters, expected_ids",
        [
            ({"category": _OT}, {"OT_A", "OT_B"}),
            ({"tier": _T2}, {"OT_B"}),
            ({"id_prefix": "SY_"}, {"SY_A"}),
            ({"category": _OT, "tier": _T1}, {"OT_A"}),
        ],
    )
    def test_filter_rules(self, filters, expected_ids):
        """Filtering should return exactly the rules that match the selector."""
        reg = self._registry_with_mixed_rules()
        result = reg.filter_rules(**filters)
        assert {rule.rule_id for rule in result} == expected_ids
