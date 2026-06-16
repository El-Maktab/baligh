"""Tests for tag compression."""

from src.services.gec.modules.edit_tagger.compressor import Compressor


class TestCompressTags:
    """Tests for Compressor.compress_tags."""

    def test_empty(self):
        """Test that compressing an empty tag list returns an empty string."""
        compressor = Compressor()
        assert compressor.compress_tags([]) == ""

    def test_single_tag(self):
        """Test that compressing a single tag returns it unchanged."""
        compressor = Compressor()
        assert compressor.compress_tags(["K"]) == "K"

    def test_all_keep(self):
        """Test that consecutive KEEP tags are compressed with a count."""
        compressor = Compressor()
        assert compressor.compress_tags(["K", "K", "K"]) == "K3"

    def test_all_delete(self):
        """Test that consecutive DELETE tags are compressed with a count."""
        compressor = Compressor()
        assert compressor.compress_tags(["D", "D"]) == "D2"

    def test_keep_and_replace(self):
        """Test that KEEP runs and REPLACE tags are concatenated correctly."""
        compressor = Compressor()
        assert compressor.compress_tags(["K", "K", "R_[hello]"]) == "K2R_[hello]"

    def test_replace_sequence(self):
        """Test that consecutive REPLACE tags merge their labels."""
        compressor = Compressor()
        result = compressor.compress_tags(["R_[a]", "R_[b]"])
        assert "R" in result

    def test_insert_sequence(self):
        """Test that consecutive INSERT tags merge their labels."""
        compressor = Compressor()
        result = compressor.compress_tags(["I_[x]", "I_[y]"])
        assert "I" in result

    def test_single_insert(self):
        """Test that a single INSERT tag is returned unchanged."""
        compressor = Compressor()
        assert compressor.compress_tags(["I_[word]"]) == "I_[word]"

    def test_single_replace(self):
        """Test that a single REPLACE tag is returned unchanged."""
        compressor = Compressor()
        assert compressor.compress_tags(["R_[word]"]) == "R_[word]"

    def test_mixed_operations(self):
        """Test that a mix of tag types is compressed correctly."""
        compressor = Compressor()
        result = compressor.compress_tags(["K", "K", "D", "K"])
        assert result == "K2DK"

    def test_merge_tags(self):
        """Test that consecutive MERGE tags are compressed with a count."""
        compressor = Compressor()
        assert compressor.compress_tags(["M", "M", "M"]) == "M3"

    def test_split_tags(self):
        """Test that consecutive SPLIT tags are compressed with a count."""
        compressor = Compressor()
        assert compressor.compress_tags(["S", "S"]) == "S2"

    def test_complex_sequence(self):
        """Test compression of a complex mixed sequence of tags."""
        compressor = Compressor()
        result = compressor.compress_tags(["K", "K", "K", "D", "I_[x]", "K", "R_[a]"])
        assert result == "K3DI_[x]KR_[a]"


class TestFormatRun:
    """Tests for Compressor._format_run."""

    def test_keep_count_greater_than_one(self):
        """Test that a KEEP run with count > 1 includes the count."""
        compressor = Compressor()
        result = compressor._format_run("K", ["K", "K"], start=0, count=2)
        assert result == "K2"

    def test_keep_count_one(self):
        """Test that a KEEP run with count 1 omits the count."""
        compressor = Compressor()
        result = compressor._format_run("K", ["K"], start=0, count=1)
        assert result == "K"

    def test_delete_count(self):
        """Test that a DELETE run with count 3 includes the count."""
        compressor = Compressor()
        result = compressor._format_run("D", ["D", "D", "D"], start=0, count=3)
        assert result == "D3"

    def test_replace_single(self):
        """Test that a single REPLACE tag is returned unchanged."""
        compressor = Compressor()
        result = compressor._format_run("R_[a]", ["R_[a]"], start=0, count=1)
        assert result == "R_[a]"

    def test_replace_multiple(self):
        """Test that multiple REPLACE tags merge their labels."""
        compressor = Compressor()
        result = compressor._format_run("R_[a]", ["R_[a]", "R_[b]"], start=0, count=2)
        assert result == "R_[ab]"

    def test_insert_multiple(self):
        """Test that multiple INSERT tags merge their labels."""
        compressor = Compressor()
        result = compressor._format_run("I_[x]", ["I_[x]", "I_[y]"], start=0, count=2)
        assert result == "I_[xy]"
