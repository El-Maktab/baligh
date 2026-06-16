"""Tests for subword projection."""

from unittest.mock import patch

import pytest
from src.core.schemas import Token
from src.services.gec.modules.edit_tagger.common import (
    Alignment,
    AlignmentType,
    ProjectedExample,
)
from src.services.gec.modules.edit_tagger.compressor import Compressor
from src.services.gec.modules.edit_tagger.extractor import Extractor
from src.services.gec.modules.edit_tagger.projector import SubwordProjector
from src.services.gec.schemas import EditOperation


def _make_token(index: int, form: str, start: int, end: int) -> Token:
    return Token(
        index=index,
        form=form,
        span=(start, end),
        norm_span=(start, end),
    )


class TestComputeSpans:
    """Tests for compute_spans method."""

    def test_single_token(self):
        """Test compute_spans with a single token."""
        proj = SubwordProjector()
        spans = proj.compute_spans(["hello"])
        assert spans == [(0, 4)]

    def test_subword_tokens(self):
        """Test compute_spans with subword tokens."""
        proj = SubwordProjector()
        spans = proj.compute_spans(["كاتب", "##ون"])
        assert spans == [(0, 3), (4, 5)]

    def test_empty(self):
        """Test compute_spans with empty token list."""
        proj = SubwordProjector()
        assert proj.compute_spans([]) == []


class TestComputeGlobalSpans:
    """Tests for compute_global_spans method."""

    def test_basic(self):
        """Test compute_global_spans with basic inputs."""
        proj = SubwordProjector()
        result = proj.compute_global_spans((10, 20), (0, 3))
        assert result == (10, 13)

    def test_nonzero_start(self):
        """Test compute_global_spans with non-zero start offset."""
        proj = SubwordProjector()
        result = proj.compute_global_spans((5, 15), (2, 4))
        assert result == (7, 9)


class TestGetSpans:
    """Tests for get_spans method."""

    def test_returns_spans(self):
        """Test get_spans returns correct spans from tokens."""
        proj = SubwordProjector()
        tokens = [
            _make_token(0, "hello", 0, 4),
            _make_token(1, "world", 5, 9),
        ]
        spans = proj.get_spans(tokens)
        assert spans == [(0, 4), (5, 9)]

    def test_empty_tokens(self):
        """Test get_spans with empty token list."""
        proj = SubwordProjector()
        assert proj.get_spans([]) == []


class TestFindCorrespondingSubwordEdit:
    """Tests for find_corresponding_subword_edit method."""

    def test_find_in_range(self):
        """Test find_corresponding_subword_edit within span ranges."""
        proj = SubwordProjector()
        spans = [(0, 4), (5, 9)]
        assert proj.find_corresponding_subword_edit(2, spans) == 0
        assert proj.find_corresponding_subword_edit(7, spans) == 1

    def test_find_at_boundary(self):
        """Test find_corresponding_subword_edit at span boundaries."""
        proj = SubwordProjector()
        spans = [(0, 4), (5, 9)]
        assert proj.find_corresponding_subword_edit(0, spans) == 0
        assert proj.find_corresponding_subword_edit(4, spans) == 0
        assert proj.find_corresponding_subword_edit(5, spans) == 1
        assert proj.find_corresponding_subword_edit(9, spans) == 1

    def test_out_of_bounds_raises(self):
        """Test find_corresponding_subword_edit raises for out of bounds position."""
        proj = SubwordProjector()
        spans = [(0, 4), (5, 9)]
        with pytest.raises(ValueError, match="out of bounds"):
            proj.find_corresponding_subword_edit(10, spans)

    def test_gap_between_spans(self):
        """Test find_corresponding_subword_edit raises for gap between spans."""
        proj = SubwordProjector()
        spans = [(0, 2), (5, 8)]
        with pytest.raises(ValueError, match="out of bounds"):
            proj.find_corresponding_subword_edit(3, spans)


class TestTokenizeWords:
    """Tests for _tokenize_words method."""

    @patch("src.services.gec.modules.edit_tagger.projector.arabert_tokenize")
    def test_calls_arabert_per_word(self, mock_tokenize):
        """Test _tokenize_words calls arabert tokenizer per word."""
        mock_tokenize.side_effect = [["كاتب", "##ون"], ["الطالب"]]
        proj = SubwordProjector()
        result = proj._tokenize_words(["كاتبون", "الطالب"])
        assert result == [["كاتب", "##ون"], ["الطالب"]]
        assert mock_tokenize.call_count == 2


