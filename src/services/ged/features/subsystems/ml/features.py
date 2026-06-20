"""Surface feature extraction for the GED CRF model."""

from __future__ import annotations

import re
from collections.abc import Sequence

from camel_tools.utils.charsets import AR_CHARSET
from camel_tools.utils.normalize import normalize_alef_ar, normalize_alef_maksura_ar

FEATURE_SET_VERSION = "surface_v1"
PUNCT_RE = re.compile(r"^[^\w\s]+$", re.UNICODE)


def normalize_token(token: str) -> str:
    """Apply the light Arabic normalization used during CRF training."""
    return normalize_alef_maksura_ar(normalize_alef_ar(token))


def token_shape(token: str) -> str:
    """Map token characters to digit, Arabic, or other shape symbols."""
    return "".join(
        "D" if char.isdigit() else "A" if char in AR_CHARSET else "P" for char in token
    )


def surface_v1_token_features(tokens: Sequence[str], index: int) -> dict[str, object]:
    """Extract the notebook's surface_v1 features for one token."""
    token = tokens[index]
    token_norm = normalize_token(token)

    features: dict[str, object] = {
        "bias": 1.0,
        "token": token,
        "norm": token_norm,
        "shape": token_shape(token),
        "len": len(token),
        "is_digit": token.isdigit(),
        "is_punct": bool(PUNCT_RE.match(token)),
        "is_arabic": bool(token) and all(char in AR_CHARSET for char in token),
    }

    for size in range(1, 5):
        features[f"prefix_{size}"] = token[:size]
        features[f"suffix_{size}"] = token[-size:]

    if index == 0:
        features["BOS"] = True
    else:
        previous = tokens[index - 1]
        features["prev_token"] = previous
        features["prev_norm"] = normalize_token(previous)
        features["prev_is_punct"] = bool(PUNCT_RE.match(previous))

    if index == len(tokens) - 1:
        features["EOS"] = True
    else:
        following = tokens[index + 1]
        features["next_token"] = following
        features["next_norm"] = normalize_token(following)
        features["next_is_punct"] = bool(PUNCT_RE.match(following))

    return features


def sentence_surface_v1_features(tokens: Sequence[str]) -> list[dict[str, object]]:
    """Extract surface_v1 features for a tokenized sentence."""
    return [surface_v1_token_features(tokens, index) for index in range(len(tokens))]
