"""Tests for edit segregation."""

from src.services.gec.modules.edit_tagger.common import Alignment, AlignmentType
from src.services.gec.modules.edit_tagger.preprocessing.segregator import (
    EditSegregator,
    SegregatedEdits,
)
from src.services.gec.schemas import EditOperation


class TestEditSegregator:
    """Tests for EditSegregator."""

    def test_punctuation_only_edits(self):
        """Test that punctuation-only edits are segregated into punctuation_edits."""
        segregator = EditSegregator()
        edits = [
            Alignment(
                source_start=0,
                source_end=1,
                target_start=0,
                target_end=1,
                operation=EditOperation.REPLACE,
                label="،",
                alignment_type=AlignmentType.CHARACTER,
            ),
        ]
        text = "،."
        result = segregator.segregate(text, edits)
        assert isinstance(result, SegregatedEdits)
        assert len(result.punctuation_edits) == 1
        assert len(result.non_punctuation_edits) == 0

    def test_non_punctuation_edits(self):
        """Test that non-punctuation edits are segregated into non_punctuation_edits."""
        segregator = EditSegregator()
        edits = [
            Alignment(
                source_start=0,
                source_end=1,
                target_start=0,
                target_end=1,
                operation=EditOperation.REPLACE,
                label="b",
                alignment_type=AlignmentType.CHARACTER,
            ),
        ]
        text = "ab"
        result = segregator.segregate(text, edits)
        assert len(result.punctuation_edits) == 0
        assert len(result.non_punctuation_edits) == 1

    def test_mixed_edits(self):
        """Test that mixed edits are correctly split between the two categories."""
        segregator = EditSegregator()
        edits = [
            Alignment(
                source_start=0,
                source_end=1,
                target_start=0,
                target_end=1,
                operation=EditOperation.REPLACE,
                label="b",
                alignment_type=AlignmentType.CHARACTER,
            ),
            Alignment(
                source_start=2,
                source_end=3,
                target_start=2,
                target_end=3,
                operation=EditOperation.REPLACE,
                label="؟",
                alignment_type=AlignmentType.CHARACTER,
            ),
        ]
        text = "ab."
        result = segregator.segregate(text, edits)
        assert len(result.punctuation_edits) == 1
        assert len(result.non_punctuation_edits) == 1

    def test_empty_edits(self):
        """Test that segregating with no edits produces empty lists."""
        segregator = EditSegregator()
        result = segregator.segregate("hello", [])
        assert len(result.punctuation_edits) == 0
        assert len(result.non_punctuation_edits) == 0

    def test_segregated_edits_text_preserved(self):
        """Test that the original text is preserved in the SegregatedEdits result."""
        segregator = EditSegregator()
        text = "hello"
        result = segregator.segregate(text, [])
        assert result.text == text

    def test_build_target_no_pnx(self):
        """Test that build_target_no_pnx filters out punctuation-only edits."""
        segregator = EditSegregator()
        edits = [
            Alignment(
                source_start=0,
                source_end=1,
                target_start=0,
                target_end=1,
                operation=EditOperation.KEEP,
            ),
        ]
        result = segregator.build_target_no_pnx(edits)
        assert len(result) == 1
