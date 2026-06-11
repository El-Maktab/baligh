"""Tests for the word boundary detection service in preprocessing."""

from src.services.preprocessing.utils.boundary import split_word_boundary


def test_split_word_boundary_empty():
    """Verify empty input behaves correctly as NWP mode."""
    assert split_word_boundary("") == ("", None, "NWP")


def test_split_word_boundary_nwp():
    """Verify text ending with delimiters results in NWP mode."""
    # Ends with space
    assert split_word_boundary("ذهب الطلاب ") == ("ذهب الطلاب ", None, "NWP")
    # Ends with Arabic punctuation
    assert split_word_boundary("ذهب الطلاب،") == ("ذهب الطلاب،", None, "NWP")
    # Ends with shared punctuation
    assert split_word_boundary("ذهب الطلاب!") == ("ذهب الطلاب!", None, "NWP")
    # Ends with multiple delimiters
    assert split_word_boundary("ذهب الطلاب،   ") == ("ذهب الطلاب،   ", None, "NWP")


def test_split_word_boundary_wac():
    """Verify text ending with letters results in WAC mode with correct fragment."""
    # Ends with Arabic letter
    assert split_word_boundary("ذهب الطلاب") == ("ذهب ", "الطلاب", "WAC")
    # Single word without whitespace
    assert split_word_boundary("ذهب") == ("", "ذهب", "WAC")
    # Delimiters and then incomplete word
    assert split_word_boundary("ذهب الطلاب، إلى الم") == (
        "ذهب الطلاب، إلى ",
        "الم",
        "WAC",
    )


def test_split_word_boundary_wac_punctuation_adjacent():
    """Verify WAC fragment is correctly extracted when bounded by punctuation.

    Words can be directly adjacent to punctuation without spaces (e.g. '،إلى').
    The backward scan must stop at any delimiter, not just whitespace.
    """
    # Word directly follows Arabic comma with no space
    assert split_word_boundary("ذهب الطلاب،إل") == ("ذهب الطلاب،", "إل", "WAC")
    # Word directly follows a period with no space
    assert split_word_boundary("انتهى.يبد") == ("انتهى.", "يبد", "WAC")


def test_split_word_boundary_cursor_offset_raises():
    """Verify that passing a cursor_offset raises NotImplementedError."""
    import pytest
    with pytest.raises(NotImplementedError):
        split_word_boundary("ذهب الطلاب", cursor_offset=5)

