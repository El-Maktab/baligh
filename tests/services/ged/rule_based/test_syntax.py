"""Tests for GED syntax rules.

Each rule is covered by a single focused test case.

Authors:
    Amir Anwar
"""

from __future__ import annotations

from src.services.ged.features.subsystems.rule_based.registry import rule_registry
from src.services.ged.schemas import ErrorCategory

from tests.services.ged.rule_based.conftest import make_morph, make_token

_T = make_token
_M = make_morph


def _run(rule_id, tokens, morphs):
    text = " ".join(t.form for t in tokens)
    return rule_registry.run_one(rule_id, text, tokens, morphs)


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
    d_morph = _M(0, "PRON_DEM", gender="masculine")
    n_morph = _M(1, "NOUN", gender="feminine")

    spans = _run("SY_DEMONSTRATIVE_NOUN_GENDER", [demo, noun], [[d_morph], [n_morph]])

    assert len(spans) == 1
    assert spans[0].span == (0, 3)
    assert spans[0].category == ErrorCategory.SYNTAX
    assert spans[0].subtype == "demonstrative_noun_gender"


def test_sy_relative_pronoun_gender():
    """Flags a relative pronoun that mismatches the preceding noun's gender."""
    noun = _T("القول", (0, 5), 0)
    rel = _T("التي", (6, 10), 1)
    n_morph = _M(0, "NOUN", gender="masculine")
    r_morph = _M(1, "PRON_REL", gender="feminine")

    spans = _run("SY_RELATIVE_PRONOUN_GENDER", [noun, rel], [[n_morph], [r_morph]])

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
