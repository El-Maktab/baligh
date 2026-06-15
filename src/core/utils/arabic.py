"""Arabic character-level helper utilities.

All functions here are pure (no side-effects, no external dependencies)
so they are safe to import anywhere.

Authors:
    Amir Anwar
"""

from __future__ import annotations

import re
import unicodedata

# ################################################################################
# character sets
# ################################################################################

# Tashkeel (diacritics) range U+064B - U+065F and the U+0670 is a supscript alif.
# For the arabic unicode block you could see this https://en.wikipedia.org/wiki/Arabic_(Unicode_block)
_DIACRITICS_RE = re.compile(r"[\u064b-\u065f\u0670]")

# Tatweel/kashida elongation mark.
# ـــــــــــــــــــــــــــ
_TATWEEL = "\u0640"

# Invisible directional/control marks commonly found in scraped Arabic resources.
_CONTROL_MARKS_RE = re.compile(r"[\u200e\u200f\u202a-\u202e\u2066-\u2069]")

_WHITESPACE_RE = re.compile(r"\s+")

# Arabic letters plus common Arabic presentation extensions used in wordlists.
_ARABIC_LETTERS_RE = re.compile(r"^[\u0621-\u064a\u066e-\u06d3]+$")

_LOOSE_ARABIC_TRANSLATION = str.maketrans(
    {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ٱ": "ا",
        "ى": "ي",
        "ة": "ه",
    }
)

# Arabic-script punctuation characters.
# NOTE: these are not the same as the latin ones we are used too.
ARABIC_PUNCTUATION: frozenset[str] = frozenset("،؟؛")

# All punctuation we care about
ALL_PUNCTUATION: frozenset[str] = ARABIC_PUNCTUATION | frozenset(".!?,;:")

# Common clitic prefixes that may precede a stem
# حروف متصلة
# والكتاب - فقال - بالقلم
_CLITIC_PREFIXES: frozenset[str] = frozenset("وفبلك")

# Alif variants
# وصل
# قطع
# قطع مكسورة
# ممدودة
ALIF_VARIANTS: frozenset[str] = frozenset("اأإآ")

# Ya character (with dots)
YA = "ي"

# Alif Maqsura (without dots)
ALIF_MAQSURA = "ى"

# Ta Marbuta
TA_MARBUTA = "ة"

# Ha
HA = "ه"

# Bare Alif الف وصل
BARE_ALIF = "ا"

# POS tags that require a همزة قطع on the stem's initial Alif.
# PREP حرف جر
# PART أداة
# CONJ أداة ربط
HAMZA_REQUIRED_POS: frozenset[str] = frozenset({"PREP", "PART", "CONJ"})


# ################################################################################
# Functions
# ############################################################################


def strip_diacritics(text: str) -> str:
    """Remove all Arabic tashkeel diacritics from text.

    Args:
        text: Any string

    Returns:
        The string with all diacritics (U+064B-U+065F, U+0670) removed.
    """
    return _DIACRITICS_RE.sub("", text)


def normalize_arabic_surface(
    text: str,
    *,
    collapse_whitespace: bool = False,
) -> str:
    """Return a form without hidden marks or diacritics.

    Args:
        text: Arabic or mixed-script text.
        collapse_whitespace: When true, any whitespace run is replaced by one
            regular space.

    Returns:
        Cleaned text that preserves Arabic spelling distinctions.
    """
    normalized = unicodedata.normalize("NFKC", text)
    normalized = _CONTROL_MARKS_RE.sub("", normalized)
    normalized = normalized.replace(_TATWEEL, "")
    normalized = strip_diacritics(normalized)
    if collapse_whitespace:
        normalized = _WHITESPACE_RE.sub(" ", normalized)
    return normalized.strip()


def loose_arabic_lookup_key(text: str) -> str:
    """Created a dict lookup key."""
    return normalize_arabic_surface(text, collapse_whitespace=True).translate(
        _LOOSE_ARABIC_TRANSLATION
    )


def is_arabic_word(text: str) -> bool:
    """Return true when text is a single Arabic-letter word.

    Args:
        text: Text

    Returns:
        True if the cleaned text contains only Arabic letters.
    """
    key = normalize_arabic_surface(text)
    return bool(key) and bool(_ARABIC_LETTERS_RE.fullmatch(key))


def first_significant_char(form: str, affix_structure: str | None = None) -> str:
    """Return the first character of the stem, skipping known clitic prefixes.

    Args:
        form: Surface form of the token (may include diacritics or clitics).
        affix_structure: CAMeL-style affix, like "CONJ+STEM" or
            None if unavailable.

    Returns:
        The first character of the identified stem, or the first character of
        form if the stem cannot be located.
    """
    clean = strip_diacritics(form)
    if not clean:
        return ""

    if affix_structure:
        # Only CONJ and particle-like single-char clitics add a surface char.
        # Each CONJ in the structure accounts for exactly 1 character.
        _SINGLE_CHAR_PREFIX_LABELS = frozenset({"CONJ", "CONJ2"})
        parts = affix_structure.upper().split("+")
        prefix_chars = 0
        for part in parts:
            if "STEM" in part:
                break
            if part in _SINGLE_CHAR_PREFIX_LABELS:
                prefix_chars += 1
            # DET (ال) adds 2 characters
        if prefix_chars < len(clean):
            return clean[prefix_chars]

    # Fallback strip clitic prefixes
    idx = 0
    while idx < len(clean) - 1 and clean[idx] in _CLITIC_PREFIXES:
        idx += 1
    return clean[idx]


def ends_with(form: str, char: str) -> bool:
    """Unicode-safe check whether form ends with char (ignoring diacritics).

    Args:
        form: Surface token form (may include trailing diacritics).
        char: A single character to check for.

    Returns:
        True if the last non-diacritic character of form equals char.

    Examples:
        >>> ends_with("المدرسةُ", "ة")
        True
        >>> ends_with("المدرسهُ", "ة")
        False
    """
    clean = strip_diacritics(form)
    return bool(clean) and clean[-1] == char


def is_arabic_punctuation(char: str) -> bool:
    """Return True if char is an Arabic punctuation mark.

    Args:
        char: A single character.

    Returns:
        True if the character is Arabic punctuation.
    """
    return char in ARABIC_PUNCTUATION
