"""Tests for GED semantics rules.

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


def _assert_semantic_hit(rule_id, form, morph):
    spans = _run(rule_id, [_T(form, (0, len(form)), 0)], [[morph]])
    assert len(spans) == 1
    assert spans[0].span == (0, len(form))
    assert spans[0].category == ErrorCategory.SEMANTICS
    assert spans[0].subtype == "lexical_usage"


def test_se_decades_iyat():
    """Flags decade expressions written with «ـينات» instead of «ـينيات»."""
    _assert_semantic_hit("SE_DECADES_IYAT", "الثلاثينات", _M(0, "NOUN"))


def test_se_moakharan():
    """Flags the lexical choice «مؤخرا»."""
    _assert_semantic_hit("SE_MOAKHARAN", "مؤخرا", _M(0, "ADV"))


def test_se_mutaakid():
    """Flags the lexical choice «متأكد»."""
    _assert_semantic_hit("SE_MUTAAKID", "متأكد", _M(0, "ADJ"))


def test_se_dhata():
    """Flags the lexical choice «ذاتا» in this usage."""
    _assert_semantic_hit("SE_DHATA", "ذاتا", _M(0, "NOUN"))


def test_se_khatir():
    """Flags the adjective «خطير» in this prescriptive usage."""
    _assert_semantic_hit("SE_KHATIR", "خطير", _M(0, "ADJ"))


def test_se_khammara():
    """Flags the lexical choice «خمارة» for a tavern/place meaning."""
    _assert_semantic_hit("SE_KHAMMARA", "خمارة", _M(0, "NOUN"))


def test_se_indhahala():
    """Flags the non-preferred verb form «انذهل»."""
    _assert_semantic_hit("SE_INDHAHALA", "انذهل", _M(0, "VERB"))


def test_se_biakmalihi():
    """Flags enclitic forms built on «بأكملـ»."""
    _assert_semantic_hit("SE_BIAKMALIHI", "بأكمله", _M(0, "ADV"))


def test_se_tahammama():
    """Flags the lexical choice «تحمم»."""
    _assert_semantic_hit("SE_TAHAMMAMA", "تحمم", _M(0, "VERB"))


def test_se_tashkilu():
    """Flags the lexical choice «تشكل» in the discouraged framing."""
    _assert_semantic_hit("SE_TASHKILU", "تشكل", _M(0, "VERB"))


def test_se_tasamama():
    """Flags the undigested doubled verb form «تصامم»."""
    _assert_semantic_hit("SE_TASAMAMA", "تصامم", _M(0, "VERB"))


def test_se_tatmin():
    """Flags the lexical choice «تطمين»."""
    _assert_semantic_hit("SE_TATMIN", "تطمين", _M(0, "NOUN"))


def test_se_ta3kisu():
    """Flags the lexical choice «تعكس» in the discouraged usage."""
    _assert_semantic_hit("SE_TA3KISU", "تعكس", _M(0, "VERB"))


def test_se_janoobi():
    """Flags the directional form «جنوبي» in this spatial usage."""
    _assert_semantic_hit("SE_JANOOBI", "جنوبي", _M(0, "ADJ"))


def test_se_khesisan():
    """Flags the lexical choice «خصيصا»."""
    _assert_semantic_hit("SE_KHESISAN", "خصيصا", _M(0, "ADV"))


def test_se_khalooq():
    """Flags the adjective «خلوق» in the discouraged usage."""
    _assert_semantic_hit("SE_KHALOOQ", "خلوق", _M(0, "ADJ"))


def test_se_raghma():
    """Flags the preposition-like usage of «رغم»."""
    _assert_semantic_hit("SE_RAGHMA", "رغم", _M(0, "NOUN"))


def test_se_rafah():
    """Flags the lexical choice «رفاة»."""
    _assert_semantic_hit("SE_RAFAH", "رفاة", _M(0, "NOUN"))


def test_se_shawyan():
    """Flags the source form «شويا»."""
    _assert_semantic_hit("SE_SHAWYAN", "شويا", _M(0, "NOUN"))


def test_se_araya():
    """Flags the lexical choice «عرايا» in this usage."""
    _assert_semantic_hit("SE_ARAYA", "عرايا", _M(0, "NOUN"))


def test_se_liwahdihi():
    """Flags the colloquial form «لوحده»."""
    _assert_semantic_hit("SE_LIWAHDIHI", "لوحده", _M(0, "ADV"))


def test_se_mahalat():
    """Flags the plural form «محلات» in this lexical sense."""
    _assert_semantic_hit("SE_MAHALAT", "محلات", _M(0, "NOUN"))


def test_se_nafoukh():
    """Flags noun forms built on «نافوخ»."""
    _assert_semantic_hit("SE_NAFOUKH", "نافوخه", _M(0, "NOUN"))


def test_se_nashet():
    """Flags the adjective «نشط» in the discouraged usage."""
    _assert_semantic_hit("SE_NASHET", "نشط", _M(0, "ADJ"))


def test_se_wallati():
    """Flags the connective form «والتي»."""
    _assert_semantic_hit("SE_WALLATI", "والتي", _M(0, "PRON_REL"))


def test_se_walladhi():
    """Flags the connective form «والذي»."""
    _assert_semantic_hit("SE_WALLADHI", "والذي", _M(0, "PRON_REL"))


def test_se_ittila3():
    """Flags the noun «إطلاع» in place of «اطّلاع»."""
    _assert_semantic_hit("SE_ITTILA3", "الإطلاع", _M(0, "NOUN"))


def test_se_idhtarada():
    """Flags the non-preferred verb form «اضطرد»."""
    _assert_semantic_hit("SE_IDHTARADA", "اضطرد", _M(0, "VERB"))


def test_se_mujbaa():
    """Flags the lexical form «مجباة»."""
    _assert_semantic_hit("SE_MUJBAA", "المجباة", _M(0, "ADJ"))


def test_se_mousoud():
    """Flags the lexical form «موصود»."""
    _assert_semantic_hit("SE_MOUSOUD", "الموصود", _M(0, "ADJ"))
