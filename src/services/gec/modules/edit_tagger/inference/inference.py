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
        self.device = device
        self.label_vocab = label_vocab
        self.label_vocab.id2label = {
            int(k): v for k, v in label_vocab.id2label.items()
        }

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

        input_ids = encoding["input_ids"].to(self.device)
        attention_mask = encoding["attention_mask"].to(self.device)

        with torch.no_grad():
            outputs = self.model(
                input_ids=input_ids,
                attention_mask=attention_mask,
            )

        logits = outputs["logits"] if isinstance(outputs, dict) and "logits" in outputs else outputs.logits
        if logits.dim() == 3:
            pred_ids = logits.argmax(dim=-1)[0].tolist()
        else:
            pred_ids = logits[0].tolist()

        subwords = self.tokenizer.tokenizer.convert_ids_to_tokens(
            input_ids[0]
        )

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