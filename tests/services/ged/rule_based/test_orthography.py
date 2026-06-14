"""Tests for GED orthographic rules.

Covers both:
- Python procedural rule: OT_HAMZA_PREP (in orthography.py)
- YAML-loaded rules: OT_ALIF_MAQSURA_PREP, OT_TA_MARBUTA_NOUN (via rule_registry)

Each rule has:
  - True-positive: input that SHOULD be flagged
  - True-negative: correct Arabic that MUST NOT be flagged

Authors:
    Amir Anwar
"""

from __future__ import annotations

import pytest
from src.services.ged.features.subsystems.rule_based.registry import rule_registry
from src.services.ged.schemas import ErrorCategory
from tests.services.ged.rule_based.conftest import make_morph, make_token

_T = make_token
_M = make_morph


# ###########################################################################
# OT_HAMZA_PREP  (Python procedural, orthography.py)
# ###########################################################################


class TestHamzaPrep:
    """OT_HAMZA_PREP: preposition / particle must start with Hamza, not bare Alif."""

    def _run(self, tokens, morphs):
        return rule_registry.run_one(
            "OT_HAMZA_PREP", " ".join(t.form for t in tokens), tokens, morphs
        )

    def test_prep_bare_alif_flagged(self):
        """«الى» (PREP, bare Alif stem) must be flagged."""
        tok = _T("الى", (0, 3), 0)
        morph = _M(0, "PREP", lemma="إلى")
        spans = self._run([tok], [[morph]])
        assert len(spans) == 1
        assert spans[0].span == (0, 3)
        assert spans[0].category == ErrorCategory.ORTHOGRAPHY
        assert spans[0].subtype == "hamza"

    def test_prep_correct_hamza_silent(self):
        """«إلى» (PREP, hamza on stem) must NOT be flagged."""
        tok = _T("إلى", (0, 3), 0)
        morph = _M(0, "PREP", lemma="إلى")
        spans = self._run([tok], [[morph]])
        assert spans == []

    def test_particle_bare_alif_flagged(self):
        """«ان» (PART, bare Alif stem) must be flagged."""
        tok = _T("ان", (0, 2), 0)
        morph = _M(0, "PART", lemma="إن")
        spans = self._run([tok], [[morph]])
        assert len(spans) == 1

    def test_particle_correct_hamza_silent(self):
        """«إن» (PART, hamza) must NOT be flagged."""
        tok = _T("إن", (0, 2), 0)
        morph = _M(0, "PART", lemma="إن")
        spans = self._run([tok], [[morph]])
        assert spans == []

    def test_noun_bare_alif_not_flagged(self):
        """Nouns starting with bare Alif are not handled by this rule."""
        tok = _T("اسم", (0, 3), 0)
        morph = _M(0, "NOUN", lemma="اسم")
        spans = self._run([tok], [[morph]])
        assert spans == []

    def test_no_morph_data_silent(self):
        """Token with no morphological candidates does not crash the rule."""
        tok = _T("ان", (0, 2), 0)
        spans = self._run([tok], [[]])  # empty candidates list
        assert spans == []

    def test_explanation_attached(self):
        """The explanation text must be a non-empty Arabic string."""
        tok = _T("الى", (0, 3), 0)
        morph = _M(0, "PREP", lemma="إلى")
        spans = self._run([tok], [[morph]])
        assert spans[0].explanation_text
        assert spans[0].explanation_eligible is True

    def test_prep_with_clitic_prefix_flagged(self):
        """«والى» (CONJ clitic + bare-Alif PREP stem) must be flagged.

        The affix structure ``CONJ+PREP+STEM`` tells first_significant_char
        to skip one character (و) and inspect the next (ا).
        """
        tok = _T("والى", (0, 4), 0)
        morph = _M(0, "PREP", lemma="إلى", affix_structure="CONJ+PREP+STEM")
        spans = self._run([tok], [[morph]])
        assert len(spans) == 1


# ###########################################################################
# OT_ALIF_MAQSURA_PREP  (YAML rule, rules/orthography.yaml)
# ###########################################################################


