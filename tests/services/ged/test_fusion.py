"""Unit tests for the GED Fusion Layer.

Each test targets one cell of the conflict-resolution decision table defined
in the `./docs/ged/ged_fusion.md`


Authors:
    Amir Anwar
"""

from src.services.ged.fusion import resolve_overlaps
from src.services.ged.schemas import (
    ErrorCategory,
    ErrorSource,
    ErrorSpan,
    ProvenanceTier,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_R = ErrorSource.RULE_BASED
_L = ErrorSource.LEXICON_MATCHER
_N = ErrorSource.SEQUENCE_LABELER

T1 = ProvenanceTier.TIER_1_RULE_DERIVED
T2 = ProvenanceTier.TIER_2_RULE_SUPPORTED
T3 = ProvenanceTier.TIER_3_STATISTICAL

OT = ErrorCategory.ORTHOGRAPHY
SY = ErrorCategory.SYNTAX
PC = ErrorCategory.PUNCTUATION


def span(
    start: int,
    end: int,
    category: ErrorCategory = OT,
    confidence: float = 0.9,
    tier: ProvenanceTier = T1,
    sources: list[ErrorSource] | None = None,
    subtype: str = "test",
    explanation_text: str | None = "تفسير",
    explanation_eligible: bool = True,
) -> ErrorSpan:
    """Convenience factory for ErrorSpan objects."""
    return ErrorSpan(
        span=(start, end),
        token_refs=[0],
        category=category,
        subtype=subtype,
        confidence=confidence,
        sources=sources or [_R],
        provenance_tier=tier,
        explanation_eligible=explanation_eligible,
        explanation_text=explanation_text,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_input(self):
        """Empty list returns empty list."""
        assert resolve_overlaps([]) == []

    def test_single_span_passthrough(self):
        """A single span is returned unchanged."""
        s = span(0, 5)
        result = resolve_overlaps([s])
        assert len(result) == 1
        assert result[0].span == (0, 5)

    def test_no_overlap_passthrough(self):
        """Non-overlapping spans all survive in offset order."""
        spans = [
            span(10, 15, OT),
            span(0, 4, OT),
            span(20, 25, SY),
        ]
        result = resolve_overlaps(spans)
        assert len(result) == 3
        # must come back sorted by start offset
        assert [s.span[0] for s in result] == [0, 10, 20]


class TestTierPriority:
    """Tests for the tier rules."""

    def test_tier1_suppresses_tier3(self):
        """When tier_1 and tier_3 overlap, tier_3 is suppressed."""
        rule_span = span(0, 5, OT, confidence=0.85, tier=T1)
        neural_span = span(2, 7, OT, confidence=0.95, tier=T3)
        result = resolve_overlaps([rule_span, neural_span])
        assert len(result) == 1
        assert result[0].provenance_tier == T1

    def test_tier3_replaced_by_tier1(self):
        """When tier_3 arrives before tier_1 in the raw list, tier_1 replaces it."""
        neural_span = span(0, 5, OT, confidence=0.95, tier=T3)
        rule_span = span(2, 7, OT, confidence=0.80, tier=T1)
        result = resolve_overlaps([neural_span, rule_span])
        assert len(result) == 1
        assert result[0].provenance_tier == T1

    def test_tier2_suppresses_tier3(self):
        """tier_2 takes priority over overlapping tier_3."""
        lexicon_span = span(0, 5, OT, confidence=0.80, tier=T2)
        neural_span = span(3, 8, OT, confidence=0.95, tier=T3)
        result = resolve_overlaps([lexicon_span, neural_span])
        assert len(result) == 1
        assert result[0].provenance_tier == T2


class TestExactSameSpan:
    """Tests for the exact same span rules."""

    def test_same_span_higher_confidence_wins(self):
        """Exact same span, same category: highest confidence span survives."""
        low = span(0, 5, OT, confidence=0.70, tier=T1, sources=[_R])
        high = span(0, 5, OT, confidence=0.95, tier=T1, sources=[_L])
        result = resolve_overlaps([low, high])
        assert len(result) == 1
        assert result[0].confidence == 0.95

    def test_same_span_sources_merged(self):
        """Exact same span, same category, same confidence: sources are merged."""
        a = span(0, 5, OT, confidence=0.90, tier=T1, sources=[_R])
        b = span(0, 5, OT, confidence=0.90, tier=T1, sources=[_L])
        result = resolve_overlaps([a, b])
        assert len(result) == 1
        assert set(result[0].sources) == {_R, _L}

    def test_same_span_different_category_higher_conf_wins(self):
        """Exact same span but different categories: higher confidence wins."""
        low = span(0, 5, OT, confidence=0.70, tier=T1)
        high = span(0, 5, SY, confidence=0.95, tier=T1)
        result = resolve_overlaps([low, high])
        assert len(result) == 1
        assert result[0].category == SY


class TestContainment:
    """Tests for the containment rules."""

    def test_containment_different_categories_both_kept(self):
        """Smaller span nested inside a larger span survives when categories differ."""
        outer = span(0, 20, SY, confidence=0.85, tier=T3, sources=[_N])
        inner = span(3, 8, OT, confidence=0.95, tier=T1, sources=[_R])
        result = resolve_overlaps([outer, inner])
        categories = {s.category for s in result}
        assert OT in categories
        assert SY in categories

    def test_containment_same_category_higher_conf_wins(self):
        """A smaller span nested inside a larger span of the same category best wins."""
        outer = span(0, 20, OT, confidence=0.70, tier=T1)
        inner = span(3, 8, OT, confidence=0.95, tier=T1)
        result = resolve_overlaps([outer, inner])
        assert len(result) == 1
        assert result[0].confidence == 0.95


class TestPartialOverlap:
    """Tests for the partial overlap rules."""

    def test_partial_overlap_same_tier_same_category_merged(self):
        """Two partial-overlap spans of same tier and category are merged."""
        a = span(0, 8, OT, confidence=0.85, tier=T1, sources=[_R])
        b = span(5, 12, OT, confidence=0.80, tier=T1, sources=[_L])
        result = resolve_overlaps([a, b])
        assert len(result) == 1
        assert result[0].span == (0, 12)
        assert set(result[0].sources) == {_R, _L}

    def test_partial_overlap_higher_conf_wins(self):
        """Partial overlap with different categories: higher confidence wins."""
        a = span(0, 8, OT, confidence=0.70, tier=T1)
        b = span(5, 12, SY, confidence=0.95, tier=T1)
        result = resolve_overlaps([a, b])
        assert len(result) == 1
        assert result[0].category == SY


class TestEligibilityNormalisation:
    """Tests for normalisation of explanation eligibility and text."""

    def test_tier3_explanation_cleared(self):
        """tier_3 spans must have explanation_eligible=False, explanation_text=None."""
        neural = span(
            0, 5, SY, tier=T3, explanation_text="some text", explanation_eligible=True
        )
        result = resolve_overlaps([neural])
        assert result[0].explanation_eligible is False
        assert result[0].explanation_text is None

    def test_tier1_eligibility_set(self):
        """tier_1 spans that were created without eligibility flag are corrected."""
        rule = span(
            0, 5, OT, tier=T1, explanation_text="تفسير", explanation_eligible=False
        )
        result = resolve_overlaps([rule])
        assert result[0].explanation_eligible is True

    def test_tier1_existing_explanation_preserved(self):
        """resolve_overlaps never overwrites an existing Arabic explanation string."""
        rule = span(0, 5, OT, tier=T1, explanation_text="حرف الجر يبدأ بهمزة قطع")
        result = resolve_overlaps([rule])
        assert result[0].explanation_text == "حرف الجر يبدأ بهمزة قطع"


class TestEndToEnd:
    """Tests for realistic end-to-end scenarios."""

    def test_multi_subsystem_realistic_scenario(self):
        """Simulate three subsystems firing on the same sentence.

        Sentence: 'ذهبوا الطلاب الى المدرسه'
          - Rule-based:   SY span (0,5)   verb-agreement      T1 0.95
          - Rule-based:   OT span (12,15) hamza-prep          T1 0.95
          - Rule-based:   OT span (16,23) ta-marbuta          T1 0.95
          - Neural:       SY span (0,12)  contextual          T3 0.72   overlaps rule SY
          - Neural:       OT span (14,17) contextual          T3 0.80   overlaps rule OT
        Expected:
          - Rule SY (0,5) survives; neural SY (0,12) is suppressed
          - Rule OT (12,15) survives; neural OT (14,17) contained, diff tier → removed
          - Rule OT (16,23) survives untouched
          = 3 spans total, all tier_1
        """
        rule_sy = span(
            0, 5, SY, confidence=0.95, tier=T1, subtype="verb_subject_agreement"
        )
        rule_ot_hamza = span(12, 15, OT, confidence=0.95, tier=T1, subtype="hamza")
        rule_ot_ta = span(16, 23, OT, confidence=0.95, tier=T1, subtype="ta_marbuta")
        neural_sy = span(
            0,
            12,
            SY,
            confidence=0.72,
            tier=T3,
            sources=[_N],
            subtype="contextual_neural",
        )
        neural_ot = span(
            14,
            17,
            OT,
            confidence=0.80,
            tier=T3,
            sources=[_N],
            subtype="contextual_neural",
        )

        raw = [rule_sy, rule_ot_hamza, rule_ot_ta, neural_sy, neural_ot]
        result = resolve_overlaps(raw)

        assert len(result) == 3
        assert all(s.provenance_tier == T1 for s in result)
        spans_out = {s.span for s in result}
        assert (0, 5) in spans_out
        assert (12, 15) in spans_out
        assert (16, 23) in spans_out
