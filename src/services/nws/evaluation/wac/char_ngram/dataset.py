import re
from collections.abc import Iterator

from datasets import load_dataset
from src.core.utils.arabic import normalize_arabic_surface

NON_ARABIC_RE = re.compile(r"[^\u0621-\u064a\s]")
SPACE_RE = re.compile(r"\s+")


def clean_text_for_lm(text: str) -> str:
    """Normalize text and remove non-arabic characters."""
    norm = normalize_arabic_surface(text)
    norm = NON_ARABIC_RE.sub(" ", norm)
    norm = SPACE_RE.sub(" ", norm)
    return norm.strip()


import logging

logger = logging.getLogger(__name__)


def get_eval_stream(
    dataset_name: str = "CALM/arwiki",
    split_type: str = "train",
    limit_chars: int | None = None,
) -> Iterator[str]:
    """Get a streaming iterator over the dataset split."""
    if dataset_name == "lstm":
        logger.info(f"Streaming from LSTM corpus output for {split_type} split...")
        from pathlib import Path

        current_dir = Path(__file__).resolve().parent
        while current_dir.name and not (current_dir / "pyproject.toml").exists():
            current_dir = current_dir.parent

        data_file = (
            current_dir / f"src/services/nws/data/lstm_corpus/corpus_{split_type}.txt"
        )
        if not data_file.exists():
            raise FileNotFoundError(f"LSTM corpus not found at {data_file}")

        chars_processed = 0
        with open(data_file, encoding="utf-8") as f:
            for line in f:
                raw_text = line.strip()
                if not raw_text:
                    continue
                clean_text = clean_text_for_lm(raw_text)
                if not clean_text:
                    continue
                clean_text = " " + clean_text + " "
                yield clean_text
                chars_processed += len(clean_text)
                if limit_chars is not None and chars_processed >= limit_chars:
                    break
        return

    logger.info(f"Connecting to HuggingFace to stream: {dataset_name}")
    dataset = load_dataset(dataset_name, split="train", streaming=True)

    if dataset_name == "CALM/arwiki":
        logger.info("Shuffling Wikipedia articles (buffer=10000)...")
        dataset = dataset.shuffle(seed=42, buffer_size=10_000)
    else:
        logger.info(
            f"Skipping shuffle for {dataset_name} to guarantee instant startup."
        )

    if dataset_name == "CALM/arwiki":
        if split_type == "train":
            dataset = dataset.take(100_000)
        elif split_type == "val":
            dataset = dataset.skip(100_000).take(20_000)
        elif split_type == "test":
            dataset = dataset.skip(120_000).take(20_000)
    elif dataset_name == "mohres/The_Arabic_E-Book_Corpus":
        # For the books dataset, there are only ~1,745 rows (books).
        if split_type == "train":
            dataset = dataset.take(1_500)
        elif split_type == "val":
            dataset = dataset.skip(1_500).take(100)
        elif split_type == "test":
            dataset = dataset.skip(1_600).take(145)
    else:
        raise ValueError(f"Unknown split_type: {split_type}")

    chars_processed = 0
    for row in dataset:
        # Different datasets use different column names for their main text
        raw_text = row.get("text", row.get("content", row.get("document", "")))
        if not raw_text:
            continue

        clean_text = clean_text_for_lm(raw_text)
        if not clean_text:
            continue

        clean_text = " " + clean_text + " "

        yield clean_text

        chars_processed += len(clean_text)
        if limit_chars is not None and chars_processed >= limit_chars:
            break


def generate_prefix_pairs(text: str) -> list[tuple[str, str, int]]:
    """Implements Format B: Generate (prefix, word, prefix_len) pairs.

    Includes preceding context words so the CharNGramLM can score based on context history.
    """
    words = text.split()
    pairs = []
    for i, word in enumerate(words):
        if len(word) < 2:
            continue

        context_words = words[max(0, i - 3) : i]
        context_str = " ".join(context_words) + " " if context_words else ""

        for prefix_len in range(1, len(word)):
            word_prefix = word[:prefix_len]
            full_prefix = context_str + word_prefix
            pairs.append((full_prefix, word, prefix_len))
    return pairs
