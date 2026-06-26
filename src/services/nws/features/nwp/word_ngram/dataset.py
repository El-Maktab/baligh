"""Dataset streaming and splitting for the Word N-Gram model.

Authors:
    Akram Hany
"""

import logging
from collections.abc import Iterator
from pathlib import Path

from datasets import load_dataset

logger = logging.getLogger(__name__)


def get_eval_stream(
    dataset_name: str = "CALM/arwiki",
    split_type: str = "train",
) -> Iterator[str]:
    """Get a streaming iterator over the dataset split."""
    if dataset_name == "wiki_dump":
        logger.info(f"Streaming local Wikipedia dump: {split_type}")

        data_dir = Path("src/services/nws/data/ar_corpus")

        if not data_dir.exists():
            raise FileNotFoundError(f"Local dataset not found at {data_dir}")

        # Sort files for deterministic splits.
        all_files = sorted(list(data_dir.glob("*.txt")))

        for i, filepath in enumerate(all_files):
            modulo = i % 10
            if split_type == "train" and modulo >= 8:
                continue
            elif split_type == "val" and modulo != 8:
                continue
            elif split_type == "test" and modulo != 9:
                continue

            try:
                with open(filepath, encoding="utf-8") as f:
                    raw_text = f.read()
                    if raw_text.strip():
                        yield raw_text
            except Exception as e:
                logger.warning(f"Read failed {filepath}: {e}")
        return

    # Handle Kaggle Downloaded Corpus
    if dataset_name == "kaggle":
        logger.info(f"Streaming Kaggle corpus: {split_type}")

        data_file = Path(f"src/services/nws/data/kaggle_corpus/corpus_{split_type}.txt")

        if not data_file.exists():
            raise FileNotFoundError(f"Kaggle corpus not found at {data_file}")

        with open(data_file, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    yield line
        return

    # Handle LSTM Corpus
    if dataset_name == "lstm":
        logger.info(f"Streaming LSTM corpus: {split_type}")

        data_file = Path(f"src/services/nws/data/lstm_corpus/corpus_{split_type}.txt")

        if not data_file.exists():
            raise FileNotFoundError(f"LSTM corpus not found at {data_file}")

        with open(data_file, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    yield line
        return

    # Handle HuggingFace Datasets
    logger.info(f"Streaming HuggingFace dataset: {dataset_name} ({split_type})")
    dataset = load_dataset(dataset_name, split="train", streaming=True)

    if dataset_name == "CALM/arwiki":
        logger.info("Shuffling Wikipedia articles.")
        dataset = dataset.shuffle(seed=42, buffer_size=10_000)
    else:
        logger.info(f"Skipping shuffle: {dataset_name}")

    for i, row in enumerate(dataset):
        # Split routing.
        modulo = i % 10

        if split_type == "train" and modulo >= 8:
            continue
        elif split_type == "val" and modulo != 8:
            continue
        elif split_type == "test" and modulo != 9:
            continue

        raw_text = row.get("text", row.get("content", row.get("document", "")))
        if not raw_text:
            continue

        yield raw_text