class TestAlifMaqsuraPrep:
    """OT_ALIF_MAQSURA_PREP: على / إلى / حتى must end with ى not ي."""

    def _run(self, tokens, morphs):
        return rule_registry.run_one(
            "OT_ALIF_MAQSURA_PREP",
            " ".join(t.form for t in tokens),
            tokens,
            morphs,
        )

    @pytest.mark.parametrize(
        "form,lemma",
        [
            ("علي", "على"),
            ("الي", "إلى"),
            ("حتي", "حتى"),
        ],
    )
    def test_prep_ya_flagged(self, form, lemma):
        """Prep lemma with Ya ending must be flagged."""
        tok = _T(form, (0, len(form)), 0)
        morph = _M(0, "PREP", lemma=lemma)
        spans = self._run([tok], [[morph]])
        assert len(spans) == 1
        assert spans[0].category == ErrorCategory.ORTHOGRAPHY
        assert spans[0].subtype == "alif_maqsura"

    @pytest.mark.parametrize(
        "form,lemma",
        [
            ("على", "على"),
            ("إلى", "إلى"),
            ("حتى", "حتى"),
        ],
    )
    def test_prep_alif_maqsura_silent(self, form, lemma):
        """Correct prep ending with ى must NOT be flagged."""
        tok = _T(form, (0, len(form)), 0)
        morph = _M(0, "PREP", lemma=lemma)
        spans = self._run([tok], [[morph]])
        assert spans == []

    def test_other_prep_silent(self):
        """A prep whose lemma is not in the list is not touched."""
        tok = _T("مني", (0, 3), 0)
        morph = _M(0, "PREP", lemma="من")
        spans = self._run([tok], [[morph]])
        assert spans == []

    def test_non_prep_silent(self):
        """Non-PREP tokens ending with ي are not flagged."""
        tok = _T("علي", (0, 3), 0)
        morph = _M(0, "NOUN", lemma="علي")  # proper noun
        spans = self._run([tok], [[morph]])
        assert spans == []


# ###########################################################################
# OT_TA_MARBUTA_NOUN  (YAML rule, rules/orthography.yaml)
# ###########################################################################


class TestTaMarbutaNoun:
    """OT_TA_MARBUTA_NOUN: feminine NOUN must end with ة not ه."""

    def _run(self, tokens, morphs):
        return rule_registry.run_one(
            "OT_TA_MARBUTA_NOUN",
            " ".join(t.form for t in tokens),
            tokens,
            morphs,
        )

    def test_feminine_noun_ending_ha_flagged(self):
        """«مدرسه» (NOUN, feminine, ends ه) must be flagged."""
        tok = _T("مدرسه", (0, 5), 0)
        morph = _M(0, "NOUN", gender="feminine")
        spans = self._run([tok], [[morph]])
        assert len(spans) == 1
        assert spans[0].category == ErrorCategory.ORTHOGRAPHY
        assert spans[0].subtype == "ta_marbuta"

    def test_feminine_noun_ending_ta_marbuta_silent(self):
        """«مدرسة» (NOUN, feminine, ends ة) must NOT be flagged."""
        tok = _T("مدرسة", (0, 5), 0)
        morph = _M(0, "NOUN", gender="feminine")
        spans = self._run([tok], [[morph]])
        assert spans == []

    def test_masculine_noun_ending_ha_silent(self):
        """«كتابه» (NOUN, masculine, ends ه) is a pronoun suffix , not flagged."""
        tok = _T("كتابه", (0, 5), 0)
        morph = _M(0, "NOUN", gender="masculine")
        spans = self._run([tok], [[morph]])
        assert spans == []

    def test_non_noun_ending_ha_silent(self):
        """Non-NOUN tokens ending with ه are not touched by this rule."""
        tok = _T("يكتبه", (0, 5), 0)
        morph = _M(0, "VERB", gender="feminine")
        spans = self._run([tok], [[morph]])
        assert spans == []
