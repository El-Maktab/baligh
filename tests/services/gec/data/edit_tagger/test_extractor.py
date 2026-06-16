"""Tests for edit tag extraction."""

import pytest
from src.services.gec.modules.edit_tagger.common import Alignment
from src.services.gec.modules.edit_tagger.extractor import Extractor
from src.services.gec.schemas import EditOperation


class TestExtractTags:
    """Tests for Extractor.extract_tags."""

    def test_keep(self):
        """Test that a KEEP alignment produces a 'K' tag."""
        extractor = Extractor()
        alignments = [
            Alignment(
                source_start=0,
                source_end=0,
                target_start=0,
                target_end=0,
                operation=EditOperation.KEEP,
            )
        ]
        assert extractor.extract_tags(alignments) == ["K"]

    def test_replace(self):
        """Test that a REPLACE alignment produces an 'R_[label]' tag."""
        extractor = Extractor()
        alignments = [
            Alignment(
                source_start=0,
                source_end=0,
                target_start=0,
                target_end=0,
                operation=EditOperation.REPLACE,
                label="world",
            )
        ]
        assert extractor.extract_tags(alignments) == ["R_[world]"]

    def test_insert(self):
        """Test that an INSERT alignment produces an 'I_[label]' tag."""
        extractor = Extractor()
        alignments = [
            Alignment(
                source_start=0,
                source_end=-1,
                target_start=0,
                target_end=0,
                operation=EditOperation.INSERT,
                label="new",
            )
        ]
        assert extractor.extract_tags(alignments) == ["I_[new]"]

    def test_delete(self):
        """Test that a DELETE alignment produces a 'D' tag."""
        extractor = Extractor()
        alignments = [
            Alignment(
                source_start=0,
                source_end=0,
                target_start=0,
                target_end=-1,
                operation=EditOperation.DELETE,
            )
        ]
        assert extractor.extract_tags(alignments) == ["D"]

    def test_merge(self):
        """Test that a MERGE alignment produces an 'M' tag."""
        extractor = Extractor()
        alignments = [
            Alignment(
                source_start=0,
                source_end=1,
                target_start=0,
                target_end=0,
                operation=EditOperation.MERGE,
            )
        ]
        assert extractor.extract_tags(alignments) == ["M"]

    def test_split(self):
        """Test that a SPLIT alignment produces an 'S' tag."""
        extractor = Extractor()
        alignments = [
            Alignment(
                source_start=0,
                source_end=0,
                target_start=0,
                target_end=1,
                operation=EditOperation.SPLIT,
            )
        ]
        assert extractor.extract_tags(alignments) == ["S"]

    def test_replace_without_label_raises(self):
        """Test that a REPLACE alignment with None label raises ValueError."""
        extractor = Extractor()
        alignments = [
            Alignment(
                source_start=0,
                source_end=0,
                target_start=0,
                target_end=0,
                operation=EditOperation.REPLACE,
                label=None,
            )
        ]
        with pytest.raises(ValueError, match="Label cannot be None for REPLACE"):
            extractor.extract_tags(alignments)

    def test_insert_without_label_raises(self):
        """Test that an INSERT alignment with None label raises ValueError."""
        extractor = Extractor()
        alignments = [
            Alignment(
                source_start=0,
                source_end=-1,
                target_start=0,
                target_end=0,
                operation=EditOperation.INSERT,
                label=None,
            )
        ]
        with pytest.raises(ValueError, match="Label cannot be None for INSERT"):
            extractor.extract_tags(alignments)

    def test_mixed_sequence(self):
        """Test mixed alignmments produce the correct tag sequence."""
        extractor = Extractor()
        alignments = [
            Alignment(
                source_start=0,
                source_end=0,
                target_start=0,
                target_end=0,
                operation=EditOperation.KEEP,
            ),
            Alignment(
                source_start=1,
                source_end=1,
                target_start=1,
                target_end=1,
                operation=EditOperation.REPLACE,
                label="world",
            ),
            Alignment(
                source_start=2,
                source_end=2,
                target_start=2,
                target_end=2,
                operation=EditOperation.KEEP,
            ),
        ]
        assert extractor.extract_tags(alignments) == ["K", "R_[world]", "K"]

    def test_empty_alignments(self):
        """Test extracting tags from empty alignment list returns []."""
        extractor = Extractor()
        assert extractor.extract_tags([]) == []
