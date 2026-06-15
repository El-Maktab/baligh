"""Tests for GED orthography rules.

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


def test_ot_hamza_prep():
    """Flags a preposition that starts with bare alif instead of hamza."""
    tok = _T("الى", (0, 3), 0)
    morph = _M(0, "PREP", lemma="إلى")

    spans = _run("OT_HAMZA_PREP", [tok], [[morph]])

    assert len(spans) == 1
    assert spans[0].span == (0, 3)
    assert spans[0].category == ErrorCategory.ORTHOGRAPHY
    assert spans[0].subtype == "hamza"


def test_ot_alif_maqsura_prep():
    """Flags a target preposition that ends with ya instead of alif maqsura."""
    tok = _T("حتي", (0, 3), 0)
    morph = _M(0, "PREP", lemma="حَتَّى")

    spans = _run("OT_ALIF_MAQSURA_PREP", [tok], [[morph]])

    assert len(spans) == 1
    assert spans[0].category == ErrorCategory.ORTHOGRAPHY
    assert spans[0].subtype == "alif_maqsura"


def test_ot_ta_marbuta_noun():
    """Flags a feminine noun that ends with ha instead of ta marbuta."""
    tok = _T("مدرسه", (0, 5), 0)
    morph = _M(0, "NOUN", gender="feminine")

    spans = _run("OT_TA_MARBUTA_NOUN", [tok], [[morph]])

    assert len(spans) == 1
    assert spans[0].category == ErrorCategory.ORTHOGRAPHY
    assert spans[0].subtype == "ta_marbuta"


def test_ot_hamza_anna():
    """Flags an أن/إن-family form that starts with bare alif instead of hamza."""
    tok = _T("انه", (0, 3), 0)
    morph = _M(0, "CONJ_SUB", lemma="أَنَّ")

    spans = _run("OT_HAMZA_ANNA", [tok], [[morph]])

    assert len(spans) == 1
    assert spans[0].category == ErrorCategory.ORTHOGRAPHY
    assert spans[0].subtype == "hamza"


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
