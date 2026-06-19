"""Unit tests for the AlternativeRanker module."""

import unittest

from src.core.schemas import Token
from src.services.gec.modules.dictionary.alternative_ranker import AlternativeRanker
from src.services.gec.modules.dictionary.arramooz_client import ArramoozClient


class TestAlternativeRanker(unittest.TestCase):
    """Tests the AlternativeRanker functionality."""

    def setUp(self):
        """Set up the test environment."""
        self.client = ArramoozClient()
        self.ranker = AlternativeRanker(arramooz_client=self.client)

    def test_ranking_logic(self):
        """Test the candidate ranking logic."""
        original_word = Token(
            index=0,
            form="بالمردسة",
            span=(0, 9),
            norm_span=(0, 9),
            affix_structure="PREP+DET+STEM",
        )

        candidates = [
            Token(
                index=0,
                form="بالمدرسة",
                span=(0, 9),
                norm_span=(0, 9),
                affix_structure="PREP+DET+STEM",
            ),
            Token(
                index=0,
                form="بالمرسة",
                span=(0, 8),
                norm_span=(0, 8),
                affix_structure="PREP+DET+STEM",
            ),
        ]

        ranked_candidates = self.ranker.rank_alternatives(original_word, candidates)

        self.assertEqual(ranked_candidates[0].form, "بالمدرسة")
        self.assertEqual(ranked_candidates[1].form, "بالمرسة")


if __name__ == "__main__":
    unittest.main()
