"""Training script for the CRF‑enhanced GEC edit‑tagger.

This script demonstrates a two‑phase training strategy:
1. **CRF‑only fine‑tuning** – the BERT encoder is frozen while the CRF layer learns
   transition scores.
2. **Full fine‑tuning** – the entire model (BERT + classifier + CRF) is trained.

The script is intentionally minimal; it re‑uses the existing ``build_trainer``
function and the ``load_model_with_optional_crf`` utility.
"""

import argparse
import json
from pathlib import Path
import torch

from transformers import AutoTokenizer
from torch.utils.data import DataLoader
from transformers import DataCollatorForTokenClassification

# Project imports
from src.services.gec.config import (
    PROCESSED_DATA_DIR,
    LABEL2ID_PATH,
    MAX_LENGTH,
    BATCH_SIZE,
)
from src.services.gec.modules.edit_tagger.training.datasets import GECTrainingDataset
from src.services.gec.modules.edit_tagger.training.trainer import build_trainer
from src.services.gec.modules.edit_tagger.crf.model_loader import (
    load_base_model,
    wrap_with_crf,
    load_model_with_optional_crf,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train GEC edit‑tagger with optional CRF layer")
    parser.add_argument("--checkpoint", default="aubmindlab/bert-base-arabertv02", help="Base AraBERT checkpoint identifier")
    parser.add_argument("--train-jsonl", default=str(PROCESSED_DATA_DIR / "train_tokens_labels.jsonl"), help="Path to training JSONL file")
    parser.add_argument("--label2id", default=str(LABEL2ID_PATH), help="Path to label2id mapping JSON")
    parser.add_argument("--output-dir", default=str(Path(__file__).resolve().parents[2] / "data" / "edit_tagger" / "models" / "edit_tagger_crf_v1"), help="Directory to save the trained model")
    parser.add_argument("--epochs", type=int, default=10, help="Number of training epochs for each phase")
    parser.add_argument("--lr", type=float, default=5e-5, help="Learning rate for full fine‑tuning phase")
    parser.add_argument("--crf-lr", type=float, default=1e-3, help="Learning rate for CRF‑only phase (higher to speed up transition learning)")
    parser.add_argument("--freeze-bert", action="store_true", help="Freeze BERT encoder during CRF‑only phase")
    args = parser.parse_args()

    # ---------------------------------------------------------------------
    # Load label vocabulary
    # ---------------------------------------------------------------------
    with open(args.label2id, encoding="utf-8") as f:
        label2id = json.load(f)
    num_labels = len(label2id)

    # ---------------------------------------------------------------------
    # Build tokenizer
    # ---------------------------------------------------------------------
    tokenizer = AutoTokenizer.from_pretrained(args.checkpoint)

    # ---------------------------------------------------------------------
    # Prepare training dataset
    # ---------------------------------------------------------------------
    train_dataset = GECTrainingDataset(
        jsonl_path=args.train_jsonl,
        tokenizer=tokenizer,
        label2id=label2id,
        max_length=MAX_LENGTH,
    )

    data_collator = DataCollatorForTokenClassification(tokenizer=tokenizer)
    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        collate_fn=data_collator,
        shuffle=True,
    )

    # ---------------------------------------------------------------------
    # Phase 1 – CRF‑only training (optional freezing of BERT)
    # ---------------------------------------------------------------------
    base_model = load_base_model(args.checkpoint, num_labels=num_labels, label2id=label2id)
    if args.freeze_bert:
        for param in base_model.bert.parameters():
            param.requires_grad = False

    crf_model = wrap_with_crf(base_model, num_labels=num_labels, label2id=label2id)

    # Trainer for CRF‑only phase – we rely on the same ``build_trainer``. The
    # trainer will compute loss via the CRF wrapper's forward method.
    trainer_crf = build_trainer(
        model=crf_model,
        train_dataset=train_dataset,
        tokenizer=tokenizer,
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        weight_decay=0.0,
        warmup_ratio=0.1,
        label2id_path=args.label2id,
        use_crf=True,
    )
    print("Starting CRF‑only fine‑tuning (BERT frozen = {} )".format(args.freeze_bert))
    trainer_crf.train()

    # ---------------------------------------------------------------------
    # Phase 2 – full fine‑tuning (unfreeze BERT)
    # ---------------------------------------------------------------------
    # Unfreeze all parameters
    for param in crf_model.parameters():
        param.requires_grad = True

    trainer_full = build_trainer(
        model=crf_model,
        train_dataset=train_dataset,
        tokenizer=tokenizer,
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        weight_decay=0.01,
        warmup_ratio=0.1,
        label2id_path=args.label2id,
        use_crf=True,
    )
    print("Starting full fine‑tuning of BERT + classifier + CRF")
    trainer_full.train()

    # Save final model and tokenizer
    save_path = Path(args.output_dir) / "best"
    trainer_full.save_model(str(save_path))
    tokenizer.save_pretrained(str(save_path))
    print(f"Model saved to {save_path}")


if __name__ == "__main__":
    main()
