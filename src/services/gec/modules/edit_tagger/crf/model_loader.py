"""Utility functions for loading the edit‑tagger model.

This module centralises model loading so that a CRF wrapper can be added
transparent to the rest of the code base. Existing pipelines that call
``load_base_model`` continue to work, while new scripts can enable the CRF
layer via ``load_model_with_optional_crf``.
"""

from pathlib import Path
from typing import Any

from transformers import AutoModelForTokenClassification

# Import the CRF wrapper lazily – avoids importing torchcrf unless required.

def load_base_model(checkpoint_path: str | Path, num_labels: int, label2id: dict) -> Any:
    """Load the original AraBERT token‑classification model.

    Args:
        checkpoint_path: Path or identifier of the pretrained checkpoint.
        num_labels: Number of label classes.
        label2id: Mapping from label string to integer id.
    Returns:
        An instance of ``AutoModelForTokenClassification`` ready for further
        wrapping.
    """
    model = AutoModelForTokenClassification.from_pretrained(
        str(checkpoint_path),
        num_labels=num_labels,
        id2label={v: k for k, v in label2id.items()},
        label2id=label2id,
    )
    return model


def wrap_with_crf(base_model: Any, num_labels: int, label2id: dict) -> Any:
    """Wrap a loaded model with the CRF layer.

    The wrapper lives in ``src.services.gec.modules.edit_tagger.model.crf_wrapper``
    and is imported only when needed to keep import overhead low.
    """
    from src.services.gec.modules.edit_tagger.crf.crf_wrapper import (
        BertCRFForTokenClassification,
    )

    return BertCRFForTokenClassification(base_model, num_labels=num_labels, label2id=label2id)


def load_model_with_optional_crf(
    checkpoint_path: str | Path,
    num_labels: int,
    label2id: dict,
    use_crf: bool = False,
) -> Any:
    """Load a model optionally wrapped with a CRF layer.

    Args:
        checkpoint_path: Path or identifier of the checkpoint.
        num_labels: Number of label classes.
        label2id: Mapping from label string to id.
        use_crf: If ``True``, the returned model includes a CRF layer.
    Returns:
        Either the base model or a ``BertCRFForTokenClassification`` instance.
    """
    base = load_base_model(checkpoint_path, num_labels, label2id)
    if use_crf:
        return wrap_with_crf(base, num_labels, label2id)
    return base
