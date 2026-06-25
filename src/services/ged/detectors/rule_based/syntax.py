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
_NOUN_LIKE_POS: frozenset[str] = frozenset({"NOUN", "NOUN_PROP"})
_DEMONSTRATIVE_GENDER: dict[str, str] = {
    "هذا": "masculine",
    "هذه": "feminine",
    "ذلك": "masculine",
    "تلك": "feminine",
}
_RELATIVE_PRONOUN_GENDER: dict[str, str] = {
    "الذي": "masculine",
    "التي": "feminine",
}


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


# ############################################################################
# Rule: SY_DEMONSTRATIVE_NOUN_GENDER
# ############################################################################


@rule_registry.register(
    rule_id="SY_DEMONSTRATIVE_NOUN_GENDER",
    category=ErrorCategory.SYNTAX,
    subtype="demonstrative_noun_gender",
    tier=ProvenanceTier.TIER_1_RULE_DERIVED,
    explanation=(
        "اسم الإشارة يجب أن يطابق الاسم الذي بعده في التذكير والتأنيث؛ "
        "فنقول: «هذه السلامة» و«هذا البطل»"
    ),
)
def check_demonstrative_noun_gender(
    text: str,  # noqa: ARG001
    tokens: list[Token],
    morph_features: list[list[MorphAnalysis]],
) -> list[tuple[int, int, int]]:
    """Detect singular demonstrative + noun gender disagreement."""
    hits: list[tuple[int, int, int]] = []

    for i in range(len(tokens) - 1):
        expected_gender = _DEMONSTRATIVE_GENDER.get(tokens[i].form)
        if expected_gender is None:
            continue

        noun_morph = morph_features[i + 1][0] if morph_features[i + 1] else None
        if noun_morph is None or noun_morph.pos not in _NOUN_LIKE_POS:
            continue
        if noun_morph.gender is None:
            continue
        if noun_morph.gender != expected_gender:
            hits.append((tokens[i].span[0], tokens[i].span[1], tokens[i].index))

    return hits


# ############################################################################
# Rule: SY_RELATIVE_PRONOUN_GENDER
# ############################################################################


@rule_registry.register(
    rule_id="SY_RELATIVE_PRONOUN_GENDER",
    category=ErrorCategory.SYNTAX,
    subtype="relative_pronoun_gender",
    tier=ProvenanceTier.TIER_1_RULE_DERIVED,
    explanation=(
        "الاسم الموصول يجب أن يطابق الاسم السابق له في التذكير والتأنيث؛ "
        "فنقول: «القول الذي» و«الوشاية التي»"
    ),
)
def check_relative_pronoun_gender(
    text: str,  # noqa: ARG001
    tokens: list[Token],
    morph_features: list[list[MorphAnalysis]],
) -> list[tuple[int, int, int]]:
    """Detect noun + relative pronoun gender disagreement."""
    hits: list[tuple[int, int, int]] = []

    for i in range(len(tokens) - 1):
        noun_morph = morph_features[i][0] if morph_features[i] else None
        if noun_morph is None or noun_morph.pos not in _NOUN_LIKE_POS:
            continue
        if noun_morph.gender is None:
            continue

        rel_gender = _RELATIVE_PRONOUN_GENDER.get(tokens[i + 1].form)
        if rel_gender is None:
            continue
        if noun_morph.gender != rel_gender:
            hits.append(
                (tokens[i + 1].span[0], tokens[i + 1].span[1], tokens[i + 1].index)
            )

    return hits


# ############################################################################
# Rule: SY_PREP_DUAL_CASE
# ############################################################################


@rule_registry.register(
    rule_id="SY_PREP_DUAL_CASE",
    category=ErrorCategory.SYNTAX,
    subtype="preposition_dual_case",
    tier=ProvenanceTier.TIER_1_RULE_DERIVED,
    explanation=(
        "الاسم المثنى بعد حرف الجر يجب أن يكون مجرورًا؛ "
        "فنقول: «في الكتابين» لا «في الكتابان»"
    ),
)
def check_prep_dual_case(
    text: str,  # noqa: ARG001
    tokens: list[Token],
    morph_features: list[list[MorphAnalysis]],
) -> list[tuple[int, int, int]]:
    """Detect nominative dual nouns after standalone prepositions."""
    hits: list[tuple[int, int, int]] = []

    for i in range(len(tokens) - 1):
        prep_morph = morph_features[i][0] if morph_features[i] else None
        if prep_morph is None or prep_morph.pos != "PREP":
            continue

        noun_morph = morph_features[i + 1][0] if morph_features[i + 1] else None
        if noun_morph is None or noun_morph.pos != "NOUN":
            continue
        if noun_morph.number == "dual" and noun_morph.case == "nominative":
            hits.append(
                (tokens[i + 1].span[0], tokens[i + 1].span[1], tokens[i + 1].index)
            )

    return hits


# ############################################################################
# Rule: SY_PREP_SOUND_MASC_PLURAL_CASE
# ############################################################################


@rule_registry.register(
    rule_id="SY_PREP_SOUND_MASC_PLURAL_CASE",
    category=ErrorCategory.SYNTAX,
    subtype="preposition_sound_masc_plural_case",
    tier=ProvenanceTier.TIER_1_RULE_DERIVED,
    explanation=(
        "جمع المذكر السالم بعد حرف الجر يجب أن يكون مجرورًا؛ "
        "فنقول: «مع المسافرين» لا «مع المسافرون»"
    ),
)
def check_prep_sound_masc_plural_case(
    text: str,  # noqa: ARG001
    tokens: list[Token],
    morph_features: list[list[MorphAnalysis]],
) -> list[tuple[int, int, int]]:
    """Detect nominative sound masculine plural nouns after prepositions."""
    hits: list[tuple[int, int, int]] = []

    for i in range(len(tokens) - 1):
        prep_morph = morph_features[i][0] if morph_features[i] else None
        if prep_morph is None or prep_morph.pos != "PREP":
            continue

        noun_morph = morph_features[i + 1][0] if morph_features[i + 1] else None
        if noun_morph is None or noun_morph.pos != "NOUN":
            continue
        if (
            noun_morph.gender == "masculine"
            and noun_morph.number == "plural"
            and noun_morph.case == "nominative"
        ):
            hits.append(
                (tokens[i + 1].span[0], tokens[i + 1].span[1], tokens[i + 1].index)
            )

    return hits
