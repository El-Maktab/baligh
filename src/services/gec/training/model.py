"""GEC edit-tagger model architecture based on HuggingFace AutoModelForTokenClassification."""

from transformers import AutoModelForTokenClassification


class GECTaggerModel:
    """Wrapper around a HuggingFace token-classification model.

    Dynamically configures ``num_labels`` from the label vocabulary so the
    classification head matches the exact set of edit tags produced by the
    data pipeline.
    """

    def __init__(self, checkpoint: str, label2id: dict[str, int]) -> None:
        self.id2label: dict[int, str] = {v: k for k, v in label2id.items()}
        self.model = AutoModelForTokenClassification.from_pretrained(
            checkpoint,
            num_labels=len(label2id),
            id2label=self.id2label,
            label2id=label2id,
        )

    def __call__(self, **kwargs):
        return self.model(**kwargs)

    def to(self, device):
        self.model = self.model.to(device)
        return self

    def train(self):
        self.model.train()

    def eval(self):
        self.model.eval()

    @property
    def device(self):
        return next(self.model.parameters()).device
