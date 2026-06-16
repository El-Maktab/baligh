"""Text segmentation service for Baligh preprocessing.

This module uses Farasa's Arabic segmenter to split completed tokens into
their component morphemes (clitics + stem) and produce Token objects with
precise character offsets on both the normalized text and the original raw text.

Design decisions:
    - One Token per whitespace-delimited word or punctuation mark (Design B).
      Farasa's +-split output is used only to derive affix_structure
      stored on the Token. (NOTE: clitics are NOT split into separate tokens)
    - Farasa is run in interactive mode so the JVM stays alive across calls.
      This is appropriate because each request carries a short sentence fragment
      rather than a large document.
    - Token.form is taken from normalized_text (semantically equivalent to the
      original surface).
    - Sequential alignment: Farasa output tokens are matched character-by-
      character against the normalized prefix to derive norm_span, the
      norm_to_orig_map then translates each norm_span into a span on the
      original raw text.

References:
- docs/contracts/preprocessing-contract.md

Authors:
    - Akram Hany
"""

import threading
from typing import TYPE_CHECKING

from src.core.schemas import Token

# Used for type checking only so that the FarasaSegmenter type is defined
if TYPE_CHECKING:
    from farasa.segmenter import FarasaSegmenter

#############################################################################
# Lazy singleton, initialise FARASA once per process.
#############################################################################

_segmenter: "FarasaSegmenter | None" = None
_segmenter_lock = threading.Lock()


# the type FarasaSegmenter is written as strings so that python don't evaluate
# it at runtime (would result in error)
def _get_segmenter() -> "FarasaSegmenter":
    """Returns the shared FarasaSegmenter instance, initialising it if needed.

    Uses double-checked locking so only one thread imports and initializes the object.

    Returns:
        The process-wide FarasaSegmenter running in interactive mode.
    """
    global _segmenter  # to access the module level _segmenter
    if _segmenter is None:
        with _segmenter_lock:
            if _segmenter is None:
                from farasa.segmenter import FarasaSegmenter

                _segmenter = FarasaSegmenter(interactive=True)
    return _segmenter


#############################################################################
# Clitic lookup tables.
# Prefix clitics are listed longest-first so that multi-character clitics
# (ex. "ال") are matched before single-character ones (ex. "ل").
#############################################################################

# Maps clitic string -> tag, ordered longest-first within each group.
_PREFIX_CLITICS: list[tuple[str, str]] = [
    ("ال", "DET"),
    ("و", "CONJ"),
    ("ف", "CONJ"),
    ("ب", "PREP"),
    ("ل", "PREP"),
    ("ك", "PREP"),
]

# Maps clitic string -> tag, ordered longest-first so multi-char suffixes
# are matched before single-char ones.
_SUFFIX_CLITICS: list[tuple[str, str]] = [
    ("ها", "PRON"),
    ("هم", "PRON"),
    ("هن", "PRON"),
    ("كم", "PRON"),
    ("نا", "PRON"),
    ("ه", "PRON"),
    ("ك", "PRON"),
    ("ت", "PRON"),
    ("ي", "PRON"),
]


#############################################################################
# Internal helpers
#############################################################################


def _build_affix_structure(farasa_word: str) -> str | None:
    """Derives the affix_structure tag string from a Farasa word chunk.

    Farasa represents a segmented word as a +-joined string, ex.
    "و+ب+ال+مدرس+ة".  This function takes known prefix clitics from the
    left and known suffix clitics from the right, everything remaining in the
    middle is collapsed into a single STEM tag.

    Punctuation words contain no + and do not match any clitic, so they
    receive None.

    Args:
        farasa_word: A single space-free token from Farasa's output, possibly
            containing + separators (ex. "و+ب+ال+مدرسة").

    Returns:
        A +-joined tag string such as "CONJ+PREP+DET+STEM", or None
        for punctuation and tokens that cannot be parsed into a stem.
    """
    segments: list[str] = farasa_word.split("+")
    tags: list[str] = []

    left = 0
    right = len(segments) - 1

    # take prefix clitics left-to-right.
    while left <= right:
        seg = segments[left]
        matched = False
        for clitic, tag in _PREFIX_CLITICS:
            if seg == clitic:
                tags.append(tag)
                left += 1
                matched = True
                break
        if not matched:
            break

    # take suffix clitics right-to-left.
    suffix_tags: list[str] = []
    while right >= left:
        seg = segments[right]
        matched = False
        for clitic, tag in _SUFFIX_CLITICS:
            if seg == clitic:
                suffix_tags.append(tag)
                right -= 1
                matched = True
                break
        if not matched:
            break

    # everything remaining between left and right (inclusive) is the stem.
    stem_parts = segments[left : right + 1]

    if not stem_parts:
        # entire word was consumed by clitics - no stem found.  this should
        # not happen for valid Arabic text, but we check anyways.
        return None

    # join back the remaining segments as they represent the stem.
    stem_str = "".join(stem_parts)

    # Punctuation check: check if the stem contains at least one Arabic letter.
    # Arabic letters span U+0621-U+064A (basic Arabic alphabet).
    has_arabic_letter = False
    for ch in stem_str:
        if "\u0621" <= ch <= "\u064a":
            has_arabic_letter = True
            break

    # if the stem contains no arabic letters and no clitics were found too,
    # this is a punctuation token, return None.
    if not has_arabic_letter and not tags and not suffix_tags:
        return None

    tags.append("STEM")
    tags.extend(reversed(suffix_tags))
    return "+".join(tags)


