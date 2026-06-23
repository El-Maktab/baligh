"""Tests for GED orthography rules."""

from __future__ import annotations

import pytest
from src.services.ged.features.subsystems.rule_based import (
    RuleBasedDetector,  # noqa: F401
)
from src.services.ged.features.subsystems.rule_based.registry import rule_registry
from src.services.ged.schemas import ErrorCategory

from tests.services.ged.rule_based.conftest import make_morph, make_token

_T = make_token
_M = make_morph


def _run(rule_id, tokens, morphs):
    text = " ".join(t.form for t in tokens)
    return rule_registry.run_one(rule_id, text, tokens, morphs)


@pytest.mark.parametrize(
    ("rule_id", "form", "pos", "lemma"),
    [
        ("OT_HAMZA_PREP", "الى", "PREP", "إِلَى"),
        ("OT_HAMZA_PREP", "او", "CONJ", "أَو"),
        ("OT_HAMZA_PREP", "اذا", "CONJ", "إِذا"),
        ("OT_HAMZA_PREP", "ان", "CONJ_SUB", "أَنَّ"),
        ("OT_HAMZA_PREP", "انه", "CONJ_SUB", "إِنَّ"),
        ("OT_ALIF_MAQSURA_ALA", "علي", "PREP", "عَلَى"),
        ("OT_ALIF_MAQSURA_HATTA", "حتي", "PREP", "حَتَّى"),
    ],
)
def test_hamza_and_alif_maqsura_rules(rule_id, form, pos, lemma):
    """Broad hamza and explicit alif-maqsura rules should flag intended forms."""
    tok = _T(form, (0, len(form)), 0)
    morph = _M(0, pos, lemma=lemma)

    spans = _run(rule_id, [tok], [[morph]])

    assert len(spans) == 1
    assert spans[0].span == (0, len(form))
    assert spans[0].category == ErrorCategory.ORTHOGRAPHY


def test_ot_tanwin_nasb_on_alif():
    """Flags tanwin nasb written on the final alif itself."""
    tok = _T("شيئاً", (0, 5), 0)
    morph = _M(0, "NOUN")

    spans = _run("OT_TANWIN_NASB_ON_ALIF", [tok], [[morph]])

    assert len(spans) == 1
    assert spans[0].span == (0, 5)
    assert spans[0].subtype == "tanwin"


def test_ot_idgham_an_ma():
    """Flags the explicit «عن ما» sequence before a verb."""
    tokens = [
        _T("عن", (0, 2), 0),
        _T("ما", (3, 5), 1),
        _T("أصابك", (6, 11), 2),
    ]
    morphs = [[_M(0, "PREP")], [_M(1, "PART")], [_M(2, "VERB", tense="past")]]

    spans = _run("OT_IDGHAM_AN_MA", tokens, morphs)

    assert len(spans) == 1
    assert spans[0].span == (0, 2)
    assert spans[0].subtype == "idgham"


def test_ot_idgham_min_ma():
    """Flags the explicit «من ما» sequence before a verb."""
    tokens = [
        _T("من", (0, 2), 0),
        _T("ما", (3, 5), 1),
        _T("أصابك", (6, 11), 2),
    ]
    morphs = [[_M(0, "PREP")], [_M(1, "PART")], [_M(2, "VERB", tense="past")]]

    spans = _run("OT_IDGHAM_MIN_MA", tokens, morphs)

    assert len(spans) == 1
    assert spans[0].span == (0, 2)
    assert spans[0].subtype == "idgham"


def test_ot_ta_marbuta_noun():
    """Flags a feminine noun that ends with ha instead of ta marbuta."""
    tok = _T("مدرسه", (0, 5), 0)
    morph = _M(0, "NOUN", gender="feminine")

    spans = _run("OT_TA_MARBUTA_NOUN", [tok], [[morph]])

    assert len(spans) == 1
    assert spans[0].category == ErrorCategory.ORTHOGRAPHY
    assert spans[0].subtype == "ta_marbuta"


def test_ot_ta_marbuta_adj():
    """Flags a feminine adjective that ends with ha instead of ta marbuta."""
    tok = _T("قويه", (0, 4), 0)
    morph = _M(0, "ADJ", gender="feminine")

    spans = _run("OT_TA_MARBUTA_ADJ", [tok], [[morph]])

    assert len(spans) == 1
    assert spans[0].category == ErrorCategory.ORTHOGRAPHY
    assert spans[0].subtype == "ta_marbuta"


def test_ot_ta_marbuta_noun_prop():
    """Flags a feminine proper noun that ends with ha instead of ta marbuta."""
    tok = _T("فاطمه", (0, 5), 0)
    morph = _M(0, "NOUN_PROP", gender="feminine")

    spans = _run("OT_TA_MARBUTA_NOUN_PROP", [tok], [[morph]])

    assert len(spans) == 1
    assert spans[0].category == ErrorCategory.ORTHOGRAPHY
    assert spans[0].subtype == "ta_marbuta"
