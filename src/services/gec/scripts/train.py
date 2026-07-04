"""Training script for the GEC edit-tagger model."""

import argparse
import json
from pathlib import Path

from transformers import AutoTokenizer

from src.runtime_config import load_runtime_config
from src.services.gec.modules.edit_tagger.training.datasets import GECTrainingDataset
from src.services.gec.modules.edit_tagger.training.trainer import build_trainer

_EDIT_TAGGER = load_runtime_config().gec.edit_tagger
CHECKPOINT_PATH = _EDIT_TAGGER.resolved_checkpoint_path
LABEL2ID_PATH = _EDIT_TAGGER.resolved_label2id_path
TEST_JSONL_PATH = _EDIT_TAGGER.resolved_test_jsonl_path


def main():
    """Parse arguments and launch training."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", default="aubmindlab/bert-base-arabertv02")
    parser.add_argument("--train_jsonl", default=str(CHECKPOINT_PATH))
    parser.add_argument("--eval_jsonl", default=str(TEST_JSONL_PATH))
    parser.add_argument("--label2id", default=str(LABEL2ID_PATH))
    parser.add_argument(
        "--output_dir",
        default=str(
            Path(__file__).resolve().parents[2]
            / "modules"
            / "models"
            / "edit_tagger_v1"
        ),
    )
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=5e-5)
    parser.add_argument("--max_length", type=int, default=256)
    parser.add_argument("--use-crf", action="store_true")
    args = parser.parse_args()

    with open(args.label2id, encoding="utf-8") as f:
        label2id = json.load(f)

    tokenizer = AutoTokenizer.from_pretrained(args.checkpoint)

    train_dataset = GECTrainingDataset(
        args.train_jsonl, tokenizer, label2id, max_length=args.max_length
    )

    trainer = build_trainer(
        model=args.checkpoint,
        train_dataset=train_dataset,
        tokenizer=tokenizer,
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        weight_decay=0.01,
        warmup_ratio=0.1,
        label2id_path=args.label2id,
        use_crf=args.use_crf,
    )

    trainer.train()

    save_path = Path(args.output_dir) / "best"
    trainer.save_model(str(save_path))
    tokenizer.save_pretrained(str(save_path))


if __name__ == "__main__":
    main()
