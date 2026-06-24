import json
from functools import partial
from pathlib import Path

from transformers import DataCollatorForTokenClassification, Trainer, TrainingArguments

from src.services.gec.training.metrics import compute_metrics


def build_trainer(
    model,
    train_dataset,
    tokenizer,
    eval_dataset=None,
    output_dir="./gec_output",
    num_train_epochs=10,
    batch_size=16,
    learning_rate=5e-5,
    weight_decay=0.01,
    warmup_ratio=0.1,
    gradient_accumulation_steps=1,
    fp16=False,
    label2id_path=None,
):
    id2label = _load_id2label(label2id_path)
    metrics_fn = partial(compute_metrics, id2label=id2label) if id2label else None

    args = TrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=num_train_epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size * 2,
        learning_rate=learning_rate,
        weight_decay=weight_decay,
        warmup_ratio=warmup_ratio,
        gradient_accumulation_steps=gradient_accumulation_steps,
        eval_strategy="epoch" if eval_dataset else "no",
        save_strategy="epoch",
        save_total_limit=3,
        load_best_model_at_end=eval_dataset is not None,
        metric_for_best_model="f05",
        greater_is_better=True,
        fp16=fp16,
        report_to="none",
        remove_unused_columns=False,
    )

    return Trainer(
        model=model,
        args=args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=DataCollatorForTokenClassification(tokenizer=tokenizer),
        compute_metrics=metrics_fn,
    )


def _load_id2label(label2id_path):
    if label2id_path is None:
        return None
    p = Path(label2id_path)
    if not p.exists():
        return None
    with p.open(encoding="utf-8") as f:
        label2id = json.load(f)
    return {v: k for k, v in label2id.items()}
