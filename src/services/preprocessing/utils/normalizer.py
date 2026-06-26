"""Text normalization service for Baligh.

Does a normalization using Unicode NFKC (Normalization
Form Compatibility Composition) and whitespace consolidation.
It also maintains a mapping from normalized text to original one.

References:
- docs/contracts/preprocessing-contract.md

Authors:
    - Akram Hany
"""

import unicodedata


def normalize_text(text: str) -> str:
    """Performs Unicode NFKC normalization and whitespace consolidation on text.

    Args:
        text: The raw input text.

    Returns:
        The normalized string representation of the text.
    """
    normalized, _ = normalize_with_mapping(text)
    return normalized


def normalize_with_mapping(text: str) -> tuple[str, list[int]]:
    """Normalizes text and computes a character index mapping back to original text.

    Args:
        text: The raw input text.

    Returns:
        A tuple of (normalized_text, norm_to_orig_map) where norm_to_orig_map[i]
        is the character index of normalized_text[i] in the original text.
        The map contains one extra element at the end mapping to len(text).
    """
    if not text:
        return "", [0]

    # step 1: Unicode NFKC character-by-character normalization
    nfkc_chars: list[str] = []
    nfkc_to_orig: list[int] = []
    for orig_idx, char in enumerate(text):
        n_char = unicodedata.normalize("NFKC", char)
        for sub_char in n_char:
            nfkc_chars.append(sub_char)
            nfkc_to_orig.append(orig_idx)

    nfkc_text = "".join(nfkc_chars)

    # step 2: Whitespace consolidation and final mapping
    final_chars: list[str] = []
    final_to_orig: list[int] = []
    in_whitespace = False

    for idx, char in enumerate(nfkc_text):
        orig_idx = nfkc_to_orig[idx]
        if char.isspace():
            if not in_whitespace:
                final_chars.append(" ")
                final_to_orig.append(orig_idx)
                in_whitespace = True
        else:
            final_chars.append(char)
            final_to_orig.append(orig_idx)
            in_whitespace = False

    normalized_text = "".join(final_chars)
    final_to_orig.append(len(text))

    return normalized_text, final_to_orig