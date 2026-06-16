"""Tests for dataset handling for edit tagging."""

from src.services.gec.modules.edit_tagger.common import Alignment, AlignmentType
from src.services.gec.features.datasets import DatasetSegregator
from src.services.gec.modules.edit_tagger.common import ParallelExample


from src.services.gec.schemas import EditOperation


class TestParallelExample:
    """Tests for the ParallelExample dataclass."""

    def test_creation(self):
        """Test that ParallelExample stores source and target strings."""
        ex = ParallelExample(source="hello", target="world")
        assert ex.source == "hello"
        assert ex.target == "world"


class TestDatasetSegregator:
    """Tests for DatasetSegregator.build_examples."""

    def test_build_examples_punctuation_only(self):
        """Test that edits reduce to punctuation-only and non-punctuation examples."""
        segregator = DatasetSegregator()
        edits = [
            Alignment(
                source_start=0,
                source_end=1,
                target_start=0,
                target_end=1,
                operation=EditOperation.KEEP,
                alignment_type=AlignmentType.CHARACTER,
            ),
        ]
        pnx, nopnx = segregator.build_examples("a", "a", edits)
        assert isinstance(pnx, ParallelExample)
        assert isinstance(nopnx, ParallelExample)
        assert pnx.source == "a"
        assert nopnx.source == "a"

    def test_build_examples_empty_edits(self):
        """Test that build_examples with no edits returns identical source strings."""
        segregator = DatasetSegregator()
        pnx, nopnx = segregator.build_examples("hello", "hello", [])
        assert pnx.source == "hello"
        assert nopnx.source == "hello"