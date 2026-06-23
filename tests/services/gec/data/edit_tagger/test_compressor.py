"""Tests for tag compression."""

from src.services.gec.modules.edit_tagger.compressor import Compressor


class TestCompressTagsCount:
    """Tests for Compressor.compress_tags (count/old variant)."""

    def test_empty(self):
        compressor = Compressor()
        assert compressor.compress_tags([]) == ("", "")

    def test_single_tag(self):
        compressor = Compressor()
        assert compressor.compress_tags(["K"]) == ("K", "K")

    def test_all_keep(self):
        compressor = Compressor()
        assert compressor.compress_tags(["K", "K", "K"]) == ("K3", "K*")

    def test_all_delete(self):
        compressor = Compressor()
        assert compressor.compress_tags(["D", "D"]) == ("D2", "D*")

    def test_keep_and_replace(self):
        compressor = Compressor()
        assert compressor.compress_tags(["K", "K", "R_[hello]"]) == ("K2R_[hello]", "K*R_[hello]")

    def test_replace_sequence(self):
        compressor = Compressor()
        count_result, star_result = compressor.compress_tags(["R_[a]", "R_[b]"])
        assert "R" in count_result

    def test_insert_sequence(self):
        compressor = Compressor()
        count_result, star_result = compressor.compress_tags(["I_[x]", "I_[y]"])
        assert "I" in count_result

    def test_single_insert(self):
        compressor = Compressor()
        assert compressor.compress_tags(["I_[word]"]) == ("I_[word]", "I_[word]")

    def test_single_replace(self):
        compressor = Compressor()
        assert compressor.compress_tags(["R_[word]"]) == ("R_[word]", "R_[word]")

    def test_mixed_operations(self):
        compressor = Compressor()
        assert compressor.compress_tags(["K", "K", "D", "K"]) == ("K2DK", "K*DK")

    def test_merge_tags(self):
        compressor = Compressor()
        assert compressor.compress_tags(["M", "M", "M"]) == ("M3", "M*")

    def test_split_tags(self):
        compressor = Compressor()
        assert compressor.compress_tags(["S", "S"]) == ("S2", "S*")

    def test_complex_sequence(self):
        compressor = Compressor()
        assert compressor.compress_tags(["K", "K", "K", "D", "I_[x]", "K", "R_[a]"]) == ("K3DI_[x]KR_[a]", "K*DI_[x]KR_[a]")


class TestCompressTagsStar:
    """Tests for Compressor.compress_tags (star/new variant)."""

    def test_keep_star(self):
        compressor = Compressor()
        _, star = compressor.compress_tags(["K", "K", "K", "I_[ش]", "I_[س]", "I_[س]"])
        assert star == "K*I_[شسس*]"

    def test_delete_star(self):
        compressor = Compressor()
        _, star = compressor.compress_tags(["D", "D", "D"])
        assert star == "D*"

    def test_replace_star(self):
        compressor = Compressor()
        _, star = compressor.compress_tags(["R_[a]", "R_[b]", "R_[c]"])
        assert star == "R_[abc*]"

    def test_insert_star(self):
        compressor = Compressor()
        _, star = compressor.compress_tags(["I_[x]", "I_[y]"])
        assert star == "I_[xy*]"

    def test_single_insert_no_star(self):
        compressor = Compressor()
        _, star = compressor.compress_tags(["I_[z]"])
        assert star == "I_[z]"

    def test_single_replace_no_star(self):
        compressor = Compressor()
        _, star = compressor.compress_tags(["R_[z]"])
        assert star == "R_[z]"

    def test_single_keep_no_star(self):
        compressor = Compressor()
        _, star = compressor.compress_tags(["K"])
        assert star == "K"

    def test_merge_star(self):
        compressor = Compressor()
        _, star = compressor.compress_tags(["M", "M", "M", "M"])
        assert star == "M*"

    def test_split_star(self):
        compressor = Compressor()
        _, star = compressor.compress_tags(["S", "S"])
        assert star == "S*"

    def test_mixed_star(self):
        compressor = Compressor()
        _, star = compressor.compress_tags(["K", "K", "D", "I_[x]", "K"])
        assert star == "K*DI_[x]K"

    def test_both_variants_complex(self):
        compressor = Compressor()
        tags = ["K", "K", "K", "D", "D", "I_[a]", "I_[b]", "R_[c]", "K"]
        count, star = compressor.compress_tags(tags)
        assert count == "K3D2I_[ab]R_[c]K"
        assert star == "K*D*I_[ab*]R_[c]K"


class TestFormatRunCount:
    """Tests for Compressor._format_run_count."""

    def test_keep_count_greater_than_one(self):
        compressor = Compressor()
        result = compressor._format_run_count("K", ["K", "K"], start=0, count=2)
        assert result == "K2"

    def test_keep_count_one(self):
        compressor = Compressor()
        result = compressor._format_run_count("K", ["K"], start=0, count=1)
        assert result == "K"

    def test_delete_count(self):
        compressor = Compressor()
        result = compressor._format_run_count("D", ["D", "D", "D"], start=0, count=3)
        assert result == "D3"

    def test_replace_single(self):
        compressor = Compressor()
        result = compressor._format_run_count("R_[a]", ["R_[a]"], start=0, count=1)
        assert result == "R_[a]"

    def test_replace_multiple(self):
        compressor = Compressor()
        result = compressor._format_run_count("R_[a]", ["R_[a]", "R_[b]"], start=0, count=2)
        assert result == "R_[ab]"

    def test_insert_multiple(self):
        compressor = Compressor()
        result = compressor._format_run_count("I_[x]", ["I_[x]", "I_[y]"], start=0, count=2)
        assert result == "I_[xy]"


class TestFormatRunStar:
    """Tests for Compressor._format_run_star."""

    def test_keep_star(self):
        compressor = Compressor()
        result = compressor._format_run_star("K", ["K", "K", "K"], start=0, count=3)
        assert result == "K*"

    def test_keep_single(self):
        compressor = Compressor()
        result = compressor._format_run_star("K", ["K"], start=0, count=1)
        assert result == "K"

    def test_delete_star(self):
        compressor = Compressor()
        result = compressor._format_run_star("D", ["D", "D"], start=0, count=2)
        assert result == "D*"

    def test_replace_single(self):
        compressor = Compressor()
        result = compressor._format_run_star("R_[a]", ["R_[a]"], start=0, count=1)
        assert result == "R_[a]"

    def test_replace_multiple_star(self):
        compressor = Compressor()
        result = compressor._format_run_star("R_[a]", ["R_[a]", "R_[b]"], start=0, count=2)
        assert result == "R_[ab*]"

    def test_insert_multiple_star(self):
        compressor = Compressor()
        result = compressor._format_run_star("I_[x]", ["I_[x]", "I_[y]"], start=0, count=2)
        assert result == "I_[xy*]"