class TestProject:
    """Tests for project method."""

    @patch("src.services.gec.modules.edit_tagger.projector.arabert_tokenize")
    def test_basic_projection(self, mock_tokenize):
        """Test basic projection of edits to subword tokens."""
        mock_tokenize.side_effect = [["hello"], ["world"]]
        proj = SubwordProjector()
        tokens = [
            _make_token(0, "hello", 0, 4),
            _make_token(1, "world", 5, 9),
        ]
        edits = [
            Alignment(
                source_start=2,
                source_end=2,
                target_start=2,
                target_end=2,
                operation=EditOperation.REPLACE,
                label="x",
                alignment_type=AlignmentType.CHARACTER,
            ),
        ]
        result = proj.project(tokens, edits)
        assert len(result) == 2
        assert len(result[0]) == 1
        assert len(result[1]) == 0

    @patch("src.services.gec.modules.edit_tagger.projector.arabert_tokenize")
    def test_multiple_edits_same_subword(self, mock_tokenize):
        """Test project with multiple edits in the same subword."""
        mock_tokenize.return_value = ["hello"]
        proj = SubwordProjector()
        tokens = [
            _make_token(0, "hello", 0, 4),
        ]
        edits = [
            Alignment(
                source_start=1,
                source_end=1,
                target_start=1,
                target_end=1,
                operation=EditOperation.REPLACE,
                label="a",
                alignment_type=AlignmentType.CHARACTER,
            ),
            Alignment(
                source_start=3,
                source_end=3,
                target_start=3,
                target_end=3,
                operation=EditOperation.REPLACE,
                label="b",
                alignment_type=AlignmentType.CHARACTER,
            ),
        ]
        result = proj.project(tokens, edits)
        assert len(result) == 1
        assert len(result[0]) == 2

    @patch("src.services.gec.modules.edit_tagger.projector.arabert_tokenize")
    def test_empty_edits(self, mock_tokenize):
        """Test project with empty edits list."""
        mock_tokenize.return_value = ["hello"]
        proj = SubwordProjector()
        tokens = [_make_token(0, "hello", 0, 4)]
        result = proj.project(tokens, [])
        assert len(result) == 1
        assert result[0] == []

    @patch("src.services.gec.modules.edit_tagger.projector.arabert_tokenize")
    def test_subword_projection(self, mock_tokenize):
        """Test projection of edits to subword tokens."""
        mock_tokenize.side_effect = [["كاتب", "##ون"]]
        proj = SubwordProjector()
        tokens = [_make_token(0, "كاتبون", 0, 5)]
        edits = [
            Alignment(
                source_start=2,
                source_end=2,
                target_start=2,
                target_end=2,
                operation=EditOperation.REPLACE,
                label="ت",
                alignment_type=AlignmentType.CHARACTER,
            ),
        ]
        result = proj.project(tokens, edits)
        assert len(result) == 2
        assert len(result[0]) == 1
        assert len(result[1]) == 0

    @patch("src.services.gec.modules.edit_tagger.projector.arabert_tokenize")
    def test_edit_in_second_subword(self, mock_tokenize):
        """Test projection of edits in the second subword token."""
        mock_tokenize.side_effect = [["كاتب", "##ون"]]
        proj = SubwordProjector()
        tokens = [_make_token(0, "كاتبون", 10, 15)]
        edits = [
            Alignment(
                source_start=14,
                source_end=14,
                target_start=14,
                target_end=14,
                operation=EditOperation.REPLACE,
                label="ن",
                alignment_type=AlignmentType.CHARACTER,
            ),
        ]
        result = proj.project(tokens, edits)
        assert len(result) == 2
        assert len(result[0]) == 0
        assert len(result[1]) == 1


class TestCompressProjection:
    """Tests for compress_projection method."""

    def test_basic(self):
        """Test compress_projection with basic projections."""
        proj = SubwordProjector()
        extractor = Extractor()
        compressor = Compressor()
        projections = [
            [
                Alignment(
                    source_start=0,
                    source_end=0,
                    target_start=0,
                    target_end=0,
                    operation=EditOperation.KEEP,
                ),
            ],
            [
                Alignment(
                    source_start=1,
                    source_end=1,
                    target_start=1,
                    target_end=1,
                    operation=EditOperation.REPLACE,
                    label="x",
                ),
            ],
        ]
        subwords = ["س", "##م", "ي", "##ه"]
        result = proj.compress_projection(
            subwords, projections, extractor, compressor
        )
        assert isinstance(result, ProjectedExample)
        assert result.subwords == subwords
        assert result.labels[0] == "K"
        assert result.labels[1] == "R_[x]"

    def test_empty_projections(self):
        """Test compress_projection with empty projections."""
        proj = SubwordProjector()
        extractor = Extractor()
        compressor = Compressor()
        projections = [[], []]
        subwords = ["س", "##م"]
        result = proj.compress_projection(
            subwords, projections, extractor, compressor
        )
        assert isinstance(result, ProjectedExample)
        assert result.subwords == subwords
        assert result.labels == ["", ""]
