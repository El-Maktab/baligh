"""Tests for punctuation detection utilities."""

from src.services.gec.modules.edit_tagger.punctuation import (
    ARABIC_PUNCTUATION,
    LATIN_PUNCTUATION,
    PUNCTUATION_SET,
    is_punctuation,
)


class TestIsPunctuation:
    """Tests for the is_punctuation function."""

    def test_latin_period(self):
        """Test that a Latin period is detected as punctuation."""
        assert is_punctuation(".") is True

    def test_latin_comma(self):
        """Test that a Latin comma is detected as punctuation."""
        assert is_punctuation(",") is True

    def test_latin_question_mark(self):
        """Test that a Latin question mark is detected as punctuation."""
        assert is_punctuation("?") is True

    def test_arabic_comma(self):
        """Test that an Arabic comma is detected as punctuation."""
        assert is_punctuation("،") is True

    def test_arabic_semicolon(self):
        """Test that an Arabic semicolon is detected as punctuation."""
        assert is_punctuation("؛") is True

    def test_arabic_question_mark(self):
        """Test that an Arabic question mark is detected as punctuation."""
        assert is_punctuation("؟") is True

    def test_empty_string(self):
        """Test that an empty string is not detected as punctuation."""
        assert is_punctuation("") is False

    def test_letter(self):
        """Test that a Latin letter is not detected as punctuation."""
        assert is_punctuation("a") is False

    def test_arabic_letter(self):
        """Test that an Arabic letter is not detected as punctuation."""
        assert is_punctuation("م") is False

    def test_mixed_punctuation_and_letter(self):
        """Test that a mix of punctuation and letters is not detected as punctuation."""
        assert is_punctuation(".a") is False

    def test_multiple_punctuation_chars(self):
        """Test a string of only punctuation is detected as punctuation."""
        assert is_punctuation("...") is True

    def test_brackets(self):
        """Test that brackets are detected as punctuation."""
        assert is_punctuation("()") is True

    def test_single_quote(self):
        """Test that a single quote is detected as punctuation."""
        assert is_punctuation("'") is True

    def test_number(self):
        """Test that a number is not detected as punctuation."""
        assert is_punctuation("1") is False


class TestPunctuationSets:
    """Tests for the punctuation character sets."""

    def test_arabic_punctuation_non_empty(self):
        """Test that the Arabic punctuation set is non-empty."""
        assert len(ARABIC_PUNCTUATION) > 0

    def test_latin_punctuation_non_empty(self):
        """Test that the Latin punctuation set is non-empty."""
        assert len(LATIN_PUNCTUATION) > 0

    def test_union(self):
        """Test that PUNCTUATION_SET equals the union of Arabic and Latin sets."""
        assert PUNCTUATION_SET == ARABIC_PUNCTUATION | LATIN_PUNCTUATION

    def test_separation(self):
        """Test that Arabic and Latin punctuation sets are disjoint."""
        for p in ARABIC_PUNCTUATION:
            assert p not in LATIN_PUNCTUATION
