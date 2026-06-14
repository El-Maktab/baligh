"""Tests for GED syntactic agreement rules.

Covers:
- SY_VERB_SUBJECT_VSO   (Python procedural, syntax.py)
- SY_NOUN_ADJ_DEFINITENESS (Python procedural, syntax.py)

Each rule has true-positive and true-negative test cases.

Authors:
    Amir Anwar
"""

from __future__ import annotations

from src.services.ged.features.subsystems.rule_based.registry import rule_registry
from src.services.ged.schemas import ErrorCategory

from tests.services.ged.rule_based.conftest import make_morph, make_token

_T = make_token
_M = make_morph


def _run(rule_id, tokens, morphs):
    text = " ".join(t.form for t in tokens)
    return rule_registry.run_one(rule_id, text, tokens, morphs)


# ###########################################################################
# SY_VERB_SUBJECT_VSO
# ###########################################################################


class TestVerbSubjectVSO:
    """VSO: verb before a nominal subject must be singular."""

    def test_plural_verb_before_noun_flagged(self):
        """«ذهبوا الطلاب» , plural verb before noun is wrong in VSO."""
        verb = _T("ذهبوا", (0, 5), 0)
        noun = _T("الطلاب", (6, 12), 1)
        v_morph = _M(0, "VERB", number="plural", tense="past")
        n_morph = _M(1, "NOUN", number="plural", definiteness="definite")

        spans = _run("SY_VERB_SUBJECT_VSO", [verb, noun], [[v_morph], [n_morph]])
        assert len(spans) == 1
        assert spans[0].span == (0, 5)  # the verb is flagged
        assert spans[0].category == ErrorCategory.SYNTAX
        assert spans[0].subtype == "verb_subject_agreement"

    def test_dual_verb_before_noun_flagged(self):
        """«ذهبا الطلاب» , dual verb before noun is wrong in VSO."""
        verb = _T("ذهبا", (0, 4), 0)
        noun = _T("الطلاب", (5, 11), 1)
        v_morph = _M(0, "VERB", number="dual", tense="past")
        n_morph = _M(1, "NOUN", number="plural", definiteness="definite")

        spans = _run("SY_VERB_SUBJECT_VSO", [verb, noun], [[v_morph], [n_morph]])
        assert len(spans) == 1
        assert spans[0].span == (0, 4)

    def test_singular_verb_before_noun_silent(self):
        """«ذهب الطلاب» , singular verb before noun is correct VSO."""
        verb = _T("ذهب", (0, 3), 0)
        noun = _T("الطلاب", (4, 10), 1)
        v_morph = _M(0, "VERB", number="singular", tense="past")
        n_morph = _M(1, "NOUN", number="plural", definiteness="definite")

        spans = _run("SY_VERB_SUBJECT_VSO", [verb, noun], [[v_morph], [n_morph]])
        assert spans == []

    def test_verb_before_verb_silent(self):
        """Verb followed by another verb , no subject pair detected."""
        v1 = _T("ذهبوا", (0, 5), 0)
        v2 = _T("يدرسون", (6, 13), 1)
        v1_morph = _M(0, "VERB", number="plural")
        v2_morph = _M(1, "VERB", number="plural")

        spans = _run("SY_VERB_SUBJECT_VSO", [v1, v2], [[v1_morph], [v2_morph]])
        assert spans == []

    def test_punc_between_verb_and_noun_skipped(self):
        """Punctuation between verb and noun is skipped; pair still detected."""
        verb = _T("ذهبوا", (0, 5), 0)
        punc = _T("،", (5, 6), 1)
        noun = _T("الطلاب", (7, 13), 2)
        v_morph = _M(0, "VERB", number="plural")
        p_morph = _M(1, "PUNC")
        n_morph = _M(2, "NOUN", number="plural", definiteness="definite")

        spans = _run(
            "SY_VERB_SUBJECT_VSO",
            [verb, punc, noun],
            [[v_morph], [p_morph], [n_morph]],
        )
        assert len(spans) == 1
        assert spans[0].span == (0, 5)

    def test_empty_tokens_silent(self):
        """An empty token list should produce no syntax spans."""
        spans = _run("SY_VERB_SUBJECT_VSO", [], [])
        assert spans == []


