"""Syntactic agreement procedural rules for the GED rule-based detector.

أخطاء نحوية

For the rules you can check `docs/ged/rules.md`

Authors:
    Amir Anwar
"""

from __future__ import annotations

from src.core.schemas import MorphAnalysis, Token
from src.services.ged.schemas import ErrorCategory, ProvenanceTier

from .registry import rule_registry

# ############################################################################
# Linguistic constants
# ############################################################################

_NON_SINGULAR: frozenset[str] = frozenset({"dual", "plural"})


# ############################################################################
# Rule: SY_VERB_SUBJECT_VSO
# ############################################################################


@rule_registry.register(
    rule_id="SY_VERB_SUBJECT_VSO",
    category=ErrorCategory.SYNTAX,
    subtype="verb_subject_agreement",
    tier=ProvenanceTier.TIER_1_RULE_DERIVED,
    explanation=(
        "إذا تقدَّم الفعل على الفاعل وجب إفراد الفعل وتجريده من علامة "
        "التثنية أو الجمع، مثل: «ذهب الطلاب» لا «ذهبوا الطلاب»"
    ),
)
def check_verb_subject_vso(
    text: str,  # noqa: ARG001
    tokens: list[Token],
    morph_features: list[list[MorphAnalysis]],
) -> list[tuple[int, int, int]]:
    """Detect VSO agreement: verb before subject must be singular.

    Scans every adjacent (VERB, NOUN) pair (allowing punctuation tokens
    in between) and flags the verb if its number is dual or plural.

    Args:
        text: Original input text (unused)
        tokens: Token list from preprocessing.
        morph_features: Per-token morphological candidates

    Returns:
        List of (span_start, span_end, token_index) for each offending token
    """
    hits: list[tuple[int, int, int]] = []
    n = len(tokens)

    for i in range(n - 1):
        verb_morph = morph_features[i][0] if morph_features[i] else None
        if verb_morph is None or verb_morph.pos != "VERB":
            continue
        if verb_morph.number not in _NON_SINGULAR:
            continue

        j = i + 1
        while j < n:
            next_morph = morph_features[j][0] if morph_features[j] else None
            if next_morph is None:
                break
            if next_morph.pos == "PUNC":
                j += 1
                continue
            if next_morph.pos == "NOUN":
                hits.append((tokens[i].span[0], tokens[i].span[1], tokens[i].index))
            break

    return hits


# ############################################################################
# Rule: SY_NOUN_ADJ_DEFINITENESS
# ############################################################################


@rule_registry.register(
    rule_id="SY_NOUN_ADJ_DEFINITENESS",
    category=ErrorCategory.SYNTAX,
    subtype="noun_adjective_agreement",
    tier=ProvenanceTier.TIER_1_RULE_DERIVED,
    explanation=(
        "النعت يتبع المنعوت في التعريف والتنكير؛ "
        "فإن كان الاسم معرفةً وجب تعريف النعت، وإن كان نكرةً وجب تنكيره"
    ),
)
def check_noun_adj_definiteness(
    text: str,  # noqa: ARG001
    tokens: list[Token],
    morph_features: list[list[MorphAnalysis]],
) -> list[tuple[int, int, int]]:
    """Detect noun-adjective definiteness disagreement.

    Scans adjacent (NOUN, ADJ) pairs (skipping punctuation) and flags the
    adjective if its definiteness does not match the noun's.

    Args:
        text: Original input text (unused)
        tokens: Token list from preprocessing
        morph_features: Per-token morphological candidates

    Returns:
        List of (span_start, span_end, token_index) for each offending adj.
    """
    hits: list[tuple[int, int, int]] = []
    n = len(tokens)

    for i in range(n - 1):
        noun_morph = morph_features[i][0] if morph_features[i] else None
        if noun_morph is None or noun_morph.pos != "NOUN":
            continue
        if noun_morph.definiteness is None:
            continue  # Cannot determine definiteness , skip.

        j = i + 1
        while j < n:
            adj_morph = morph_features[j][0] if morph_features[j] else None
            if adj_morph is None:
                break
            if adj_morph.pos == "PUNC":
                j += 1
                continue
            if adj_morph.pos == "ADJ" and adj_morph.definiteness is not None:
                if adj_morph.definiteness != noun_morph.definiteness:
                    hits.append((tokens[j].span[0], tokens[j].span[1], tokens[j].index))
            break

    return hits
