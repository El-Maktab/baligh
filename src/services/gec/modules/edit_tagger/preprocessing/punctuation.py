"""Punctuation detection utilities."""

ARABIC_PUNCTUATION = {
    "،",
    "؛",
    "؟",
}

LATIN_PUNCTUATION = {
    ".",
    ",",
    ";",
    ":",
    "!",
    "?",
    "(",
    ")",
    "{",
    "}",
    '"',
    "'",
}

PUNCTUATION_SET = ARABIC_PUNCTUATION | LATIN_PUNCTUATION


def is_punctuation(text: str) -> bool:
    """Check if text contains only punctuation."""
    return text != "" and all(char in PUNCTUATION_SET for char in text)
