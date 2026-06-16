"""Tests for common data structures and enums."""

from src.services.gec.modules.edit_tagger.common import (
    Alignment,
    AlignmentType,
    BackPointer,
)
from src.services.gec.schemas import EditOperation


class TestAlignmentType:
    """Tests for the AlignmentType enum."""

    def test_values(self):
        """Test that AlignmentType enum members have the correct string values."""
        assert AlignmentType.WORD == "WORD"
        assert AlignmentType.CHARACTER == "CHARACTER"

    def test_is_str_enum(self):
        """Test that AlignmentType members are instances of str."""
        assert isinstance(AlignmentType.WORD, str)
        assert isinstance(AlignmentType.CHARACTER, str)


class TestAlignment:
    """Tests for the Alignment dataclass."""

    def test_defaults(self):
        """Test that Alignment defaults label to None and alignment_type to WORD."""
        a = Alignment(
            source_start=0,
            source_end=0,
            target_start=0,
            target_end=0,
            operation=EditOperation.KEEP,
        )
        assert a.label is None
        assert a.alignment_type == AlignmentType.WORD

    def test_with_label(self):
        """Test that Alignment stores the provided label."""
        a = Alignment(
            source_start=0,
            source_end=0,
            target_start=0,
            target_end=0,
            operation=EditOperation.REPLACE,
            label="x",
        )
        assert a.label == "x"

    def test_with_character_alignment_type(self):
        """Test that Alignment stores a CHARACTER alignment_type override."""
        a = Alignment(
            source_start=0,
            source_end=0,
            target_start=0,
            target_end=0,
            operation=EditOperation.INSERT,
            alignment_type=AlignmentType.CHARACTER,
        )
        assert a.alignment_type == AlignmentType.CHARACTER


class TestBackPointer:
    """Tests for the BackPointer dataclass."""

    def test_creation(self):
        """Test that BackPointer stores operation and previous indices."""
        bp = BackPointer(operation=EditOperation.KEEP, prev_i=0, prev_j=0)
        assert bp.operation == EditOperation.KEEP
        assert bp.prev_i == 0
        assert bp.prev_j == 0

    def test_with_replace(self):
        """Test that BackPointer correctly stores REPLACE operation and indices."""
        bp = BackPointer(operation=EditOperation.REPLACE, prev_i=2, prev_j=3)
        assert bp.operation == EditOperation.REPLACE
        assert bp.prev_i == 2
        assert bp.prev_j == 3
