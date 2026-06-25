"""Dataset streaming and splitting for the Word N-Gram model.

Implements an 80/10/10 modulo router to safely split massive datasets
while maintaining streaming properties (O(1) memory).
"""

import logging
from typing import Iterator
from datasets import load_dataset
from pathlib import Path

logger = logging.getLogger(__name__)

def get_eval_stream(
    dataset_name: str = "CALM/arwiki", 
    split_type: str = "train",
) -> Iterator[str]:
    """Get a streaming iterator over the dataset split.
    
    Uses modulo routing (row_index % 10) to enforce strict splits:
    - Train (80%): 0, 1, 2, 3, 4, 5, 6, 7
    - Validation (10%): 8
    - Test (10%): 9
    """
    
    # Handle Local Wikipedia Dump
    if dataset_name == "wiki_dump":
        logger.info(f"Streaming from local Wikipedia dump for {split_type} split...")
        
        # Traverse up to project root to find data dir correctly regardless of where script is run
        current_dir = Path(__file__).resolve().parent
        while current_dir.name and not (current_dir / 'pyproject.toml').exists():
            current_dir = current_dir.parent
            
        data_dir = current_dir / "src/services/nws/data/ar_corpus"
        
        if not data_dir.exists():
            raise FileNotFoundError(f"Local dataset not found at {data_dir}")
            
        # Sort files to guarantee deterministic splits
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
                with open(filepath, "r", encoding="utf-8") as f:
                    raw_text = f.read()
                    if raw_text.strip():
                        yield raw_text
            except Exception as e:
                logger.warning(f"Failed to read {filepath}: {e}")
        return

    # Handle Kaggle Downloaded Corpus
    if dataset_name == "kaggle":
        logger.info(f"Streaming from Kaggle corpus output for {split_type} split...")
        
        current_dir = Path(__file__).resolve().parent
        while current_dir.name and not (current_dir / 'pyproject.toml').exists():
            current_dir = current_dir.parent
            
        data_file = current_dir / f"src/services/nws/data/kaggle_corpus/corpus_{split_type}.txt"
        
        if not data_file.exists():
            raise FileNotFoundError(f"Kaggle corpus not found at {data_file}")
            
        with open(data_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    yield line
        return

    # Handle LSTM Corpus
    if dataset_name == "lstm":
        logger.info(f"Streaming from LSTM corpus output for {split_type} split...")
        
        current_dir = Path(__file__).resolve().parent
        while current_dir.name and not (current_dir / 'pyproject.toml').exists():
            current_dir = current_dir.parent
            
        data_file = current_dir / f"src/services/nws/data/lstm_corpus/corpus_{split_type}.txt"
        
        if not data_file.exists():
            raise FileNotFoundError(f"LSTM corpus not found at {data_file}")
            
        with open(data_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    yield line
        return

    # Handle HuggingFace Datasets
    logger.info(f"Connecting to HuggingFace to stream: {dataset_name} for {split_type} split...")
    dataset = load_dataset(dataset_name, split="train", streaming=True)
    
    if dataset_name == "CALM/arwiki":
        logger.info("Shuffling Wikipedia articles (buffer=10000)...")
        dataset = dataset.shuffle(seed=42, buffer_size=10_000)
    else:
        logger.info(f"Skipping shuffle for {dataset_name} to guarantee instant startup.")
        
    for i, row in enumerate(dataset):
        # Modulo Routing
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
