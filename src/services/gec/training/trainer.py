"""HuggingFace Trainer construction for the GEC edit-tagger model."""

import json
from functools import partial
from pathlib import Path

from transformers import Trainer, TrainingArguments

from src.services.gec.training.metrics import compute_metrics


def build_trainer(
    model_wrapper,
    train_dataset,
    eval_dataset=None,
    output_dir: str | Path = "./gec_output",
    num_train_epochs: int = 10,
    per_device_train_batch_size: int = 16,
    per_device_eval_batch_size: int = 32,
    learning_rate: float = 5e-5,
    weight_decay: float = 0.01,
    warmup_ratio: float = 0.1,
    logging_steps: int = 50,
    eval_strategy: str = "epoch",
    save_strategy: str = "epoch",
    save_total_limit: int = 3,
    load_best_model_at_end: bool = True,
    metric_for_best_model: str = "f05",
    greater_is_better: bool = True,
    gradient_accumulation_steps: int = 1,
    fp16: bool = False,
    label2id_path: str | Path | None = None,
    id2label_path: str | Path | None = None,
) -> Trainer:
    """Construct a HuggingFace ``Trainer`` ready for ``.train()``.

    Args:
        model_wrapper: A ``GECTaggerModel`` wrapper (assumes ``model`` attr).
        train_dataset: Training ``GECTrainingDataset``.
        eval_dataset: Optional evaluation ``GECTrainingDataset``.
        output_dir: Directory for checkpoints and logs.
        num_train_epochs: Number of training epochs.
        per_device_train_batch_size: Batch size per GPU for training.
        per_device_eval_batch_size: Batch size per GPU for evaluation.
        learning_rate: Peak learning rate.
        weight_decay: AdamW weight decay.
        warmup_ratio: Ratio of total steps used for linear warmup.
        logging_steps: Log every N steps.
        eval_strategy: Evaluation strategy (``epoch`` or ``steps``).
        save_strategy: Saving strategy (``epoch`` or ``steps``).
        save_total_limit: Maximum number of checkpoints to keep.
        load_best_model_at_end: Whether to load the best checkpoint at the end.
        metric_for_best_model: Metric name used to select the best model.
        greater_is_better: Whether a higher metric value is better.
        gradient_accumulation_steps: Number of gradient accumulation steps.
        fp16: Whether to use FP16 mixed precision.
        label2id_path: Path to the ``label2id.json`` file for metrics.
        id2label_path: Path to the ``id2label.json`` file for metrics.

    Returns:
        A ``Trainer`` instance ready for training.
    """
    output_dir = Path(output_dir)

    id2label = _load_id2label(id2label_path, label2id_path)

    training_args = TrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=num_train_epochs,
        per_device_train_batch_size=per_device_train_batch_size,
        per_device_eval_batch_size=per_device_eval_batch_size,
        learning_rate=learning_rate,
        weight_decay=weight_decay,
        warmup_ratio=warmup_ratio,
        logging_steps=logging_steps,
        eval_strategy=eval_strategy,
        save_strategy=save_strategy,
        save_total_limit=save_total_limit,
        load_best_model_at_end=load_best_model_at_end and eval_dataset is not None,
        metric_for_best_model=metric_for_best_model,
        greater_is_better=greater_is_better,
        gradient_accumulation_steps=gradient_accumulation_steps,
        fp16=fp16,
        report_to="none",
        remove_unused_columns=False,
    )

    metrics_fn = partial(compute_metrics, id2label=id2label) if id2label else None

    trainer = Trainer(
        model=model_wrapper.model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        compute_metrics=metrics_fn if id2label else None,
    )

    return trainer


def _load_id2label(
    id2label_path: str | Path | None,
    label2id_path: str | Path | None,
) -> dict[int, str] | None:
    """Load id2label mapping from a JSON file.

    Tries ``id2label_path`` first; falls back to inverting
    ``label2id_path``.
    """
    if id2label_path is not None:
        p = Path(id2label_path)
        if p.exists():
            with p.open(encoding="utf-8") as f:
                raw = json.load(f)
            return {int(k): v for k, v in raw.items()}

    if label2id_path is not None:
        p = Path(label2id_path)
        if p.exists():
            with p.open(encoding="utf-8") as f:
                label2id = json.load(f)
            return {v: k for k, v in label2id.items()}

    return None
