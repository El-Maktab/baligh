"""Tests for the text normalization in preprocessing service."""

from src.services.preprocessing.utils.normalizer import (
    normalize_text,
    normalize_with_mapping,
    canonicalize_alif,
    canonicalize_ya,
    canonicalize_ta_marbuta,
)


def test_normalize_text_basic():
    """normalize_text should correctly normalize text without mapping."""
    raw = "ذهب   الطلاب   إلى المدرسة"
    expected = "ذهب الطلاب إلى المدرسة"
    assert normalize_text(raw) == expected


def test_normalize_with_mapping_empty():
    """empty input should return empty results and correct maps."""
    assert normalize_with_mapping("") == ("", [0])


def test_normalize_with_mapping_whitespace():
    """check whitespace consolidation and correct mapping."""
    # Index: 01234
    raw = "أ   ب"  # multiple spaces
    # normalized: "أ ب" (length -> 3)
    # Mapping:
    # normalized[0] ('أ') -> original index 0
    # normalized[1] (' ') -> original index 1 (the first space)
    # normalized[2] ('ب') -> original index 4
    # mapping[3] -> original length 5
    norm, mapping = normalize_with_mapping(raw)
    assert norm == "أ ب"
    assert mapping == [0, 1, 4, 5]


def test_normalize_with_mapping_nfkc():
    """NFKC normalization and mapping."""
    # 'ﻼ' (This is one character in unicode, U+FEFC) -> normalizes to 'لا' (U+0644 U+0627, length 2)
    ligature_char = "\uFEFC"  # ﻼ
    print(ligature_char)
    norm, mapping = normalize_with_mapping(ligature_char)
    assert norm == "\u0644\u0627"  # "لا"
    assert mapping == [0, 0, 1]


def test_canonicalize_alif():
    """canonicalize_alif transforms Alif variants correctly."""
    assert canonicalize_alif("أحمد") == "احمد"
    assert canonicalize_alif("إلى") == "الى"
    assert canonicalize_alif("آدم") == "ادم"
    assert canonicalize_alif("ذهب") == "ذهب"


def test_canonicalize_ya():
    """canonicalize_ya transforms Alif Maqsura correctly."""
    assert canonicalize_ya("على") == "علي"
    assert canonicalize_ya("إلى") == "إلي"
    assert canonicalize_ya("يمشي") == "يمشي"
    assert canonicalize_ya("ذهب") == "ذهب"


def test_canonicalize_ta_marbuta():
    """canonicalize_ta_marbuta transforms Ta Marbuta correctly."""
    assert canonicalize_ta_marbuta("مدرسة") == "مدرسه"
    assert canonicalize_ta_marbuta("طالبة") == "طالبه"
    assert canonicalize_ta_marbuta("كتابه") == "كتابه"
    assert canonicalize_ta_marbuta("ذهب") == "ذهب"
