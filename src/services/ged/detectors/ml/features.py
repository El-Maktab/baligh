"""Morphology-aware feature extraction for the GED CRF model."""

from __future__ import annotations

import re
from collections.abc import Sequence

from camel_tools.utils.charsets import AR_CHARSET
from camel_tools.utils.normalize import normalize_alef_ar, normalize_alef_maksura_ar

from src.core.schemas import MorphAnalysis, Token

FEATURE_SET_VERSION = "surface_morph_v2"
PUNCT_RE = re.compile(r"^[^\w\s]+$", re.UNICODE)
MISSING = "__NONE__"
MORPH_FIELDS = (
    "pos",
    "lemma",
    "gender",
    "number",
    "person",
    "definiteness",
    "case",
    "tense",
    "voice",
    "mood",
    "diacritized",
)


def normalize_token(token: str) -> str:
    """Apply the light Arabic normalization used during CRF training."""
    return normalize_alef_maksura_ar(normalize_alef_ar(token))


def token_shape(token: str) -> str:
    """Map token characters to digit, Arabic, or other shape symbols."""
    return "".join(
        "D" if char.isdigit() else "A" if char in AR_CHARSET else "P" for char in token
    )


def _string_feature(value: str | None) -> str:
    """Return a stable placeholder for optional string features."""
    return value if value is not None else MISSING


def _best_analysis(candidates: Sequence[MorphAnalysis]) -> MorphAnalysis | None:
    """Return the disambiguated analysis or the first candidate."""
    if not candidates:
        return None
    return next(
        (candidate for candidate in candidates if candidate.is_disambiguated),
        candidates[0],
    )


def _add_morph_features(
    features: dict[str, object],
    prefix: str,
    analysis: MorphAnalysis | None,
) -> None:
    """Attach morphology fields with a consistent prefix."""
    if analysis is None:
        for field in MORPH_FIELDS:
            features[f"{prefix}_{field}"] = MISSING
        return

    features[f"{prefix}_pos"] = analysis.pos
    features[f"{prefix}_lemma"] = _string_feature(analysis.lemma)
    features[f"{prefix}_gender"] = _string_feature(analysis.gender)
    features[f"{prefix}_number"] = _string_feature(analysis.number)
    features[f"{prefix}_person"] = _string_feature(analysis.person)
    features[f"{prefix}_definiteness"] = _string_feature(analysis.definiteness)
    features[f"{prefix}_case"] = _string_feature(analysis.case)
    features[f"{prefix}_tense"] = _string_feature(analysis.tense)
    features[f"{prefix}_voice"] = _string_feature(analysis.voice)
    features[f"{prefix}_mood"] = _string_feature(analysis.mood)
    features[f"{prefix}_diacritized"] = _string_feature(analysis.diacritized)


def token_features(
    tokens: Sequence[Token],
    morph_features: Sequence[Sequence[MorphAnalysis]],
    index: int,
) -> dict[str, object]:
    """Extract morphology-aware CRF features for one token."""
    token = tokens[index]
    features = _base_token_features(token)
    _add_morph_features(features, "morph", _best_analysis(morph_features[index]))
    _add_affix_features(features, token)

    if index == 0:
        features["BOS"] = True
    else:
        _add_previous_context(features, tokens, morph_features, index)

    if index == len(tokens) - 1:
        features["EOS"] = True
    else:
        _add_next_context(features, tokens, morph_features, index)

    return features


def _base_token_features(token: Token) -> dict[str, object]:
    """Build token-local surface and preprocessing features."""
    return {
        "bias": 1.0,
        "token": token.form,
        "norm": normalize_token(token.form),
        "shape": token_shape(token.form),
        "len": len(token.form),
        "is_digit": token.form.isdigit(),
        "is_punct": bool(PUNCT_RE.match(token.form)),
        "is_arabic": bool(token.form)
        and all(char in AR_CHARSET for char in token.form),
        "affix_structure": _string_feature(token.affix_structure),
        "farasa_segmentation": _string_feature(token.farasa_segmentation),
        "is_oov": token.is_oov,
    }


def _add_affix_features(features: dict[str, object], token: Token) -> None:
    """Attach fixed-width surface prefixes and suffixes."""
    for size in range(1, 5):
        features[f"prefix_{size}"] = token.form[:size]
        features[f"suffix_{size}"] = token.form[-size:]


def _add_previous_context(
    features: dict[str, object],
    tokens: Sequence[Token],
    morph_features: Sequence[Sequence[MorphAnalysis]],
    index: int,
) -> None:
    """Attach one-token left context features."""
    previous = tokens[index - 1]
    features["prev_token"] = previous.form
    features["prev_norm"] = normalize_token(previous.form)
    features["prev_is_punct"] = bool(PUNCT_RE.match(previous.form))
    features["prev_affix_structure"] = _string_feature(previous.affix_structure)
    _add_morph_features(
        features,
        "prev_morph",
        _best_analysis(morph_features[index - 1]),
    )


def _add_next_context(
    features: dict[str, object],
    tokens: Sequence[Token],
    morph_features: Sequence[Sequence[MorphAnalysis]],
    index: int,
) -> None:
    """Attach one-token right context features."""
    following = tokens[index + 1]
    features["next_token"] = following.form
    features["next_norm"] = normalize_token(following.form)
    features["next_is_punct"] = bool(PUNCT_RE.match(following.form))
    features["next_affix_structure"] = _string_feature(following.affix_structure)
    _add_morph_features(
        features,
        "next_morph",
        _best_analysis(morph_features[index + 1]),
    )


def sentence_features(
    tokens: Sequence[Token],
    morph_features: Sequence[Sequence[MorphAnalysis]],
) -> list[dict[str, object]]:
    """Extract morphology-aware features for a tokenized sentence."""
    if len(tokens) != len(morph_features):
        raise ValueError("Token and morphology feature counts do not match.")
    return [
        token_features(tokens, morph_features, index) for index in range(len(tokens))
    ]