def _align_tokens(
    farasa_output: str,
    normalized_prefix: str,
    norm_to_orig_map: list[int],
) -> list[Token]:
    """Aligns Farasa output tokens to character spans in normalized and original text.

    Farasa returns a string where words are separated by single spaces and
    clitics within a word are joined by +.  This function reconstructs the
    surface form of each word (by removing + separators) and then walks
    through normalized_prefix sequentially to find where each word starts
    and ends.

    Args:
        farasa_output: The raw string returned by FarasaSegmenter.segment().
        normalized_prefix: The normalized completed-prefix text that was passed
            to Farasa.
        norm_to_orig_map: Mapping produced by normalize_with_mapping where
            norm_to_orig_map[i] is the index of normalized_prefix[i]
            in the original raw text. The list has one extra sentinel element
            at the end equal to len(original_text).

    Returns:
        A list of Token objects with correct form, span, norm_span,
        and affix_structure.
    """
    tokens: list[Token] = []
    token_index = 0
    norm_cursor = 0  # current position in normalized_prefix

    # Farasa word chunks are space-separated.
    farasa_words = farasa_output.split(" ")

    for farasa_word in farasa_words:
        if not farasa_word:
            continue

        # the surface form is the word with "+" removed.
        surface = farasa_word.replace("+", "")
        surface_len = len(surface)

        # skip whitespace in the normalized text (it would always be one space).
        while (
            norm_cursor < len(normalized_prefix)
            and normalized_prefix[norm_cursor].isspace()
        ):
            norm_cursor += 1

        if norm_cursor >= len(normalized_prefix):
            break

        norm_start = norm_cursor
        norm_end = norm_cursor + surface_len

        # the form is taken directly from the normalized text.
        form = normalized_prefix[norm_start:norm_end]

        # translate norm_span -> orig_span via the mapping.
        orig_start = norm_to_orig_map[norm_start]
        # norm_to_orig_map has len(normalized_prefix)+1 entries, index norm_end
        # gives the original index just past the last character (we have an extra entry
        # in norm_to_orig_map at the end so that if norm_end is after the last element).
        orig_end = norm_to_orig_map[norm_end]

        affix_structure = _build_affix_structure(farasa_word)

        tokens.append(
            Token(
                index=token_index,
                form=form,
                span=(orig_start, orig_end),
                norm_span=(norm_start, norm_end),
                affix_structure=affix_structure,
            )
        )

        token_index += 1
        norm_cursor = norm_end

    return tokens


#############################################################################
# Public API
#############################################################################

_PREFIX_TAG_TO_CLITICS: dict[str, list[str]] = {}
for clitic, tag in _PREFIX_CLITICS:
    _PREFIX_TAG_TO_CLITICS.setdefault(tag, []).append(clitic)

_SUFFIX_TAG_TO_CLITICS: dict[str, list[str]] = {}
for clitic, tag in _SUFFIX_CLITICS:
    _SUFFIX_TAG_TO_CLITICS.setdefault(tag, []).append(clitic)


def break_token(token: Token) -> list[tuple[str, str]] | None:
    """Reconstructs the clitic/stem breakdown for a token from its affix_structure.

    use the affix_structure to break the token to it's segmented parts.

    Args:
        token: A Token produced by the segmentation stage.

    Returns:
        A list of (tag, substring) pairs in left-to-right order, where each
        pair contains a component label (ex. CONJ, DET, STEM, PRON) and the
        corresponding part from token.form. Returns None when
        affix_structure is None.
    """
    if token.affix_structure is None:
        return None

    tags = token.affix_structure.split("+")
    form = token.form

    # We are sure that STEM must exist if affix_structure is not none
    stem_idx = tags.index("STEM")       
    prefix_tags = tags[:stem_idx]
    suffix_tags = tags[stem_idx + 1:]

    components: list[tuple[str, str]] = []
    left = 0
    right = len(form)

    for tag in prefix_tags:
        matched = False
        for clitic in _PREFIX_TAG_TO_CLITICS.get(tag, []):
            if form[left:].startswith(clitic):
                components.append((tag, clitic))
                left += len(clitic)
                matched = True
                break
        if not matched:
            return None

    suffix_components: list[tuple[str, str]] = []
    for tag in reversed(suffix_tags):
        matched = False
        for clitic in _SUFFIX_TAG_TO_CLITICS.get(tag, []):
            if form[:right].endswith(clitic):
                suffix_components.append((tag, clitic))
                right -= len(clitic)
                matched = True
                break
        if not matched:
            return None

    components.append(("STEM", form[left:right]))
    components.extend(reversed(suffix_components))

    return components


def segment(completed_prefix: str, norm_to_orig_map: list[int]) -> list[Token]:
    """Segments the completed prefix into tokens using Farasa.

    Runs Farasa on the normalized completed_prefix, derives
    affix_structure for each token from the +-split output, and aligns
    each token to its character offsets in both the normalized text and the
    original raw text.

    Args:
        completed_prefix: The normalized text of the completed portion of the
            user's input (everything before the current fragment), as returned
            by the boundary detector. Must be normalized.

        norm_to_orig_map: The character index mapping produced by
            normalize_with_mapping, where norm_to_orig_map[i] is the
            index of completed_prefix[i] in the original raw text.

    Returns:
        A list of Token objects ordered by their position in the text. Returns
        an empty list when completed_prefix is empty or contains only
        whitespace.
    """
    if not completed_prefix.strip():
        return []

    seg = _get_segmenter()
    farasa_output: str = seg.segment(completed_prefix)

    return _align_tokens(farasa_output, completed_prefix, norm_to_orig_map)
