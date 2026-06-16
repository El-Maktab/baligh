"""Tests for word and character-level alignment."""

from src.services.gec.modules.edit_tagger.aligner import Aligner
from src.services.gec.modules.edit_tagger.common import AlignmentType
from src.services.gec.schemas import EditOperation


class TestAlignWords:
    """Tests for word-level alignment via Aligner.align_words."""

    def test_identical_words(self):
        """Test that aligning identical words produces all KEEP operations."""
        aligner = Aligner()
        result = aligner.align_words("hello world", "hello world")
        assert len(result) == 2
        assert all(a.operation == EditOperation.KEEP for a in result)

    def test_single_word_replace(self):
        """Test that aligning a single different word produces a REPLACE operation."""
        aligner = Aligner()
        result = aligner.align_words("hello", "world")
        assert len(result) == 1
        assert result[0].operation == EditOperation.REPLACE

    def test_single_word_keep(self):
        """Test that aligning a single identical word produces a KEEP operation."""
        aligner = Aligner()
        result = aligner.align_words("hello", "hello")
        assert len(result) == 1
        assert result[0].operation == EditOperation.KEEP

    def test_delete(self):
        """Test that deleting a word produces a DELETE operation."""
        aligner = Aligner()
        result = aligner.align_words("hello world", "hello")
        ops = [a.operation for a in result]
        assert EditOperation.DELETE in ops

    def test_insert(self):
        """Test that inserting a word produces an INSERT operation."""
        aligner = Aligner()
        result = aligner.align_words("hello", "hello world")
        ops = [a.operation for a in result]
        assert EditOperation.INSERT in ops

    def test_replace_in_middle(self):
        """Test that replacing a middle word yields KEEP and REPLACE operations."""
        aligner = Aligner()
        result = aligner.align_words("the cat sat", "the dog sat")
        ops = [a.operation for a in result]
        assert EditOperation.KEEP in ops
        assert EditOperation.REPLACE in ops

    def test_word_alignment_type(self):
        """Test that word-level alignment produces WORD alignment type."""
        aligner = Aligner()
        result = aligner.align_words("hello", "hello")
        assert all(a.alignment_type == AlignmentType.WORD for a in result)

    def test_empty_source(self):
        """Test empty source with non-empty target yields all INSERTs."""
        aligner = Aligner()
        result = aligner.align_words("", "hello")
        assert all(a.operation == EditOperation.INSERT for a in result)

    def test_empty_target(self):
        """Test non-empty source with empty target yields all DELETEs."""
        aligner = Aligner()
        result = aligner.align_words("hello", "")
        assert all(a.operation == EditOperation.DELETE for a in result)

    def test_both_empty(self):
        """Test that aligning two empty strings returns an empty list."""
        aligner = Aligner()
        result = aligner.align_words("", "")
        assert result == []

    def test_merge(self):
        """Test merging two source words into one target yields MERGE."""
        aligner = Aligner()
        result = aligner.align_words("to day", "today")
        ops = [a.operation for a in result]
        assert EditOperation.MERGE in ops

    def test_split(self):
        """Test splitting one source word into two targets yields SPLIT."""
        aligner = Aligner()
        result = aligner.align_words("today", "to day")
        ops = [a.operation for a in result]
        assert EditOperation.SPLIT in ops


class TestAlignCharacters:
    """Tests for character-level alignment via Aligner.align_characters."""

    def test_identical_chars(self):
        """Test that aligning identical characters produces all KEEP operations."""
        aligner = Aligner()
        result = aligner.align_characters("abc", "abc")
        assert all(a.operation == EditOperation.KEEP for a in result)

    def test_single_char_replace(self):
        """Test a single character substitution yields KEEP and REPLACE."""
        aligner = Aligner()
        result = aligner.align_characters("abc", "axc")
        ops = [a.operation for a in result]
        assert EditOperation.KEEP in ops
        assert EditOperation.REPLACE in ops

    def test_character_alignment_type(self):
        """Test that character-level alignment produces CHARACTER alignment type."""
        aligner = Aligner()
        result = aligner.align_characters("a", "a")
        assert all(a.alignment_type == AlignmentType.CHARACTER for a in result)

    def test_char_insert(self):
        """Test that inserting a character yields an INSERT operation."""
        aligner = Aligner()
        result = aligner.align_characters("ac", "abc")
        ops = [a.operation for a in result]
        assert EditOperation.INSERT in ops

    def test_char_delete(self):
        """Test that deleting a character yields a DELETE operation."""
        aligner = Aligner()
        result = aligner.align_characters("abc", "ac")
        ops = [a.operation for a in result]
        assert EditOperation.DELETE in ops

    def test_empty_strings(self):
        """Test that aligning two empty strings returns an empty list."""
        aligner = Aligner()
        result = aligner.align_characters("", "")
        assert result == []

    def test_empty_source_char(self):
        """Test empty source with character target yields all INSERTs."""
        aligner = Aligner()
        result = aligner.align_characters("", "a")
        assert all(a.operation == EditOperation.INSERT for a in result)

    def test_empty_target_char(self):
        """Test character source with empty target yields all DELETEs."""
        aligner = Aligner()
        result = aligner.align_characters("a", "")
        assert all(a.operation == EditOperation.DELETE for a in result)


class TestAlignerCost:
    """Tests for internal cost functions of the Aligner."""

    def test_word_cost_identical(self):
        """Test that identical words have zero cost."""
        aligner = Aligner()
        assert aligner._word_cost("hello", "hello") == 0.0

    def test_word_cost_different(self):
        """Test that different words have a positive cost."""
        aligner = Aligner()
        assert aligner._word_cost("cat", "dog") > 0

    def test_merge_cost(self):
        """Test merging words whose concat matches target has zero cost."""
        aligner = Aligner()
        cost = aligner._merge_cost("to", "day", "today")
        assert cost == 0

    def test_split_cost(self):
        """Test that splitting a word into matching parts has zero cost."""
        aligner = Aligner()
        cost = aligner._split_cost("today", "to", "day")
        assert cost == 0

    def test_merge_cost_multiple(self):
        """Test merging multiple words whose concat matches target has zero cost."""
        aligner = Aligner()
        cost = aligner._merge_cost_multiple(["a", "b", "c"], "abc")
        assert cost == 0

    def test_split_cost_multiple(self):
        """Test that splitting a word into multiple matching parts has zero cost."""
        aligner = Aligner()
        cost = aligner._split_cost_multiple("abc", ["a", "b", "c"])
        assert cost == 0
