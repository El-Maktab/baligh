import argparse
import json
from pathlib import Path

from transformers import AutoTokenizer, AutoModelForTokenClassification

from src.services.gec.config import CHECKPOINT_PATH, LABEL2ID_PATH
from src.services.gec.modules.edit_tagger.training.datasets import GECTrainingDataset
from src.services.gec.modules.edit_tagger.training.trainer import build_trainer

def create_model(checkpoint, label2id):
    id2label = {v: k for k, v in label2id.items()}
    return AutoModelForTokenClassification.from_pretrained(
        checkpoint,
        num_labels=len(label2id),
        id2label=id2label,
        label2id=label2id,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", default="aubmindlab/bert-base-arabertv02")
    parser.add_argument("--train_jsonl", default=str(CHECKPOINT_PATH))
    parser.add_argument("--eval_jsonl", default=None)
    parser.add_argument("--label2id", default=str(LABEL2ID_PATH))
    parser.add_argument("--output_dir", default=str(Path(__file__).resolve().parents[2] / "data" / "edit_tagger" / "models" / "edit_tagger_v1"))
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=5e-5)
    parser.add_argument("--fp16", action="store_true")
    parser.add_argument("--max_length", type=int, default=256)
    args = parser.parse_args()

    with open(args.label2id, encoding="utf-8") as f:
        label2id = json.load(f)

    tokenizer = AutoTokenizer.from_pretrained(args.checkpoint)

    train_dataset = GECTrainingDataset(args.train_jsonl, tokenizer, label2id, max_length=args.max_length)

    eval_dataset = None
    if args.eval_jsonl:
        eval_dataset = GECTrainingDataset(args.eval_jsonl, tokenizer, label2id, max_length=args.max_length)

    model = create_model(args.checkpoint, label2id)

    trainer = build_trainer(
        model=model,
        train_dataset=train_dataset,
        tokenizer=tokenizer,
        eval_dataset=eval_dataset,
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        fp16=args.fp16,
        label2id_path=args.label2id,
    )

    trainer.train()

    save_path = Path(args.output_dir) / "best"
    trainer.save_model(str(save_path))
    tokenizer.save_pretrained(str(save_path))


if __name__ == "__main__":
    main()
 