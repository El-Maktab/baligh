"""Tests for GED punctuation rules.

Covers:
- PC_SPACE_BEFORE_PUNC (Python procedural, punctuation.py)
- Latin punctuation variants in Arabic context

Authors:
    Amir Anwar
"""

from __future__ import annotations

import pytest
from src.services.ged.detectors.rule_based.registry import rule_registry
from src.services.ged.schemas import ErrorCategory

from tests.services.ged.rule_based.conftest import make_morph, make_token

_T = make_token
_M = make_morph

_RULE = "PC_SPACE_BEFORE_PUNC"


def _run(text, tokens, morphs):
    return rule_registry.run_one(_RULE, text, tokens, morphs)


# ###########################################################################
# PC_SPACE_BEFORE_PUNC
# ###########################################################################


class TestSpaceBeforePunc:
    """Arabic and Latin punctuation must not be preceded by whitespace."""

    @pytest.mark.parametrize(
        "char,text,word_end,punc_span",
        [
            # word chars + space + punc: offsets are Python codepoint indices
            ("،", "ذهب ،", 3, (4, 5)),  # ذ=0 ه=1 ب=2 ' '=3 ،=4
            ("؟", "ما هو ؟", 5, (6, 7)),  # م=0 ا=1 ' '=2 ه=3 و=4 ' '=5 ؟=6
            ("؛", "قرأ ؛", 3, (4, 5)),  # ق=0 ر=1 أ=2 ' '=3 ؛=4
            (".", "كتب .", 3, (4, 5)),  # ك=0 ت=1 ب=2 ' '=3 .=4
            ("!", "أحسنت !", 5, (6, 7)),  # أ=0 ح=1 س=2 ن=3 ت=4 ' '=5 !=6
        ],
    )
    def test_space_before_punc_flagged(self, char, text, word_end, punc_span):
        """Whitespace before any punctuation mark must be flagged."""
        word_form = text[:word_end]
        word = _T(word_form, (0, word_end), 0)
        punc = _T(char, punc_span, 1)
        w_morph = _M(0, "VERB")
        p_morph = _M(1, "PUNC")

        spans = _run(text, [word, punc], [[w_morph], [p_morph]])
        assert len(spans) == 1
        assert spans[0].span == punc_span
        assert spans[0].category == ErrorCategory.PUNCTUATION
        assert spans[0].subtype == "spacing"

    @pytest.mark.parametrize(
        "char,text,word_span,punc_span",
        [
            ("،", "ذهب،", (0, 3), (3, 4)),
            ("؟", "ماذا؟", (0, 4), (4, 5)),
            (".", "كتب.", (0, 3), (3, 4)),
        ],
    )
    def test_no_space_before_punc_silent(self, char, text, word_span, punc_span):
        """Punctuation immediately after a word must NOT be flagged."""
        word = _T(text[word_span[0] : word_span[1]], word_span, 0)
        punc = _T(char, punc_span, 1)
        w_morph = _M(0, "VERB")
        p_morph = _M(1, "PUNC")

        spans = _run(text, [word, punc], [[w_morph], [p_morph]])
        assert spans == []

    def test_punc_at_start_of_text_silent(self):
        """Punctuation at position 0 must never be flagged (no preceding char)."""
        punc = _T("،", (0, 1), 0)
        p_morph = _M(0, "PUNC")
        spans = _run("،", [punc], [[p_morph]])
        assert spans == []

    def test_non_punc_token_silent(self):
        """Non-punctuation tokens are never flagged by this rule."""
        tok = _T("ذهب", (0, 3), 0)
        morph = _M(0, "VERB")
        spans = _run("ذهب", [tok], [[morph]])
        assert spans == []

    def test_punc_detected_by_form_when_no_morph(self):
        """Punctuation identified by form (not POS) when morph list is empty."""
        word = _T("كتب", (0, 3), 0)
        punc = _T(".", (4, 5), 1)
        w_morph = _M(0, "NOUN")

        # Pass empty candidates for the punctuation token
        spans = _run("كتب .", [word, punc], [[w_morph], []])
        assert len(spans) == 1
        assert spans[0].span == (4, 5)

    def test_explanation_attached(self):
        """The rule must attach a non-empty Arabic explanation."""
        word = _T("ذهب", (0, 3), 0)
        punc = _T("،", (4, 5), 1)
        spans = _run("ذهب ،", [word, punc], [[_M(0, "VERB")], [_M(1, "PUNC")]])
        assert spans[0].explanation_text
        assert spans[0].explanation_eligible is True


@pytest.mark.parametrize(
    ("rule_id", "mark", "left", "right", "span"),
    [
        ("PC_LATIN_COMMA_ARABIC", ",", "قال", "ثم", (4, 5)),
        ("PC_LATIN_QUESTION_ARABIC", "?", "هذا", "", (4, 5)),
        ("PC_LATIN_SEMICOLON_ARABIC", ";", "قال", "ثم", (4, 5)),
    ],
)
def test_latin_punctuation_variant_flagged(rule_id, mark, left, right, span):
    """Latin punctuation marks should be flagged in Arabic context."""
    text = f"{left} {mark}" + (f" {right}" if right else "")
    tokens = [
        _T(left, (0, len(left)), 0),
        _T(mark, (len(left) + 1, len(left) + 2), 1),
    ]
    morphs = [[_M(0, "VERB")], [_M(1, "PUNC")]]

    if right:
        tokens.append(_T(right, (len(left) + 3, len(text)), 2))
        morphs.append([_M(2, "CONJ")])

    spans = rule_registry.run_one(rule_id, text, tokens, morphs)

    assert len(spans) == 1
    assert spans[0].span == span
    assert spans[0].category == ErrorCategory.PUNCTUATION
    assert spans[0].subtype == "variant"


@pytest.mark.parametrize(
    "rule_id,mark",
    [
        ("PC_LATIN_COMMA_ARABIC", ","),
        ("PC_LATIN_QUESTION_ARABIC", "?"),
        ("PC_LATIN_SEMICOLON_ARABIC", ";"),
    ],
)
def test_latin_punctuation_variant_requires_arabic_context(rule_id, mark):
    """The variant rules stay silent when adjacent text is not Arabic."""
    text = f"item {mark} next"
    tokens = [
        _T("item", (0, 4), 0),
        _T(mark, (5, 6), 1),
        _T("next", (7, 11), 2),
    ]
    morphs = [[_M(0, "NOUN")], [_M(1, "PUNC")], [_M(2, "NOUN")]]

    spans = rule_registry.run_one(rule_id, text, tokens, morphs)

    assert spans == []
