from src.services.gec.data.edit_tagger.common import Alignment


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
"[",
"]",
"{",
"}",
'"',
"'",
}

PUNCTUATION_SET = (
ARABIC_PUNCTUATION |
LATIN_PUNCTUATION
)

def is_punctuation(text: str) -> bool:
    text != "" and all(char in PUNCTUATION_SET for char in text)
