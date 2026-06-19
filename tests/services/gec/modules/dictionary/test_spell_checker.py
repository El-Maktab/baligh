"""Unit tests for the SpellChecker module."""

import unittest

from src.core.schemas import Token
from src.core.utils.arabic import extract_affixes
from src.services.gec.modules.dictionary.arramooz_client import ArramoozClient
from src.services.gec.modules.dictionary.spell_checker import SpellChecker


class TestExtractAffixes(unittest.TestCase):
    """Tests the _extract_affixes helper function."""

    def test_no_affix(self):
        """Test a simple word with no clitics."""
        token = Token(
            index=0,
            form="مدرسة",
            span=(0, 5),
            norm_span=(0, 5),
            affix_structure="STEM",
        )
        prefix, stem, suffix = extract_affixes(token)
        self.assertEqual(prefix, "")
        self.assertEqual(stem, "مدرسة")
        self.assertEqual(suffix, "")

    def test_det_prefix(self):
        """Test definite article prefix."""
        token = Token(
            index=0,
            form="المدرسة",
            span=(0, 7),
            norm_span=(0, 7),
            affix_structure="DET+STEM",
        )
        prefix, stem, suffix = extract_affixes(token)
        self.assertEqual(prefix, "ال")
        self.assertEqual(stem, "مدرسة")
        self.assertEqual(suffix, "")

    def test_multiple_prefixes(self):
        """Test CONJ+PREP+DET stacked prefixes."""
        token = Token(
            index=0,
            form="وبالمدرسة",
            span=(0, 9),
            norm_span=(0, 9),
            affix_structure="CONJ+PREP+DET+STEM",
        )
        prefix, stem, suffix = extract_affixes(token)
        self.assertEqual(prefix, "وبال")
        self.assertEqual(stem, "مدرسة")
        self.assertEqual(suffix, "")

    def test_suffix(self):
        """Test stem with pronoun suffix."""
        token = Token(
            index=0,
            form="كتبوها",
            span=(0, 6),
            norm_span=(0, 6),
            affix_structure="STEM+PRON",
        )
        prefix, stem, suffix = extract_affixes(token)
        self.assertEqual(prefix, "")
        self.assertEqual(stem, "كتبو")
        self.assertEqual(suffix, "ها")

    def test_null_affix_structure(self):
        """Test punctuation token with null affix_structure."""
        token = Token(
            index=0,
            form="،",
            span=(0, 1),
            norm_span=(0, 1),
            affix_structure=None,
        )
        prefix, stem, suffix = extract_affixes(token)
        self.assertEqual(prefix, "")
        self.assertEqual(stem, "،")
        self.assertEqual(suffix, "")

    def test_no_over_stripping(self):
        """Test that 'ألوان' is not stripped of 'ال'."""
        token = Token(
            index=0,
            form="ألوان",
            span=(0, 5),
            norm_span=(0, 5),
            affix_structure="STEM",
        )
        prefix, stem, suffix = extract_affixes(token)
        self.assertEqual(prefix, "")
        self.assertEqual(stem, "ألوان")


class TestSpellChecker(unittest.TestCase):
    """Tests the SpellChecker functionality."""

    def setUp(self):
        """Set up the test environment."""
        self.arramooz_client = ArramoozClient()
        self.spell_checker = SpellChecker(self.arramooz_client)

    def test_oov_detection(self):
        """Test the Out-of-Vocabulary detection."""
        self.assertFalse(
            self.spell_checker.is_oov(
                Token(
                    index=0,
                    form="مدرسة",
                    span=(0, 5),
                    norm_span=(0, 5),
                    affix_structure="STEM",
                )
            )
        )
        self.assertFalse(
            self.spell_checker.is_oov(
                Token(
                    index=0,
                    form="المدرسة",
                    span=(0, 7),
                    norm_span=(0, 7),
                    affix_structure="DET+STEM",
                )
            )
        )
        self.assertTrue(
            self.spell_checker.is_oov(
                Token(
                    index=0,
                    form="المردسة",
                    span=(0, 7),
                    norm_span=(0, 7),
                    affix_structure="DET+STEM",
                )
            )
        )

    def test_candidate_generation(self):
        """Test the spelling candidate generation."""
        candidates = self.spell_checker.generate_candidates(
            Token(
                index=0,
                form="المدشة",
                span=(0, 5),
                norm_span=(0, 5),
                affix_structure="DET+STEM",
            ),
            max_dist=2,
        )
        candidate_forms = [c.form for c in candidates]
        self.assertIn("المدرسة", candidate_forms)

        candidates = self.spell_checker.generate_candidates(
            Token(
                index=0, form="ال", span=(0, 2), norm_span=(0, 2), affix_structure="DET"
            ),
        )
        self.assertEqual(len(candidates), 0)

        candidates = self.spell_checker.generate_candidates(
            Token(
                index=0,
                form="مدرسة",
                span=(0, 5),
                norm_span=(0, 5),
                affix_structure="STEM",
            ),
        )
        self.assertEqual(len(candidates), 0)


if __name__ == "__main__":
    unittest.main()
