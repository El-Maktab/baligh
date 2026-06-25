"""Tests for GED syntax rules."""

from __future__ import annotations

import pytest
from src.services.ged.detectors.rule_based import (
    RuleBasedDetector,  # noqa: F401
)
from src.services.ged.detectors.rule_based.registry import rule_registry
from src.services.ged.schemas import ErrorCategory

from tests.services.ged.rule_based.conftest import make_morph, make_token

_T = make_token
_M = make_morph


def _run(rule_id, tokens, morphs):
    text = " ".join(t.form for t in tokens)
    return rule_registry.run_one(rule_id, text, tokens, morphs)


@pytest.mark.parametrize(
    ("rule_id", "tokens", "morphs", "expected_span"),
    [
        (
            "SY_DEM_HADHANI_FEM",
            [_T("هذان", (0, 4), 0), _T("البطاقتان", (5, 14), 1)],
            [[_M(0, "PRON_DEM")], [_M(1, "NOUN", gender="feminine", number="dual")]],
            (0, 4),
        ),
        (
            "SY_DEM_HATANI_MASC",
            [_T("هاتان", (0, 5), 0), _T("السلامان", (6, 14), 1)],
            [[_M(0, "PRON_DEM")], [_M(1, "NOUN", gender="masculine", number="dual")]],
            (0, 5),
        ),
        (
            "SY_DEM_HADHAYNI_FEM",
            [_T("هذين", (0, 4), 0), _T("البطاقتين", (5, 14), 1)],
            [[_M(0, "PRON_DEM")], [_M(1, "NOUN", gender="feminine", number="dual")]],
            (0, 4),
        ),
        (
            "SY_DEM_HATAYNI_MASC",
            [_T("هاتين", (0, 5), 0), _T("السلامين", (6, 14), 1)],
            [[_M(0, "PRON_DEM")], [_M(1, "NOUN", gender="masculine", number="dual")]],
            (0, 5),
        ),
        (
            "SY_DEM_HADHANI_CASE_OBLIQUE_NOUN",
            [_T("هذان", (0, 4), 0), _T("الكتابين", (5, 13), 1)],
            [
                [_M(0, "PRON_DEM")],
                [_M(1, "NOUN", gender="masculine", number="dual", case="accusative")],
            ],
            (5, 13),
        ),
        (
            "SY_DEM_HADHAYNI_CASE_NOM_NOUN",
            [_T("هذين", (0, 4), 0), _T("الكتابان", (5, 13), 1)],
            [
                [_M(0, "PRON_DEM")],
                [_M(1, "NOUN", gender="masculine", number="dual", case="nominative")],
            ],
            (5, 13),
        ),
        (
            "SY_DEM_PREP_HADHAYNI_CASE_NOM_NOUN",
            [_T("بهذين", (0, 5), 0), _T("الكتابان", (6, 14), 1)],
            [
                [_M(0, "PRON_DEM")],
                [_M(1, "NOUN", gender="masculine", number="dual", case="nominative")],
            ],
            (6, 14),
        ),
        (
            "SY_DEM_HATANI_CASE_OBLIQUE_NOUN",
            [_T("هاتان", (0, 5), 0), _T("البطاقتين", (6, 15), 1)],
            [
                [_M(0, "PRON_DEM")],
                [_M(1, "NOUN", gender="feminine", number="dual", case="accusative")],
            ],
            (6, 15),
        ),
        (
            "SY_DEM_HATAYNI_CASE_NOM_NOUN",
            [_T("هاتين", (0, 5), 0), _T("البطاقتان", (6, 15), 1)],
            [
                [_M(0, "PRON_DEM")],
                [_M(1, "NOUN", gender="feminine", number="dual", case="nominative")],
            ],
            (6, 15),
        ),
        (
            "SY_DEM_PREP_HATAYNI_CASE_NOM_NOUN",
            [_T("بهاتين", (0, 6), 0), _T("البطاقتان", (7, 16), 1)],
            [
                [_M(0, "PRON_DEM")],
                [_M(1, "NOUN", gender="feminine", number="dual", case="nominative")],
            ],
            (7, 16),
        ),
        (
            "SY_LAM_JUSSIVE",
            [_T("لم", (0, 2), 0), _T("يجري", (3, 7), 1)],
            [[_M(0, "PART")], [_M(1, "VERB", tense="present", mood="indicative")]],
            (3, 7),
        ),
        (
            "SY_LAMMA_JUSSIVE",
            [_T("لما", (0, 3), 0), _T("يجري", (4, 8), 1)],
            [[_M(0, "PART")], [_M(1, "VERB", tense="present", mood="indicative")]],
            (4, 8),
        ),
        (
            "SY_LA_NAHIYA_JUSSIVE",
            [_T("لا", (0, 2), 0), _T("تخافون", (3, 9), 1)],
            [
                [_M(0, "PART")],
                [_M(1, "VERB", tense="present", person="second", mood="indicative")],
            ],
            (3, 9),
        ),
        (
            "SY_LA_NAFIYA_NOT_JUSSIVE",
            [_T("لا", (0, 2), 0), _T("يخافوا", (3, 9), 1)],
            [[_M(0, "PART")], [_M(1, "VERB", tense="present", person="third")]],
            (3, 9),
        ),
        (
            "SY_INNA_SISTERS_DUAL_ACCUSATIVE",
            [_T("إن", (0, 2), 0), _T("الكتابان", (3, 11), 1)],
            [[_M(0, "PART")], [_M(1, "NOUN", number="dual", case="nominative")]],
            (3, 11),
        ),
    ],
)
def test_yaml_syntax_rules(rule_id, tokens, morphs, expected_span):
    """Each declarative syntax rule should flag its intended token span."""
    spans = _run(rule_id, tokens, morphs)

    assert len(spans) == 1
    assert spans[0].span == expected_span
    assert spans[0].category == ErrorCategory.SYNTAX


