"""Tokenizer for the Word N-Gram model.

Authors:
    Akram Hany
"""

import re

from src.core.utils.arabic import normalize_arabic_surface

SENTENCE_END = {".", "!", "?", "؟"}
KEEP_AS_TOKEN = {",", "،", ":", ";", "؛", '"', "'", "-"}

# Regex for punctuation splitting.
PUNCT_SPLIT_RE = re.compile(r'([.!؟?,،:;؛"\'-])')


def tokenize_text(text: str, is_inference: bool = False) -> list[str]:
    """Normalize and tokenize text into words and punctuation marks."""
    # Normalize text.
    text = normalize_arabic_surface(text)

    # Add spaces around punctuation.
    text = PUNCT_SPLIT_RE.sub(r" \1 ", text)

    # Tokenize and insert boundaries.
    tokens = ["<s>"]

    for token in text.split():
        if token in SENTENCE_END:
            # End of sentence.
            tokens.append("</s>")
            tokens.append("<s>")
        elif token in KEEP_AS_TOKEN:
            # Mid-sentence punctuation.
            tokens.append(token)
        else:
            if token.strip():
                tokens.append(token)

    # Close final sentence.
    # Skip if inference.
    if not is_inference and tokens[-1] != "</s>":
        tokens.append("</s>")

    # Clean empty sentence blocks.
    cleaned_tokens = []
    skip_next = False
    for i in range(len(tokens) - 1):
        if skip_next:
            skip_next = False
            continue

        if tokens[i] == "<s>" and tokens[i + 1] == "</s>":
            skip_next = True
        else:
            cleaned_tokens.append(tokens[i])

    if not skip_next:
        cleaned_tokens.append(tokens[-1])

    return cleaned_tokens
