"""Tests for the word boundary service in preprocessing."""

from src.services.preprocessing.utils.boundary import split_word_boundary


def test_split_word_boundary_empty():
    """empty input is NWP mode."""
    assert split_word_boundary("") == ("", None, "NWP")


def test_split_word_boundary_nwp():
    """text ending with delimiters is in NWP mode."""
    assert split_word_boundary("ذهب الطلاب ") == ("ذهب الطلاب ", None, "NWP")
    assert split_word_boundary("ذهب الطلاب،") == ("ذهب الطلاب،", None, "NWP")
    assert split_word_boundary("ذهب الطلاب!") == ("ذهب الطلاب!", None, "NWP")
    assert split_word_boundary("ذهب الطلاب،   ") == ("ذهب الطلاب،   ", None, "NWP")


def test_split_word_boundary_wac():
    """text ending with letters is in WAC mode with correct fragment."""
    assert split_word_boundary("ذهب الطلاب") == ("ذهب ", "الطلاب", "WAC")
    assert split_word_boundary("ذهب") == ("", "ذهب", "WAC")
    assert split_word_boundary("ذهب الطلاب، إلى الم") == (
        "ذهب الطلاب، إلى ",
        "الم",
        "WAC",
    )


def test_split_word_boundary_wac_punctuation_adjacent():
    """WAC fragment is extracted when followed by punctuation"""
    assert split_word_boundary("ذهب الطلاب،إل") == ("ذهب الطلاب،", "إل", "WAC")
    assert split_word_boundary("انتهى.يبد") == ("انتهى.", "يبد", "WAC")


def test_split_word_boundary_cursor_offset_raises():
    """passing a cursor_offset raises NotImplementedError."""
    import pytest
    with pytest.raises(NotImplementedError):
        split_word_boundary("ذهب الطلاب", cursor_offset=5)

