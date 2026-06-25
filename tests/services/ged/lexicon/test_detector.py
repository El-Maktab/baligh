"""Tests for the lexicon GED detector.

Authors:
    Amir Anwar
"""

from __future__ import annotations

from src.services.ged.detectors.lexicon.detector import LexiconDetector
from src.services.ged.detectors.lexicon.models import LexiconPattern
from src.services.ged.schemas import ErrorCategory, ErrorSource, ProvenanceTier

from tests.services.ged.rule_based.conftest import make_token


def _pattern(**kwargs) -> LexiconPattern:
    return LexiconPattern.model_validate(kwargs)


def _detector() -> LexiconDetector:
    return LexiconDetector(
        patterns=[
            _pattern(
                id="TEST_TOKEN_ILA",
                match_type="token",
                wrong="الى",
                correct="إلى",
                category="OT",
                subtype="hamza",
                tier="tier_1_rule_derived",
                explanation="حرف الجر إلى يكتب بهمزة قطع.",
            ),
            _pattern(
                id="TEST_SPLIT_LAKIN",
                match_type="split",
                wrong_tokens=["لا", "كن"],
                correct="لكن",
                category="SP",
                subtype="common_split",
                tier="tier_1_rule_derived",
                explanation="تكتب الكلمة متصلة: لكن.",
            ),
            _pattern(
                id="TEST_MERGE_IN_SHA_ALLAH",
                match_type="merge",
                wrong="انشاءالله",
                correct_tokens=["إن", "شاء", "الله"],
                category="MG",
                subtype="common_merge",
                tier="tier_1_rule_derived",
                explanation="الصواب فصل العبارة: إن شاء الله.",
            ),
        ]
    )


def test_detector_name_matches_contract():
    """Detector name should align with the GED source contract."""
    detector = _detector()

    assert detector.name == "lexicon_matcher"


def test_token_pattern_returns_orthography_span():
    """Token patterns should produce one orthography span."""
    detector = _detector()
    tokens = [
        make_token("ذهب", (0, 3), 0),
        make_token("الى", (4, 7), 1),
    ]

    spans = detector.detect("ذهب الى", "ذهب الى", tokens, [[], []])

    assert len(spans) == 1
    assert spans[0].span == (4, 7)
    assert spans[0].token_refs == [1]
    assert spans[0].category == ErrorCategory.ORTHOGRAPHY
    assert spans[0].subtype == "hamza"
    assert spans[0].sources == [ErrorSource.LEXICON_MATCHER]


def test_split_pattern_spans_adjacent_tokens():
    """Split patterns should cover all adjacent wrong tokens."""
    detector = _detector()
    tokens = [
        make_token("لا", (0, 2), 0),
        make_token("كن", (3, 5), 1),
        make_token("واضحا", (6, 12), 2),
    ]

    spans = detector.detect("لا كن واضحا", "لا كن واضحا", tokens, [[], [], []])

    assert len(spans) == 1
    assert spans[0].span == (0, 5)
    assert spans[0].token_refs == [0, 1]
    assert spans[0].category == ErrorCategory.SPLIT
    assert spans[0].subtype == "common_split"


def test_merge_pattern_spans_one_token():
    """Merge patterns should cover the merged surface token."""
    detector = _detector()
    tokens = [
        make_token("انشاءالله", (0, 9), 0),
        make_token("خير", (10, 13), 1),
    ]

    spans = detector.detect("انشاءالله خير", "انشاءالله خير", tokens, [[], []])

    assert len(spans) == 1
    assert spans[0].span == (0, 9)
    assert spans[0].token_refs == [0]
    assert spans[0].category == ErrorCategory.MERGE
    assert spans[0].subtype == "common_merge"


def test_confidence_is_derived_from_tier():
    """Lexicon confidence should come from the provenance tier."""
    detector = LexiconDetector(
        patterns=[
            _pattern(
                id="TEST_TIER_2",
                match_type="token",
                wrong="مشبوهة",
                correct="مشتبهة",
                category="OT",
                subtype="spelling",
                tier="tier_2_rule_supported",
                explanation="صيغة شائعة الالتباس.",
            )
        ]
    )
    tokens = [make_token("مشبوهة", (0, 6), 0)]

    spans = detector.detect("مشبوهة", "مشبوهة", tokens, [[]])

    assert spans[0].provenance_tier == ProvenanceTier.TIER_2_RULE_SUPPORTED
    assert spans[0].confidence == 0.8


def test_curated_matching_preserves_correct_forms():
    """Curated matching should not collapse correct forms into wrong patterns."""
    detector = _detector()
    tokens = [
        make_token("إلى", (0, 3), 0),
        make_token("لكن", (4, 7), 1),
        make_token("إن", (8, 10), 2),
        make_token("شاء", (11, 14), 3),
        make_token("الله", (15, 19), 4),
    ]

    spans = detector.detect(
        "إلى لكن إن شاء الله",
        "إلى لكن إن شاء الله",
        tokens,
        [[], [], [], [], []],
    )

    assert spans == []