def test_sy_verb_subject_vso():
    """Flags a plural verb when it precedes an explicit nominal subject."""
    verb = _T("ذهبوا", (0, 5), 0)
    noun = _T("الطلاب", (6, 12), 1)
    v_morph = _M(0, "VERB", number="plural", tense="past")
    n_morph = _M(1, "NOUN", number="plural", definiteness="definite")

    spans = _run("SY_VERB_SUBJECT_VSO", [verb, noun], [[v_morph], [n_morph]])

    assert len(spans) == 1
    assert spans[0].span == (0, 5)
    assert spans[0].category == ErrorCategory.SYNTAX
    assert spans[0].subtype == "verb_subject_agreement"


def test_sy_noun_adj_definiteness():
    """Flags an adjective whose definiteness does not match the preceding noun."""
    noun = _T("الكتاب", (0, 6), 0)
    adj = _T("مفيد", (7, 11), 1)
    n_morph = _M(0, "NOUN", definiteness="definite")
    a_morph = _M(1, "ADJ", definiteness="indefinite")

    spans = _run("SY_NOUN_ADJ_DEFINITENESS", [noun, adj], [[n_morph], [a_morph]])

    assert len(spans) == 1
    assert spans[0].span == (7, 11)
    assert spans[0].category == ErrorCategory.SYNTAX
    assert spans[0].subtype == "noun_adjective_agreement"


def test_sy_demonstrative_noun_gender():
    """Flags a demonstrative pronoun that mismatches the following noun's gender."""
    demo = _T("هذا", (0, 3), 0)
    noun = _T("السلامة", (4, 11), 1)
    n_morph = _M(1, "NOUN", gender="feminine")

    spans = _run(
        "SY_DEMONSTRATIVE_NOUN_GENDER", [demo, noun], [[_M(0, "PRON_DEM")], [n_morph]]
    )

    assert len(spans) == 1
    assert spans[0].span == (0, 3)
    assert spans[0].category == ErrorCategory.SYNTAX
    assert spans[0].subtype == "demonstrative_noun_gender"


def test_sy_relative_pronoun_gender():
    """Flags a relative pronoun that mismatches the preceding noun's gender."""
    noun = _T("القول", (0, 5), 0)
    rel = _T("التي", (6, 10), 1)
    n_morph = _M(0, "NOUN", gender="masculine")

    spans = _run(
        "SY_RELATIVE_PRONOUN_GENDER",
        [noun, rel],
        [[n_morph], [_M(1, "PRON_REL", gender="feminine")]],
    )

    assert len(spans) == 1
    assert spans[0].span == (6, 10)
    assert spans[0].category == ErrorCategory.SYNTAX
    assert spans[0].subtype == "relative_pronoun_gender"


def test_sy_prep_dual_case():
    """Flags a dual noun left in nominative after a preposition."""
    prep = _T("في", (0, 2), 0)
    noun = _T("الكتابان", (3, 11), 1)
    p_morph = _M(0, "PREP")
    n_morph = _M(1, "NOUN", number="dual", case="nominative")

    spans = _run("SY_PREP_DUAL_CASE", [prep, noun], [[p_morph], [n_morph]])

    assert len(spans) == 1
    assert spans[0].span == (3, 11)
    assert spans[0].category == ErrorCategory.SYNTAX
    assert spans[0].subtype == "preposition_dual_case"


def test_sy_prep_sound_masc_plural_case():
    """Flags a sound masculine plural noun left in nominative after a preposition."""
    prep = _T("مع", (0, 2), 0)
    noun = _T("المسافرون", (3, 12), 1)
    p_morph = _M(0, "PREP")
    n_morph = _M(1, "NOUN", gender="masculine", number="plural", case="nominative")

    spans = _run(
        "SY_PREP_SOUND_MASC_PLURAL_CASE",
        [prep, noun],
        [[p_morph], [n_morph]],
    )

    assert len(spans) == 1
    assert spans[0].span == (3, 12)
    assert spans[0].category == ErrorCategory.SYNTAX
    assert spans[0].subtype == "preposition_sound_masc_plural_case"
