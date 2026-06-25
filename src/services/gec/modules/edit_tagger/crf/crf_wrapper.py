import torch
import torch.nn as nn
from torchcrf import CRF


class BertCRFForTokenClassification(nn.Module):
    """Wrap a HuggingFace token classification model with a CRF layer.

    The wrapper reuses the original model's encoder and classification head to
    produce emission scores, then applies a CRF on top. This design keeps the
    original model architecture intact while adding sequence‑level decoding.
    """

    def __init__(self, base_model: nn.Module, num_labels: int, label2id: dict | None = None):
        super().__init__()
        self.bert = base_model
        # Assume the original model already has a classification head that
        # produces logits of shape (batch, seq_len, num_labels).
        # Reuse it directly.
        self.classifier = getattr(base_model, "classifier", None)
        if self.classifier is None:
            raise AttributeError("Base model does not expose a 'classifier' attribute")
        # CRF expects emission scores of shape (batch, seq_len, num_labels)
        self.crf = CRF(num_tags=num_labels, batch_first=True)
        self.num_labels = num_labels
        self.label2id = label2id or {}

    def forward(self, input_ids, attention_mask=None, labels=None):
        """Run the model.

        Args:
            input_ids: Tensor of token ids.
            attention_mask: Optional mask tensor.
            labels: Optional gold label ids for training.

        Returns:
            dict containing ``loss`` (when ``labels`` provided) and ``logits``
            (emission scores). For inference without ``labels`` the ``logits``
            field contains the decoded label sequence.
        """
        # Get hidden states from the base BERT model
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        # ``outputs`` is a ``ModelOutput``; use ``last_hidden_state``
        hidden_states = outputs.last_hidden_state
        # Produce emission logits via the classifier head
        emissions = self.classifier(hidden_states)

        # If training, compute negative log‑likelihood loss via CRF
        if labels is not None:
            # CRF expects ``mask`` of shape (batch, seq_len) – convert bool tensor
            mask = attention_mask.bool() if attention_mask is not None else None
            loss = -self.crf(emissions, labels, mask=mask, reduction="mean")
            return {"loss": loss, "logits": emissions}
        else:
            # Inference – Viterbi decoding
            mask = attention_mask.bool() if attention_mask is not None else None
            decoded = self.crf.decode(emissions, mask=mask)
            # ``decoded`` is a list of list of tag ids (batch size list)
            # Convert to tensor for downstream compatibility
            # Pad to the max length in the batch
            max_len = max(len(seq) for seq in decoded) if decoded else 0
            if max_len == 0:
                # Empty batch – return empty tensor
                return {"logits": torch.empty((0, 0), dtype=torch.long, device=emissions.device)}
            padded = torch.full((len(decoded), max_len), -100, dtype=torch.long, device=emissions.device)
            for i, seq in enumerate(decoded):
                padded[i, : len(seq)] = torch.tensor(seq, dtype=torch.long, device=emissions.device)
            return {"logits": padded}
