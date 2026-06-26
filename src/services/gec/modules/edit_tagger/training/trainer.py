"""Helper to build a HuggingFace Trainer for the GEC edit-tagger."""

from src.services.gec.modules.edit_tagger.training.metrics import compute_metrics
from transformers import DataCollatorForTokenClassification, Trainer, TrainingArguments


def build_trainer(
    model,
    train_dataset,
    tokenizer,
    output_dir="../models/",
    num_train_epochs=10,
    weight_decay=0.01,
    warmup_ratio=0.1,
    use_crf: bool = False,
):
    """Build a HuggingFace Trainer for the edit-tagger model."""
    args = TrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=num_train_epochs,
        weight_decay=weight_decay,
        warmup_ratio=warmup_ratio,
        save_strategy="epoch",
        metric_for_best_model="f05",
        greater_is_better=True,
        remove_unused_columns=False,
    )

    return Trainer(
        model=model,
        args=args,
        train_dataset=train_dataset,
        data_collator=DataCollatorForTokenClassification(tokenizer=tokenizer),
        compute_metrics=compute_metrics,
    )
