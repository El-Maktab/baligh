import json
from functools import partial
from pathlib import Path

from transformers import DataCollatorForTokenClassification, Trainer, TrainingArguments

from src.services.gec.modules.edit_tagger.training.metrics import compute_metrics
 

def build_trainer(
    model,
    train_dataset,
    tokenizer,
    output_dir="./gec_output",
    num_train_epochs=10,
    weight_decay=0.01,
    warmup_ratio=0.1,
    label2id_path=None,
):
    id2label = _load_id2label(label2id_path)
    metrics_fn = partial(compute_metrics, id2label=id2label)

    args = TrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=num_train_epochs,
        weight_decay=weight_decay,
        warmup_ratio=warmup_ratio,
        save_strategy="epoch",
        save_total_limit=3,
        metric_for_best_model="f05",
        greater_is_better=True,
        remove_unused_columns=False,
    )

    return Trainer(
        model=model,
        args=args,
        train_dataset=train_dataset,
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
