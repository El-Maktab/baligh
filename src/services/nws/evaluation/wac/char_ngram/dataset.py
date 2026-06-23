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


import logging

logger = logging.getLogger(__name__)

def get_eval_stream(
    dataset_name: str = "CALM/arwiki", 
    split_type: str = "train",
    limit_chars: int | None = None
) -> Iterator[str]:
    """Get a streaming iterator over the dataset split."""
    
    logger.info(f"Connecting to HuggingFace to stream: {dataset_name}")
    dataset = load_dataset(dataset_name, split="train", streaming=True)
    
    if dataset_name == "CALM/arwiki":
        logger.info("Shuffling Wikipedia articles (buffer=10000)...")
        dataset = dataset.shuffle(seed=42, buffer_size=10_000)
    else:
        logger.info(f"Skipping shuffle for {dataset_name} to guarantee instant startup.")
    
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
