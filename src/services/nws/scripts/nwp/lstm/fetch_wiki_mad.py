#!/usr/bin/env python3
import os
import re
import sys
import gc
import random
import shutil
from pathlib import Path
from collections import Counter
from typing import List, Optional

from datasets import load_dataset
from tqdm.auto import tqdm

SEED = 42
random.seed(SEED)

BASE_DIR = Path("src/services/nws/data/lstm_corpus")
BASE_DIR.mkdir(parents=True, exist_ok=True)

# ── Hyperparameters ──────────────────────────────
CFG = {
    "wiki_max_docs":     15_000,
    "mad_max_docs":      15_000,
    "val_frac":          0.05,
    "test_frac":         0.05,
}

# ── Normalization Regex ──────────────────────────
TASHKEEL      = re.compile(r'[\u064B-\u065F\u0670]')
TATWEEL       = re.compile(r'\u0640')
ALIF_MAP = str.maketrans({
    '\u0622': '\u0627', '\u0623': '\u0627', '\u0625': '\u0627', '\u0671': '\u0627',
})
YAA_MAP = str.maketrans({
    '\u0649': '\u064A', '\uFEEF': '\u064A', '\uFEF0': '\u064A', '\uFEF1': '\u064A',
    '\uFEF2': '\u064A', '\uFEF3': '\u064A', '\uFEF4': '\u064A',
})
HAA_MAP = str.maketrans({'\u0629': '\u0647'})

def normalise_arabic(text: str) -> str:
    text = TASHKEEL.sub('', text)
    text = TATWEEL.sub('', text)
    text = text.translate(ALIF_MAP)
    text = text.translate(YAA_MAP)
    text = text.translate(HAA_MAP)
    text = re.sub(r'[^\u0600-\u06FF\u0750-\u077F\s0-9\.,!?؟\-]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def inject_sentence_boundaries(text: str) -> str:
    sentences = re.split(r'[.!?؟\n]+', text)
    pieces = []
    for sent in sentences:
        sent = sent.strip()
        if len(sent.split()) >= 3:
            pieces.append(f"<s> {sent} </s>")
    return '\n'.join(pieces)

def is_mostly_arabic(text: str, threshold: float = 0.60) -> bool:
    if not text:
        return False
    arabic_count = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
    return arabic_count / len(text) >= threshold

def clean_doc(raw: str) -> Optional[str]:
    if not raw or len(raw) < 50:
        return None
    if not is_mostly_arabic(raw):
        return None
    text = normalise_arabic(raw)
    if len(text) < 30:
        return None
    text = inject_sentence_boundaries(text)
    return text if text.strip() else None

def download_wikipedia_ar(max_docs: int) -> List[str]:
    print(f"\n[+] Downloading Arabic Wikipedia (max {max_docs:,} docs)...")
    texts = []
    ds = load_dataset("wikimedia/wikipedia", "20231101.ar", split="train", streaming=True)
    for i, row in enumerate(tqdm(ds, total=max_docs, desc="Wikipedia-ar")):
        if i >= max_docs: break
        txt = row.get("text", "").strip()
        if len(txt) > 100: texts.append(txt)
    return texts

def download_mad_ar(max_docs: int) -> List[str]:
    print(f"\n[+] Downloading Mixed Arabic Dataset (max {max_docs:,} docs)...")
    texts = []
    ds = load_dataset("M-A-D/Mixed-Arabic-Dataset-Main", split="train", streaming=True)
    for i, row in enumerate(tqdm(ds, total=max_docs, desc="MAD-ar")):
        if i >= max_docs: break
        txt = row.get("text", row.get("content", "")).strip()
        if len(txt) > 100: texts.append(txt)
    return texts

def build_corpus():
    wiki_docs  = download_wikipedia_ar(CFG["wiki_max_docs"])
    mad_docs   = download_mad_ar(CFG["mad_max_docs"])

    all_docs = wiki_docs + mad_docs
    print(f"\n[+] Total raw docs: {len(all_docs):,}")

    cleaned = []
    for doc in tqdm(all_docs, desc="Cleaning"):
        result = clean_doc(doc)
        if result: cleaned.append(result)

    print("[+] Deduplicating at paragraph level...")
    para_counts = Counter()
    deduped = []
    for doc in tqdm(cleaned, desc="Dedup pass 1"):
        for para in doc.split('\n'):
            para_counts[para.strip()] += 1

    for doc in tqdm(cleaned, desc="Dedup pass 2"):
        paras = [p for p in doc.split('\n') if para_counts[p.strip()] <= 3]
        if paras: deduped.append('\n'.join(paras))
    
    random.shuffle(deduped)

    n = len(deduped)
    n_val  = max(1, int(n * CFG["val_frac"]))
    n_test = max(1, int(n * CFG["test_frac"]))
    n_train = n - n_val - n_test

    splits = {
        "train": deduped[:n_train],
        "val":   deduped[n_train:n_train + n_val],
        "test":  deduped[n_train + n_val:],
    }

    total_words = 0
    for split_name, docs in splits.items():
        out_path = BASE_DIR / f"corpus_{split_name}.txt"
        with open(out_path, 'w', encoding='utf-8') as f:
            for doc in docs:
                f.write(doc + '\n')
        words = sum(len(d.split()) for d in docs)
        total_words += words
        print(f"  {split_name}: {len(docs):,} docs, ~{words/1e6:.2f}M words → {out_path.name}")

if __name__ == "__main__":
    build_corpus()
