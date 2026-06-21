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

import difflib
import re
import threading
from typing import TYPE_CHECKING

from src.core.schemas import Token
from src.core.utils.arabic import PREFIX_CLITICS, SUFFIX_CLITICS

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
        for clitic, tag in PREFIX_CLITICS:
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
        for clitic, tag in SUFFIX_CLITICS:
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


def _canonicalize_for_alignment(text: str) -> str:
    """Removes or normalizes characters that Farasa implicitly corrects.

    Used for the SequenceMatcher can perfectly align characters regardless of
    Farasa's internal changes (ex. converting 'اكرم' to 'أكرم').
    """
    text = re.sub(r"[أإآ]", "ا", text)      # TODO: cover more alif variations
    text = text.replace("ة", "ه").replace("ى", "ي")
    return text


def _build_character_mapping(farasa_clean: str, normalized_prefix: str) -> dict[int, int]:
    """Builds a character index map between Farasa output and normalized text."""
    clean_canon = _canonicalize_for_alignment(farasa_clean)
    norm_canon = _canonicalize_for_alignment(normalized_prefix)

    matcher = difflib.SequenceMatcher(None, clean_canon, norm_canon)
    clean_to_norm: dict[int, int] = {}
    for match in matcher.get_matching_blocks():
        for i in range(match.size):
            clean_to_norm[match.a + i] = match.b + i
            
    return clean_to_norm


def _get_farasa_spans(farasa_words: list[str], clean_to_norm: dict[int, int]) -> list[dict]:
    """Calculates mapped boundaries for each Farasa word."""
    clean_cursor = 0
    spans = []
    
    for farasa_word in farasa_words:
        fword_clean = farasa_word.replace("+", "")
        start_clean = clean_cursor
        end_clean = clean_cursor + len(fword_clean)

        mapped_indices = [
            clean_to_norm[i] for i in range(start_clean, end_clean) if i in clean_to_norm
        ]

        if mapped_indices:
            norm_start = min(mapped_indices)
            norm_end = max(mapped_indices) + 1
        else:
            norm_start = -1
            norm_end = -1

        spans.append({
            "word": farasa_word,
            "norm_start": norm_start,
            "norm_end": norm_end,
            "start_clean": start_clean,
        })
        clean_cursor = end_clean + 1  # +1 for the space

    return spans


def _reconstruct_farasa_segmentation(
    grouped_farasa: list[dict],
    clean_to_norm: dict[int, int],
    normalized_prefix: str,
    form: str,
) -> tuple[str, str | None]:
    """Reconstructs farasa_segmentation using exact user characters."""
    if not grouped_farasa:
        return form, None

    recon_parts = []
    for fw in grouped_farasa:
        recon = []
        clean_idx = fw["start_clean"]
        for char in fw["word"]:
            if char == "+":
                recon.append("+")
            else:
                if clean_idx in clean_to_norm:
                    recon.append(normalized_prefix[clean_to_norm[clean_idx]])
                else:
                    recon.append(char)
                clean_idx += 1
        recon_parts.append("".join(recon))
        
    farasa_seg = " ".join(recon_parts)
    
    if len(grouped_farasa) == 1:
        affix_structure = _build_affix_structure(farasa_seg)
    else:
        affix_structure = None
        
    return farasa_seg, affix_structure


def _align_tokens(
    farasa_output: str,
    normalized_prefix: str,
    norm_to_orig_map: list[int],
    regex_matches: list[re.Match],
) -> list[Token]:
    """Aligns Farasa output tokens to regex-extracted token spans.

    Maps character indices from Farasa's cleaned output back to the
    normalized_prefix to bypass inserted/dropped characters. It reconstructs
    the farasa_segmentation string by fetching exact user characters, which
    perserve spelling errors that Farasa silently corrected.

    Args:
        farasa_output: The raw string returned by FarasaSegmenter.segment().
        normalized_prefix: The original normalized text.
        norm_to_orig_map: Character index mapping from normalized to raw text.
        regex_matches: Pre-computed token boundaries via regex.

    Returns:
        A list of Token objects representing exactly the regex matches, populated
        with the corresponding Farasa affix structure and segmentation.
    """
    tokens: list[Token] = []
    token_index = 0

    farasa_words = farasa_output.split(" ")
    farasa_clean = farasa_output.replace("+", "")

    clean_to_norm = _build_character_mapping(farasa_clean, normalized_prefix)
    farasa_word_spans = _get_farasa_spans(farasa_words, clean_to_norm)

    # Group Farasa words into the rigid regex matches
    for match in regex_matches:
        match_start, match_end = match.span()
        form = normalized_prefix[match_start:match_end]

        grouped_farasa = []
        for f in farasa_word_spans:
            if f["norm_start"] != -1:
                # If the mapped farasa word overlaps with this regex match
                if max(match_start, f["norm_start"]) < min(match_end, f["norm_end"]):
                    grouped_farasa.append(f)

        farasa_seg, affix_structure = _reconstruct_farasa_segmentation(
            grouped_farasa, clean_to_norm, normalized_prefix, form
        )

        orig_start = norm_to_orig_map[match_start]
        orig_end = norm_to_orig_map[match_end]

        tokens.append(
            Token(
                index=token_index,
                form=form,
                span=(orig_start, orig_end),
                norm_span=(match_start, match_end),
                affix_structure=affix_structure,
                farasa_segmentation=farasa_seg,
            )
        )
        token_index += 1

    return tokens


#############################################################################
# Public API
#############################################################################

_PREFIX_TAG_TO_CLITICS: dict[str, list[str]] = {}
for clitic, tag in PREFIX_CLITICS:
    _PREFIX_TAG_TO_CLITICS.setdefault(tag, []).append(clitic)

_SUFFIX_TAG_TO_CLITICS: dict[str, list[str]] = {}
for clitic, tag in SUFFIX_CLITICS:
    _SUFFIX_TAG_TO_CLITICS.setdefault(tag, []).append(clitic)


def break_token(token: Token) -> list[tuple[str, str]] | None:
    """Reconstructs the clitic/stem breakdown for a token from its farasa_segmentation.

    uses the farasa_segmentation and affix_structure to break the token to it's segmented parts.

    Args:
        token: A Token produced by the segmentation stage.

    Returns:
        A list of (tag, substring) pairs in left-to-right order, where each
        pair contains a component label (ex. CONJ, DET, STEM, PRON) and the
        corresponding part from token.farasa_segmentation. Returns None when
        affix_structure or farasa_segmentation is None.
    """
    if token.farasa_segmentation is None or token.affix_structure is None:
        return None

    tags = token.affix_structure.split("+")
    segments = token.farasa_segmentation.split("+")

    stem_idx = tags.index("STEM")
    
    prefix_clitics = segments[:stem_idx]
    
    num_suffixes = len(tags) - stem_idx - 1
    if num_suffixes > 0:
        suffix_clitics = segments[-num_suffixes:]
        stem_str = "".join(segments[stem_idx : -num_suffixes])
    else:
        suffix_clitics = []
        stem_str = "".join(segments[stem_idx:])

    components = []
    for i in range(stem_idx):
        components.append((tags[i], prefix_clitics[i]))
        
    components.append(("STEM", stem_str))
    
    for i in range(num_suffixes):
        components.append((tags[stem_idx + 1 + i], suffix_clitics[i]))
        
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
    matches = list(re.finditer(r"\w+|[^\w\s]", completed_prefix))
    if not matches:
        return []

    seg = _get_segmenter()
    farasa_output: str = seg.segment(completed_prefix)

    return _align_tokens(farasa_output, completed_prefix, norm_to_orig_map, matches)
