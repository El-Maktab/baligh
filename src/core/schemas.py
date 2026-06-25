"""Core schemas for Baligh.

This module defines the basic data structures shared across all pipeline modules.

References:
- docs/contracts/preprocessing-contract.md

Authors:
    - Akram Hany
"""

from pydantic import BaseModel, Field, model_validator


class Token(BaseModel):
    """Represents a token used by the Baligh service.

    Attributes:
        index: Position of this token in the token list (0-based).
        form: Surface form of the token taken from normalized_text. Semantically
            equivalent to the original surface form, span is provided for UI
            character-offset positioning on the original text.
        span: Start and end character offsets in the original text, used by the
            UI to highlight characters the user actually typed.
        norm_span: Start and end character offsets on the normalized text, may
            differ from span when NFKC expands a single codepoint into multiple
            characters.
        affix_structure: Plus-joined clitic/stem breakdown derived from Farasa
            segmentation (ex. "CONJ+PREP+DET+STEM"), None for punctuation and
            non-Arabic tokens.
        is_oov: stands for Out-Of-Vocabulary, which means that the word is invalid
            and matches no word in dictionary.
        farasa_segmentation: The raw +-joined string produced by Segmenter for this
            token (ex. "ل+ال+حج").
    """

    index: int = 0
    form: str = ""
    span: tuple[int, int] = Field(default=(0, 0))
    norm_span: tuple[int, int] | None = None
    affix_structure: str | None = None
    farasa_segmentation: str | None = None
    is_oov: bool = False

    @model_validator(mode="after")
    def set_default_spans(self) -> "Token":
        """Set span defaults based on form length."""
        if self.span == (0, 0):
            self.span = (0, len(self.form))
        if self.norm_span is None:
            self.norm_span = self.span
        return self


class MorphAnalysis(BaseModel):
    """Morphological analysis candidate for a token.

    Represents one candidate analysis produced by a morphological analyzer.

    Attributes:
        token_index: Index of the corresponding Token.
        lemma: Base/root form of the token, None for punctuation and non-Arabic.
        pos: Part-of-speech tag. One of: NOUN, NOUN_PROP, NOUN_QUANT, VERB,
            ADJ, ADV, PREP, CONJ, PRON, PRON_REL, PRON_INTERROG, DET, PART,
            PUNC, NUM, INTJ. See the POS Tagset section in the contract.
        gender: "masculine", "feminine", or None.
        number: "singular", "dual", "plural", or None.
        person: "first", "second", "third", or None.
        definiteness: "definite", "indefinite", or None.
        case: "nominative", "accusative", "genitive", or None if can't be determned.
        tense: "past", "present", "imperative", or None for non verbs.
        voice: "active", "passive", or None for non verbs.
        mood: "indicative", "subjunctive", "jussive", or None for non verbs.
        diacritized: The token form with full diacritics as resolved by disambiguation.
        is_disambiguated: True for the candidate selected by the disambiguator.
    """

    token_index: int
    lemma: str | None = None
    pos: str
    gender: str | None = None
    number: str | None = None
    person: str | None = None
    definiteness: str | None = None
    case: str | None = None
    tense: str | None = None
    voice: str | None = None
    mood: str | None = None
    diacritized: str | None = None
    is_disambiguated: bool = False
