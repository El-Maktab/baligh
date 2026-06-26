"""Word boundary detection service for Baligh.

This module determines whether the user is in Next Word Prediction (NWP) mode
or Word Autocomplete (WAC) mode, splitting the text into a completed prefix
and an optional active word fragment.

Note:
    cursor_offset is not supported for now.

References:
- docs/contracts/preprocessing-contract.md

Authors:
    - Akram Hany
"""

from typing import Literal

# - whitespace (space, tab, newline, etc...)
# - arabic punctuation: ، ؟ ؛
# - shared punctuation: . , ! ? ; : " ' ( ) [ ] { } - —
DELIMITERS = set(" \t\n\r\v\f" + "،؟؛" + ".,!?;:\"'()[]{}—-")


def split_word_boundary(
    text: str, cursor_offset: int | None = None
) -> tuple[str, str | None, Literal["NWP", "WAC"]]:
    """Splits input text into a completed prefix, an active fragment, and a mode.

    determines if the word being written is complete (NWP mode) or incomplete
    (WAC mode).

    Args:
        text: The raw or normalized input text.
        cursor_offset: NOT SUPP for now.

    Returns:
        A tuple of (completed_prefix, current_fragment, mode) where:
            - completed_prefix (str): Text containing all complete words.
            - current_fragment (str | None): The active incomplete word fragment.
            - mode (str): "WAC" (Word Autocomplete) or "NWP" (Next Word Prediction).

    Raises:
        NotImplementedError: If cursor_offset is not None.
    """
    if cursor_offset is not None:
        raise NotImplementedError("cursor_offset support is not yet implemented. ")

    left_text = text

    # NWP
    if not left_text:
        return "", None, "NWP"

    last_char = left_text[-1]
    if last_char in DELIMITERS:
        return left_text, None, "NWP"

    # WAC
    last_delimiter_idx = -1
    for idx in range(len(left_text) - 1, -1, -1):
        if left_text[idx] in DELIMITERS:
            last_delimiter_idx = idx
            break

    if last_delimiter_idx != -1:
        completed_prefix = left_text[: last_delimiter_idx + 1]
        current_fragment = left_text[last_delimiter_idx + 1 :]
    else:
        completed_prefix = ""
        current_fragment = left_text

    return completed_prefix, current_fragment, "WAC"
