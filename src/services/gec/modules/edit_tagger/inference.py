import torch

from src.services.gec.utils.string_utils import Tokenizer


class GECInferencePipeline:

    def __init__(self, model, tokenizer: Tokenizer, label_vocab):
        self.model = model
        self.tokenizer = tokenizer
        self.label_vocab = label_vocab

    def predict(self, text: str) -> tuple[list[str], list[str]]:
        words = text.split(" ")
        print("words: ", words)
        tokens = []
        for word in words:
            tokens.append(self.tokenizer.tokenize(word))

        print("tokens: ", tokens)
        encoding = self.tokenizer.tokenizer(
            tokens,
            is_split_into_words=True,
            add_special_tokens=True,
            return_tensors="pt",
            truncation=True,
            padding=True,
        )
        print(encoding)

        input_ids = encoding["input_ids"]
        attention_mask = encoding["attention_mask"]
        word_ids = encoding.word_ids()

        with torch.no_grad():
            outputs = self.model(
                input_ids=input_ids,
                attention_mask=attention_mask,
            )

        logits = outputs.logits
        pred_ids = logits.argmax(-1).squeeze(0).tolist()

        subword_labels = [
            self.label_vocab.id2label.get(idx, "[UNK]")
            for idx in pred_ids
        ]

        word_labels = self._subword_to_word_labels(subword_labels, word_ids)

        return subword_labels, word_labels

    def _subword_to_word_labels(
        self,
        labels: list[str],
        word_ids: list[int | None],
    ) -> list[str]:
        word_label_map = {}
        
        for label, word_id in zip(labels, word_ids):
            if word_id is None:
                continue
            if word_id not in word_label_map:
                word_label_map[word_id] = label
        
        if not word_label_map:
            return []
        
        max_word_id = max(word_label_map.keys())
        return [word_label_map.get(i, "[PAD]") for i in range(max_word_id + 1)]