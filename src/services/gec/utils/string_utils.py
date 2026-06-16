"""String utility functions."""

from transformers import AutoTokenizer

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