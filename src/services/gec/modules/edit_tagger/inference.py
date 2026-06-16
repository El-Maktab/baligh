import torch

from src.services.gec.schemas import GECInput, EditTaggerCandidateEdit
from src.services.gec.utils import Tokenizer
class GECInferencePipeline:
    def __init__(
        self,
        model,
        tokenizer: Tokenizer,
        label_vocab,
        rewriter,
    ):
        self.model = model
        self.tokenizer = tokenizer
        self.label_vocab = label_vocab
        self.rewriter = rewriter

    def subword_to_word_labels(
        labels: list[str],
        word_ids: list[int | None]) -> list[str]:
        word_labels = {}

        for label, word_id in zip(labels, word_ids):
            if word_id is None:
                continue

            if word_id not in word_labels:
                word_labels[word_id] = label


    def predict(self, input: GECInput) -> EditTaggerCandidateEdit:
        words: list[str] = [token.form for token in input.tokens]
        tokens: list[list[str]] = [self.tokenizer.tokenize(word) for word in words]
        
        with torch.no_grad():
            logits = self.model(**tokens)

        pred_ids = logits.argmax(-1).squeeze(0)

        labels = [
            self.label_vocab.id2label[idx]
            for idx in pred_ids.tolist()
        ]