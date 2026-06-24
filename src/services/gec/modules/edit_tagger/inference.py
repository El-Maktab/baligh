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

    @staticmethod
    def subword_to_word_labels(
        labels: list[str],
        word_ids: list[int | None]) -> list[str]:
        word_labels = {}

        for label, word_id in zip(labels, word_ids):
            if word_id is None:
                continue

            if word_id not in word_labels:
                word_labels[word_id] = label
        
        return [word_labels[i] for i in range(len(word_labels))]


    def predict(self, input: GECInput) -> list[str]:
        words: list[str] = [token.form for token in input.tokens]
        tokens: list[list[str]] = [self.tokenizer.tokenize(word) for word in words]
        
        input_ids = self.tokenizer.convert_tokens_to_ids(tokens)
        
        with torch.no_grad():
            logits = self.model(input_ids=input_ids)

        pred_ids = logits.logits.argmax(-1).squeeze(0)

        labels = [
            self.label_vocab.id2label[idx]
            for idx in pred_ids.tolist()
        ]
        return labels