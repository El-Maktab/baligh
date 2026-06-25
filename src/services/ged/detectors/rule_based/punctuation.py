"""Punctuation procedural rules for the GED rule-based detector.

For the rules check `docs/ged/rules.md`

Authors:
    Amir Anwar
"""

from __future__ import annotations

from src.core.schemas import MorphAnalysis, Token
from src.core.utils.arabic import ALL_PUNCTUATION, is_arabic_word
from src.services.ged.schemas import ErrorCategory, ProvenanceTier

from .registry import rule_registry

# ############################################################################
# Linguistic constants
# ############################################################################

# Characters treated as whitespace before punctuation.
# '\u00a0' (non-breaking space)
_WHITESPACE = frozenset({" ", "\t", "\u00a0", "\n"})


def _has_arabic_neighbor(tokens: list[Token], index: int) -> bool:
    """Return true when adjacent non-punctuation context is Arabic text."""
    for neighbor_index in (index - 1, index + 1):
        if neighbor_index < 0 or neighbor_index >= len(tokens):
            continue
        form = tokens[neighbor_index].form.strip()
        if form and form not in ALL_PUNCTUATION and is_arabic_word(form):
            return True
    return False


# ############################################################################
# Rule: PC_SPACE_BEFORE_PUNC
# ############################################################################


@rule_registry.register(
    rule_id="PC_SPACE_BEFORE_PUNC",
    category=ErrorCategory.PUNCTUATION,
    subtype="spacing",
    tier=ProvenanceTier.TIER_1_RULE_DERIVED,
    explanation=(
        "علامة الترقيم يجب أن تلتصق بالكلمة التي تسبقها دون فراغ؛ "
        "مثل: «ذهب، ثم» لا «ذهب ، ثم»"
    ),
)
def check_space_before_punc(
    text: str,
    tokens: list[Token],
    morph_features: list[list[MorphAnalysis]],
) -> list[tuple[int, int, int]]:
    """Detect whitespace inserted before a punctuation mark.

    For each punctuation token (POS == PUNC or surface form is a known
    punctuation character) checks whether the character immediately before
    its start offset in the original text is whitespace.

    Args:
        text: Original input text , used for span-offset character inspection.
        tokens: Token list from preprocessing.
        morph_features: Per-token morphological candidates

    Returns:
        List of (span_start, span_end, token_index) for each punctuation
        token preceded by whitespace.
    """
    hits: list[tuple[int, int, int]] = []

    for i, token in enumerate(tokens):
        morph = morph_features[i][0] if morph_features[i] else None
        is_punc = (morph is not None and morph.pos == "PUNC") or (
            token.form.strip() in ALL_PUNCTUATION
        )

        if not is_punc:
            continue

        start = token.span[0]
        if start == 0:
            continue  # Nothing before the first token.

        if text[start - 1] in _WHITESPACE:
            hits.append((token.span[0], token.span[1], token.index))

    return hits


def _check_latin_punctuation_variant(
    tokens: list[Token],
    target_char: str,
) -> list[tuple[int, int, int]]:
    """Flag a Latin punctuation mark used inside Arabic context."""
    hits: list[tuple[int, int, int]] = []

    for token in tokens:
        if token.form.strip() != target_char:
            continue
        if not _has_arabic_neighbor(tokens, token.index):
            continue
        hits.append((token.span[0], token.span[1], token.index))

    return hits


@rule_registry.register(
    rule_id="PC_LATIN_COMMA_ARABIC",
    category=ErrorCategory.PUNCTUATION,
    subtype="variant",
    tier=ProvenanceTier.TIER_1_RULE_DERIVED,
    explanation="في السياق العربي تستعمل الفاصلة العربية «،» لا الفاصلة اللاتينية «,».",
)
def check_latin_comma_arabic(
    text: str,  # noqa: ARG001
    tokens: list[Token],
    morph_features: list[list[MorphAnalysis]],  # noqa: ARG001
) -> list[tuple[int, int, int]]:
    """Detect latin comma usage in Arabic text."""
    return _check_latin_punctuation_variant(tokens, ",")


@rule_registry.register(
    rule_id="PC_LATIN_QUESTION_ARABIC",
    category=ErrorCategory.PUNCTUATION,
    subtype="variant",
    tier=ProvenanceTier.TIER_1_RULE_DERIVED,
    explanation=(
        "في السياق العربي تستعمل علامة الاستفهام العربية «؟» لا العلامة اللاتينية «?»."
    ),
)
def check_latin_question_arabic(
    text: str,  # noqa: ARG001
    tokens: list[Token],
    morph_features: list[list[MorphAnalysis]],  # noqa: ARG001
) -> list[tuple[int, int, int]]:
    """Detect latin question mark usage in Arabic text."""
    return _check_latin_punctuation_variant(tokens, "?")


@rule_registry.register(
    rule_id="PC_LATIN_SEMICOLON_ARABIC",
    category=ErrorCategory.PUNCTUATION,
    subtype="variant",
    tier=ProvenanceTier.TIER_1_RULE_DERIVED,
    explanation="في السياق العربي تستعمل الفاصلة المنقوطة العربية «؛» لا «;».",
)
def check_latin_semicolon_arabic(
    text: str,  # noqa: ARG001
    tokens: list[Token],
    morph_features: list[list[MorphAnalysis]],  # noqa: ARG001
) -> list[tuple[int, int, int]]:
    """Detect latin semicolon usage in Arabic text."""
    return _check_latin_punctuation_variant(tokens, ";")
