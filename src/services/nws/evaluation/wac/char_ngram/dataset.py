import re
import sys
from typing import Iterator

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


def get_eval_stream(
    dataset_name: str = "CALM/arwiki", 
    split_type: str = "train",
    limit_chars: int | None = None
) -> Iterator[str]:
    """Get a streaming iterator over the dataset split.
    
    Implements Stage 1 from the evaluation pipeline:
    - Shuffles the stream with a buffer of 10,000 to break topic clustering.
    - Partitions the data safely into train/val/test using skip/take.
    
    Since we are working with a massive dataset (15.4M rows), we will use fixed
    row counts for the splits:
    - Train: First 100,000 rows
    - Validation: Next 20,000 rows
    - Test: Next 20,000 rows
    """
    dataset = load_dataset(dataset_name, split="train", streaming=True)
    
    # Shuffle before splitting
    dataset = dataset.shuffle(seed=42, buffer_size=10_000)
    
    if split_type == "train":
        dataset = dataset.take(100_000)
    elif split_type == "val":
        dataset = dataset.skip(100_000).take(20_000)
    elif split_type == "test":
        dataset = dataset.skip(120_000).take(20_000)
    else:
        raise ValueError(f"Unknown split_type: {split_type}")
        
    chars_processed = 0
    for row in dataset:
        raw_text = row.get("text", "")
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


def generate_prefix_pairs(text: str) -> list[tuple[str, str]]:
    """Implements Format B: Generate (prefix, word) pairs.
    
    For every word, generates all prefix lengths from 1 up to (word length - 1).
    """
    words = text.split()
    pairs = []
    for word in words:
        if len(word) < 2:
            continue
        for prefix_len in range(1, len(word)):
            prefix = word[:prefix_len]
            pairs.append((prefix, word))
    return pairs
