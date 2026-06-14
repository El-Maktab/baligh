"""Punctuation procedural rules for the GED rule-based detector.

For the rules check `docs/ged/rules.md`

Authors:
    Amir Anwar
"""

from __future__ import annotations

from src.core.schemas import MorphAnalysis, Token
from src.core.utils.arabic import ALL_PUNCTUATION
from src.services.ged.schemas import ErrorCategory, ProvenanceTier

from .registry import rule_registry

# ############################################################################
# Linguistic constants
# ############################################################################

# Characters treated as whitespace before punctuation.
# '\u00a0' (non-breaking space)
_WHITESPACE = frozenset({" ", "\t", "\u00a0", "\n"})


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
