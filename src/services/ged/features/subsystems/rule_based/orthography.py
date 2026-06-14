"""Orthographic procedural rules for the GED rule-based detector.

قواعد إملائية

For the ruels you can check `docs/ged/rules.md`

Authors:
    Amir Anwar
"""

from __future__ import annotations

from src.core.schemas import MorphAnalysis, Token
from src.core.utils.arabic import BARE_ALIF, HAMZA_REQUIRED_POS, first_significant_char
from src.services.ged.schemas import ErrorCategory, ProvenanceTier

from .registry import rule_registry

# ############################################################################
# Rule: OT_HAMZA_PREP
# ############################################################################


@rule_registry.register(
    rule_id="OT_HAMZA_PREP",
    category=ErrorCategory.ORTHOGRAPHY,
    subtype="hamza",
    tier=ProvenanceTier.TIER_1_RULE_DERIVED,
    explanation=(
        "حرف الجر أو الربط يبدأ بهمزة قطع (إ/أ) لا بألف مجردة (ا)؛ "
        "مثل: إلى، إن، أن , لا: الى، ان، ان"
    ),
)
def check_hamza_prep(
    text: str,  # noqa: ARG001
    tokens: list[Token],
    morph_features: list[list[MorphAnalysis]],
) -> list[tuple[int, int, int]]:
    """Detect prepositions/particles starting with bare Alif instead of Hamza.

    Args:
        text: Original input text (unused)
        tokens: Token list from preprocessing.
        morph_features: Per-token morphological candidates

    Returns:
        List of (span_start, span_end, token_index) for every offending token.
    """
    hits: list[tuple[int, int, int]] = []

    for i, token in enumerate(tokens):
        candidates = morph_features[i]
        if not candidates:
            continue

        morph = candidates[0]  # disambiguated candidate
        if morph.pos not in HAMZA_REQUIRED_POS:
            continue

        stem_first = first_significant_char(token.form, morph.affix_structure)
        if stem_first == BARE_ALIF:
            hits.append((token.span[0], token.span[1], token.index))

    return hits