# ###########################################################################
# SY_NOUN_ADJ_DEFINITENESS
# ###########################################################################


class TestNounAdjDefiniteness:
    """Noun-Adjective definiteness agreement."""

    def test_definite_noun_indefinite_adj_flagged(self):
        """«الكتاب مفيدٌ» , definite noun + indefinite adj disagree."""
        noun = _T("الكتاب", (0, 6), 0)
        adj = _T("مفيد", (7, 11), 1)
        n_morph = _M(0, "NOUN", definiteness="definite")
        a_morph = _M(1, "ADJ", definiteness="indefinite")

        spans = _run("SY_NOUN_ADJ_DEFINITENESS", [noun, adj], [[n_morph], [a_morph]])
        assert len(spans) == 1
        assert spans[0].span == (7, 11)  # adjective is flagged
        assert spans[0].category == ErrorCategory.SYNTAX
        assert spans[0].subtype == "noun_adjective_agreement"

    def test_indefinite_noun_definite_adj_flagged(self):
        """«كتابٌ المفيد» , indefinite noun + definite adj disagree."""
        noun = _T("كتاب", (0, 4), 0)
        adj = _T("المفيد", (5, 11), 1)
        n_morph = _M(0, "NOUN", definiteness="indefinite")
        a_morph = _M(1, "ADJ", definiteness="definite")

        spans = _run("SY_NOUN_ADJ_DEFINITENESS", [noun, adj], [[n_morph], [a_morph]])
        assert len(spans) == 1
        assert spans[0].span == (5, 11)

    def test_definite_noun_definite_adj_silent(self):
        """«الكتاب المفيد» , both definite, no error."""
        noun = _T("الكتاب", (0, 6), 0)
        adj = _T("المفيد", (7, 13), 1)
        n_morph = _M(0, "NOUN", definiteness="definite")
        a_morph = _M(1, "ADJ", definiteness="definite")

        spans = _run("SY_NOUN_ADJ_DEFINITENESS", [noun, adj], [[n_morph], [a_morph]])
        assert spans == []

    def test_indefinite_noun_indefinite_adj_silent(self):
        """«كتابٌ مفيدٌ» , both indefinite, no error."""
        noun = _T("كتاب", (0, 4), 0)
        adj = _T("مفيد", (5, 9), 1)
        n_morph = _M(0, "NOUN", definiteness="indefinite")
        a_morph = _M(1, "ADJ", definiteness="indefinite")

        spans = _run("SY_NOUN_ADJ_DEFINITENESS", [noun, adj], [[n_morph], [a_morph]])
        assert spans == []

    def test_noun_no_definiteness_silent(self):
        """Noun without definiteness info is skipped (avoid false positives)."""
        noun = _T("كتاب", (0, 4), 0)
        adj = _T("مفيد", (5, 9), 1)
        n_morph = _M(0, "NOUN", definiteness=None)
        a_morph = _M(1, "ADJ", definiteness="indefinite")

        spans = _run("SY_NOUN_ADJ_DEFINITENESS", [noun, adj], [[n_morph], [a_morph]])
        assert spans == []

    def test_adj_no_definiteness_silent(self):
        """Adjective without definiteness info is skipped."""
        noun = _T("الكتاب", (0, 6), 0)
        adj = _T("مفيد", (7, 11), 1)
        n_morph = _M(0, "NOUN", definiteness="definite")
        a_morph = _M(1, "ADJ", definiteness=None)

        spans = _run("SY_NOUN_ADJ_DEFINITENESS", [noun, adj], [[n_morph], [a_morph]])
        assert spans == []

    def test_punc_between_noun_adj_skipped(self):
        """Punctuation between noun and adjective is skipped correctly."""
        noun = _T("الكتاب", (0, 6), 0)
        punc = _T("،", (6, 7), 1)
        adj = _T("مفيد", (8, 12), 2)
        n_morph = _M(0, "NOUN", definiteness="definite")
        p_morph = _M(1, "PUNC")
        a_morph = _M(2, "ADJ", definiteness="indefinite")

        spans = _run(
            "SY_NOUN_ADJ_DEFINITENESS",
            [noun, punc, adj],
            [[n_morph], [p_morph], [a_morph]],
        )
        assert len(spans) == 1
        assert spans[0].span == (8, 12)
