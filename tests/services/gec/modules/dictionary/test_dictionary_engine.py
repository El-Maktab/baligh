"""Unit tests for the DictionaryEngine module."""

import unittest

from src.core.schemas import MorphAnalysis, Token
from src.services.gec.modules.dictionary.engine import DictionaryEngine
from src.services.gec.schemas import GECInput, ModuleName, ModuleResult, ModuleStatus
from src.services.ged.schemas import (
    ErrorCategory,
    ErrorSource,
    ErrorSpan,
    ProvenanceTier,
)


class TestDictionaryEngine(unittest.TestCase):
    """Tests the DictionaryEngine orchestration."""

    def setUp(self):
        """Set up the test environment."""
        self.engine = DictionaryEngine()

    def _make_orth_error(self, token_refs, confidence=0.9):
        return ErrorSpan(
            span=(9, 17),
            token_refs=token_refs,
            category=ErrorCategory.ORTHOGRAPHY,
            subtype="spelling",
            confidence=confidence,
            sources=[ErrorSource.LEXICON_MATCHER],
            provenance_tier=ProvenanceTier.TIER_1_RULE_DERIVED,
            explanation_eligible=True,
            explanation_text="Spelling mistake",
        )

    def test_engine_process_ged_flagged(self):
        """Test that GED-flagged orthography tokens get high confidence."""
        tokens = [
            Token(
                index=0,
                form="ذهبت",
                span=(0, 5),
                norm_span=(0, 5),
                affix_structure="STEM+PRON",
            ),
            Token(
                index=1,
                form="إلى",
                span=(6, 8),
                norm_span=(6, 8),
                affix_structure="STEM",
            ),
            Token(
                index=2,
                form="المردسة",
                span=(9, 16),
                norm_span=(9, 16),
                affix_structure="DET+STEM",
            ),
            Token(
                index=3,
                form="المدشة",
                span=(17, 22),
                norm_span=(17, 22),
                affix_structure="DET+STEM",
            ),
        ]
        error_span = self._make_orth_error(token_refs=[2], confidence=0.85)
        morph = MorphAnalysis(token_index=0, pos="verb")

        input_data = GECInput(
            text="ذهبت الى المردسة المدشة",
            tokens=tokens,
            morph_features=[[morph]],
            errors_span=[error_span],
        )

        result = self.engine.process(input_data)

        self.assertIsInstance(result, ModuleResult)
        self.assertEqual(result.module_name, ModuleName.DICTIONARY)

        # Both OOV tokens (2 and 3) should produce edits
        ged_edits = [e for e in result.candidate_edits if 2 in e.token_refs]
        unflagged_edits = [e for e in result.candidate_edits if 3 in e.token_refs]

        self.assertGreaterEqual(len(ged_edits), 1)
        self.assertGreaterEqual(len(unflagged_edits), 1)

        # GED-flagged token should have confidence >= 0.85
        ged_edit = ged_edits[0]
        self.assertGreaterEqual(ged_edit.edit_confidence, 0.85)

        # Unflagged OOV token should have lower confidence than GED-flagged
        unflagged_edit = unflagged_edits[0]
        self.assertLess(unflagged_edit.edit_confidence, ged_edit.edit_confidence)

    def test_engine_ged_flagged_gets_higher_confidence(self):
        """Test that GED-flagged token gets GED confidence, unflagged gets lower."""
        tokens = [
            Token(
                index=0,
                form="ذهبت",
                span=(0, 5),
                norm_span=(0, 5),
                affix_structure="STEM+PRON",
            ),
            Token(
                index=1,
                form="إلى",
                span=(6, 8),
                norm_span=(6, 8),
                affix_structure="STEM",
            ),
            Token(
                index=2,
                form="المردسة",
                span=(9, 16),
                norm_span=(9, 16),
                affix_structure="DET+STEM",
            ),
            Token(
                index=3,
                form="المدشة",
                span=(17, 22),
                norm_span=(17, 22),
                affix_structure="DET+STEM",
            ),
        ]
        error_span = self._make_orth_error(token_refs=[2], confidence=0.92)
        morph = MorphAnalysis(token_index=0, pos="verb")

        input_data = GECInput(
            text="ذهبت الى المردسة المدشة",
            tokens=tokens,
            morph_features=[[morph]],
            errors_span=[error_span],
        )

        result = self.engine.process(input_data)

        ged_edit = [e for e in result.candidate_edits if 2 in e.token_refs][0]
        self.assertAlmostEqual(ged_edit.edit_confidence, 0.92)

        unflagged_edit = [e for e in result.candidate_edits if 3 in e.token_refs][0]
        self.assertAlmostEqual(unflagged_edit.edit_confidence, 0.5)

    def test_engine_no_edits_returns_correct(self):
        """Test that the module returns CORRECT status when no edits are found."""
        tokens = [
            Token(
                index=0,
                form="ذهبت",
                span=(0, 5),
                norm_span=(0, 5),
                affix_structure="STEM+PRON",
            ),
            Token(
                index=1,
                form="إلى",
                span=(6, 8),
                norm_span=(6, 8),
                affix_structure="STEM",
            ),
        ]
        morph = MorphAnalysis(token_index=0, pos="verb")

        input_data = GECInput(
            text="ذهبت إلى",
            tokens=tokens,
            morph_features=[[morph]],
            errors_span=[],
        )

        result = self.engine.process(input_data)

        self.assertEqual(result.status, ModuleStatus.CORRECT)
        self.assertEqual(len(result.candidate_edits), 0)

    def test_engine_non_orthography_errors_ignored(self):
        """Test that non-orthography GED errors don't trigger dictionary checks."""
        tokens = [
            Token(
                index=0,
                form="الذهاب",
                span=(0, 6),
                norm_span=(0, 6),
                affix_structure="DET+STEM",
            ),
        ]
        morph = MorphAnalysis(token_index=0, pos="verb")
        syntax_error = ErrorSpan(
            span=(0, 6),
            token_refs=[0],
            category=ErrorCategory.SYNTAX,
            subtype="agreement",
            confidence=0.7,
            sources=[ErrorSource.RULE_BASED],
            provenance_tier=ProvenanceTier.TIER_1_RULE_DERIVED,
            explanation_eligible=True,
            explanation_text="Syntax error",
        )

        input_data = GECInput(
            text="الذهاب",
            tokens=tokens,
            morph_features=[[morph]],
            errors_span=[syntax_error],
        )

        result = self.engine.process(input_data)

        self.assertEqual(len(result.candidate_edits), 0)


if __name__ == "__main__":
    unittest.main()
