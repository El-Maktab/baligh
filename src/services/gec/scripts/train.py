"""CLI entry-point for training the GEC edit-tagger model.

Usage::

    python -m src.services.gec.scripts.train \\
        --checkpoint aubmindlab/bert-base-arabertv02 \\
        --train_jsonl src/services/gec/data/edit_tagger/processed/tokens_labels.jsonl \\
        --output_dir src/services/gec/data/edit_tagger/models/edit_tagger_v1 \\
        --epochs 10 --batch_size 16
"""

import argparse
import json
from pathlib import Path

from transformers import AutoTokenizer

from src.services.gec.config import (
    CHECKPOINT_PATH,
    ID2LABEL_PATH,
    LABEL2ID_PATH,
)
from src.services.gec.training.datasets import GECTrainingDataset
from src.services.gec.training.model import GECTaggerModel
from src.services.gec.training.trainer import build_trainer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train the GEC edit-tagger sequence labelling model",
    )
    parser.add_argument(
        "--checkpoint",
        type=str,
        default="aubmindlab/bert-base-arabertv02",
        help="HuggingFace model checkpoint / identifier",
    )
    parser.add_argument(
        "--train_jsonl",
        type=str,
        default=str(CHECKPOINT_PATH),
        help="Path to the training JSONL file",
    )
    parser.add_argument(
        "--eval_jsonl",
        type=str,
        default=None,
        help="Path to the evaluation JSONL file (optional)",
    )
    parser.add_argument(
        "--label2id",
        type=str,
        default=str(LABEL2ID_PATH),
        help="Path to label2id.json",
    )
    parser.add_argument(
        "--id2label",
        type=str,
        default=str(ID2LABEL_PATH),
        help="Path to id2label.json",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=str(
            Path(__file__).resolve().parents[2]
            / "data"
            / "edit_tagger"
            / "models"
            / "edit_tagger_v1"
        ),
        help="Output directory for model checkpoints",
    )
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--eval_batch_size", type=int, default=32)
    parser.add_argument("--learning_rate", type=float, default=5e-5)
    parser.add_argument("--fp16", action="store_true")
    parser.add_argument("--max_length", type=int, default=512)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    with open(args.label2id, encoding="utf-8") as f:
        label2id = json.load(f)

    tokenizer = AutoTokenizer.from_pretrained(args.checkpoint)

    print(f"Loading training data from {args.train_jsonl}")
    train_dataset = GECTrainingDataset(
        jsonl_path=Path(args.train_jsonl),
        tokenizer=tokenizer,
        label2id=label2id,
        max_length=args.max_length,
    )

    eval_dataset = None
    if args.eval_jsonl:
        print(f"Loading eval data from {args.eval_jsonl}")
        eval_dataset = GECTrainingDataset(
            jsonl_path=Path(args.eval_jsonl),
            tokenizer=tokenizer,
            label2id=label2id,
            max_length=args.max_length,
        )

    print(f"Initialising model from {args.checkpoint}")
    print(f"num_labels = {len(label2id)}")
    model_wrapper = GECTaggerModel(
        checkpoint=args.checkpoint,
        label2id=label2id,
    )

    trainer = build_trainer(
        model_wrapper=model_wrapper,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.eval_batch_size,
        learning_rate=args.learning_rate,
        fp16=args.fp16,
        label2id_path=args.label2id,
        id2label_path=args.id2label,
    )

    print("Starting training...")
    trainer.train()

    print(f"Saving model to {args.output_dir}")
    trainer.save_model(str(Path(args.output_dir) / "best"))
    tokenizer.save_pretrained(str(Path(args.output_dir) / "best"))

    print("Training complete.")


if __name__ == "__main__":
    main()
