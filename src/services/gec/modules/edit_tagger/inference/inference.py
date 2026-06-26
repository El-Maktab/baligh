"""GEC inference pipeline for edit-tagger models."""

import torch
from src.services.gec.utils.string_utils import Tokenizer


class GECInferencePipeline:
    """Runs inference on a trained edit-tagger model."""

    def __init__(
        self,
        model,
        tokenizer: Tokenizer,
        label_vocab,
        device: str = "cpu",
    ):
        """Initialize the inference pipeline.

        Args:
            model: The token-classification model.
            tokenizer: Sub-word tokenizer.
            label_vocab: Mapping between label IDs and names.
            device: Torch device string.

        """
        self.model = model
        self.tokenizer = tokenizer
        self.device = device
        self.label_vocab = label_vocab
        self.label_vocab.id2label = {int(k): v for k, v in label_vocab.id2label.items()}

        self.model.to(device)
        self.model.eval()

    def predict(
        self,
        text: str,
    ) -> tuple[list[float], list[str], list[str]]:
        """Predict subword tags for a text string.

        Returns:
            A tuple of (subwords, labels).
        """
        encoding = self.tokenizer.encode(text)

        input_ids = encoding["input_ids"].to(self.device)
        attention_mask = encoding["attention_mask"].to(self.device)

        with torch.no_grad():
            outputs = self.model(
                input_ids=input_ids,
                attention_mask=attention_mask,
            )

        logits = (
            outputs["logits"]
            if isinstance(outputs, dict) and "logits" in outputs
            else outputs.logits
        )
        if logits.dim() == 3:
            pred_ids = logits.argmax(dim=-1)[0].tolist()
        else:
            pred_ids = logits[0].tolist()

        conf = logits[pred_ids]
        subwords = self.tokenizer.tokenizer.convert_ids_to_tokens(input_ids[0])

        filtered_subwords = []
        filtered_labels = []

        for subword, pred_id in zip(subwords, pred_ids, strict=False):
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

        return conf, filtered_subwords, filtered_labels
