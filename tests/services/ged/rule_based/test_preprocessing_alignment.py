"""Integration checks between GED rules and the real preprocessing module.

These tests use the live preprocessing pipeline so that rule assumptions are
validated against actual tokenization and CAMeL/Farasa outputs.
"""

from __future__ import annotations

import pytest
from src.services.ged.detectors.rule_based import (
    RuleBasedDetector,  # noqa: F401
)
from src.services.ged.detectors.rule_based.registry import rule_registry
from src.services.preprocessing import PreprocessingInput, preprocess


def _run(rule_id: str, text: str):
    out = preprocess(PreprocessingInput(text=text))
    return out, rule_registry.run_one(rule_id, out.text, out.tokens, out.morph_features)


@pytest.mark.parametrize(
    ("rule_id", "text", "expected_span"),
    [
        ("OT_HAMZA_PREP", "الى ", (0, 3)),
        ("OT_HAMZA_PREP", "انه ", (0, 3)),
        ("PC_LATIN_COMMA_ARABIC", "قال , ثم ", (4, 5)),
        ("SY_DEM_PREP_HADHAYNI_CASE_NOM_NOUN", "بهذين الكتابان ", (6, 14)),
        ("SY_DEM_PREP_HATAYNI_CASE_NOM_NOUN", "بهاتين البطاقتان ", (7, 16)),
        ("SY_LAM_JUSSIVE", "لم يجري ", (3, 7)),
        ("SY_LAMMA_JUSSIVE", "لما يجري ", (4, 8)),
        ("SY_LA_NAHIYA_JUSSIVE", "لا تخافون ", (3, 9)),
        ("SY_LA_NAFIYA_NOT_JUSSIVE", "لا يخافوا ", (3, 9)),
        ("SY_INNA_SISTERS_DUAL_ACCUSATIVE", "إن الكتابان ", (3, 11)),
    ],
)
def test_rules_align_with_real_preprocessing(rule_id, text, expected_span):
    """Representative YAML rules should fire on real preprocessing outputs."""
    _out, spans = _run(rule_id, text)

    assert len(spans) == 1
    assert spans[0].span == expected_span


def test_attached_preposition_demonstrative_is_single_token_in_preprocessing():
    """Preprocessing keeps attached preposition + demonstrative as one token."""
    out, _spans = _run("SY_DEM_PREP_HADHAYNI_CASE_NOM_NOUN", "بهذين الكتابان ")

    assert [token.form for token in out.tokens] == ["بهذين", "الكتابان"]
    assert out.tokens[0].affix_structure == "PREP+STEM"
    assert out.morph_features[0][0].pos == "PRON_DEM"


def test_lam_jussive_relies_on_surface_not_mood_from_preprocessing():
    """CAMeL does not expose a useful mood tag for this live error example."""
    out, spans = _run("SY_LAM_JUSSIVE", "لم يجري ")

    assert out.morph_features[1][0].mood is None
    assert len(spans) == 1
