"""Text normalization service for Baligh.

This module provides utilities to normalize Arabic text (Unicode NFKC (Normalization Form 
Compatibility Composition) and whitespace consolidation) while maintaining a mapping of
character indices back to the original raw text.

Note:
    The canonicalize_* utilities (canonicalize_alif, canonicalize_ya,
    canonicalize_ta_marbuta) are intentionally NOT applied during main text
    normalization. The reason is becuase they will hide errors in the words, where some modules
    like the GED and GEC, would need the text as it is unmodified, so these features should only
    be used in the NWS module.

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

    Consolidates multiple consecutive spaces into a single space, applies NFKC 
    Unicode normalization, and maps each character in the resulting normalized 
    string to its corresponding index in the original string.

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

    # Loop over the nfkc_text, only take one whitespace between each 2 chars and append it's orig index to final_to_orig
    # else ignore any in between whitespaces.
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


def canonicalize_alif(text: str) -> str:
    """Canonicalizes Alif variants to plain Alif.

    This function must ONLY be applied to the current_fragment (the incomplete
    word being typed). It would help the NWS module to predict the next word.

    Warning:
        Never apply this to the completed prefix or normalized_text.

    Args:
        text: The incomplete word fragment being typed by the user.

    Returns:
        The incomplet word with normlaized Alif values.
    """
    alif_map = {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
    }
    return "".join(alif_map.get(char, char) for char in text)


def canonicalize_ya(text: str) -> str:
    """Canonicalizes Alif Maqsura (ى) to Ya (ي).

    This function must ONLY be applied to the current_fragment (the incomplete
    word being typed). It helps the NWS module in the predictions it make.

    Warning:
        Never apply this to the completed prefix or normalized_text.

    Args:
        text: The incomplete word fragment being typed by the user.

    Returns:
        The fragment with Alif Maqsura (ى) replaced by Ya (ي).
    """
    return text.replace("\u0649", "\u064a")


def canonicalize_ta_marbuta(text: str) -> str:
    """Canonicalizes Ta Marbuta (ة) to Ha (ه).

    This function must ONLY be applied to the current_fragment (the incomplete
    word being typed). It would help the NWS module to predict the next word.

    Warning:
        Never apply this to the completed prefix or normalized_text.

    Args:
        text: The incomplete word fragment being typed by the user.

    Returns:
        The fragment with Ta Marbuta (ة) replaced by Ha (ه).
    """
    return text.replace("\u0629", "\u0647")
