import torch

from src.services.gec.utils.string_utils import Tokenizer


class GECInferencePipeline:

    def __init__(
        self,
        model,
        tokenizer: Tokenizer,
        label_vocab,
        device: str = "cpu",
    ):
        self.model = model
        self.tokenizer = tokenizer
        self.label_vocab = label_vocab
        self.device = device

        self.model.to(device)
        self.model.eval()

    def predict(
        self,
        text: str,
    ) -> tuple[list[str], list[str]]:
        """
        Returns:
            subwords: list[str]
            labels: list[str]
        """
        encoding = self.tokenizer.encode(text)
        print(encoding)

        input_ids = encoding["input_ids"].to(self.device)
        attention_mask = encoding["attention_mask"].to(self.device)

        with torch.no_grad():
            outputs = self.model(
                input_ids=input_ids,
                attention_mask=attention_mask,
            )

        pred_ids = outputs.logits.argmax(dim=-1)[0].tolist()

        subwords = self.tokenizer.tokenizer.convert_ids_to_tokens(
            input_ids[0]
        )
        print(type(next(iter(self.label_vocab.id2label.keys()))))
        print(type(pred_ids[0]))
        print(pred_ids)
        print(max(pred_ids))
        print(min(pred_ids))

        print(len(self.label_vocab.id2label))
        print(self.model.config.num_labels)

        filtered_subwords = []
        filtered_labels = []

        for subword, pred_id in zip(subwords, pred_ids):
            if subword in {
                "[CLS]",
                "[SEP]",
                "[PAD]",
            }:
                continue

            filtered_subwords.append(subword)

            filtered_labels.append(
                self.label_vocab.id2label.get(
                    pred_id,
                    "[UNK]",
                )
            )

        return filtered_subwords, filtered_labels