"""String utility functions."""

from camel_tools.utils.normalize import (
    normalize_alef_maksura_ar,
    normalize_alef_ar,
    normalize_teh_marbuta_ar,
)
from camel_tools.utils.dediac import dediac_ar
from transformers import AutoTokenizer

# Max sequence length used during training. Must stay in sync with
# GECTrainingDataset(max_length=...) to avoid train/inference mismatch.
_MAX_LENGTH = 256


def _normalize_arabic(text: str) -> str:
    """Light Arabic normalization to match QALB corpus preprocessing.

    Strips diacritics and normalises Alef/Ya/Ta-marbuta variants so that
    raw inference text is closer to the training distribution.
    """
    text = dediac_ar(text)
    text = normalize_alef_ar(text)
    text = normalize_alef_maksura_ar(text)
    text = normalize_teh_marbuta_ar(text)
    return text


class Tokenizer:

    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained("aubmindlab/bert-base-arabertv02")

    def tokenize(self, word: str) -> list[str]:
        """Tokenize a word into Arabert subword tokens.
        Args:
            word: The word to tokenize.

        Returns:
            A list of subword tokens produced by the Arabert tokenizer.
        """

        tokens = self.tokenizer.tokenize(word)
        return tokens

    def get_token_id(self, tokens: list[str]) -> list[int]:
        return self.tokenizer.convert_tokens_to_ids(tokens)

    def encode(self, text: str):
        """Encode raw Arabic text for inference.

        Applies the same normalization as the QALB training corpus and
        truncates to the training max_length so the model never sees
        sequences longer than those it was trained on.
        """
        text = _normalize_arabic(text)
        return self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=_MAX_LENGTH,
        )