# ============================================================
#  ARABIC KEYBOARD AUTOCOMPLETE — BPE + LSTM LANGUAGE MODEL
#  Single-file Kaggle notebook (GPU P100/T4 recommended)
#
#  SECTIONS:
#   0. Imports & Configuration
#   1. Dataset Download & Extraction
#   2. Arabic Text Cleaning & Normalisation
#   3. Corpus Assembly & Train/Val/Test Split
#   4. BPE Tokeniser Training (SentencePiece)
#   5. Dataset Class & DataLoaders
#   6. LSTM Language Model Architecture
#   7. Training Loop
#   8. Evaluation (Perplexity + Top-K Accuracy)
#   9. Hybrid Inference (LSTM + Kneser-Ney blending)
#  10. ONNX Export & INT8 Quantisation
#  11. Quick Demo
# ============================================================


# ╔══════════════════════════════════════════════════════════╗
# ║  SECTION 0 — IMPORTS & CONFIGURATION                    ║
# ╚══════════════════════════════════════════════════════════╝

import gc
import json
import math
import os
import random
import re
import shutil
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

# Dependencies must be installed manually via uv since we are running locally
# (sentencepiece, datasets, tqdm, torch)
import sentencepiece as spm
import torch
import torch.nn as nn
import torch.nn.functional as F
from datasets import load_dataset
from torch.optim import AdamW
from torch.optim.lr_scheduler import OneCycleLR
from torch.utils.data import DataLoader, Dataset
from tqdm.auto import tqdm

# ── Reproducibility ─────────────────────────────────────────
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
torch.cuda.manual_seed_all(SEED)

# ── Paths ────────────────────────────────────────────────────
# Changed from /kaggle/working to a local directory inside the project
BASE_DIR = Path("src/services/nws/data/lstm_working_dir")
CORPUS_DIR = BASE_DIR / "corpus"
CORPUS_FILE = BASE_DIR / "corpus_cleaned.txt"
SPM_PREFIX = str(BASE_DIR / "arabic_bpe")
CHECKPOINT_DIR = BASE_DIR / "checkpoints"
ONNX_PATH = BASE_DIR / "arabic_lm.onnx"
ONNX_INT8_PATH = BASE_DIR / "arabic_lm_int8.onnx"

for d in [CORPUS_DIR, CHECKPOINT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── Hyperparameters (edit here) ──────────────────────────────
CFG = {
    # Corpus (Reduced heavily to ensure we stay under ~10 million words locally)
    "wiki_max_docs": 15_000,  # ~4.5M words
    "oscar_max_chars": 0,  # Disabled to speed up local testing
    "mad_max_docs": 15_000,  # ~4.5M words
    # BPE
    "vocab_size": 12_000,
    # Model
    "embed_dim": 256,
    "hidden_size": 512,
    "num_layers": 2,
    "dropout": 0.30,
    "seq_len": 64,  # training sequence length (subword tokens)
    # Training
    "batch_size": 128,  # good for 8 GB VRAM; lower to 64 if OOM
    "epochs": 20,
    "peak_lr": 3e-3,
    "weight_decay": 1e-2,
    "grad_clip": 1.0,
    "warmup_pct": 0.05,
    "patience": 3,  # early stopping patience (epochs)
    "val_frac": 0.05,
    "test_frac": 0.05,
    # Inference
    "infer_ctx_len": 32,  # tokens of context at inference time
    "alpha_high": 0.75,  # neural weight when confident
    "alpha_low": 0.50,  # neural weight when uncertain
    "confidence_thresh": 0.35,
    "top_k": 5,
}

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"[0] Device: {DEVICE}")
print(
    f"[0] Config: vocab={CFG['vocab_size']}, hidden={CFG['hidden_size']}, "
    f"layers={CFG['num_layers']}, seq_len={CFG['seq_len']}"
)


# ╔══════════════════════════════════════════════════════════╗
# ║  SECTION 1 — DATASET DOWNLOAD & EXTRACTION             ║
# ╚══════════════════════════════════════════════════════════╝
#
#  We pull from three public, no-auth-required sources:
#    A) wikimedia/wikipedia  — Arabic Wikipedia (20231101.ar)
#    B) oscar-corpus/oscar   — OSCAR Arabic (unshuffled_deduplicated_ar)
#    C) M-A-D/Mixed-Arabic-Dataset-Main — books, news, stories, mixed
#
#  All three are freely accessible on Hugging Face without a token.
# ──────────────────────────────────────────────────────────────


def download_wikipedia_ar(max_docs: int) -> list[str]:
    """Stream Arabic Wikipedia, return list of article texts."""
    print(f"\n[1] Downloading Arabic Wikipedia (max {max_docs:,} docs)...")
    texts = []
    try:
        ds = load_dataset(
            "wikimedia/wikipedia",
            "20231101.ar",
            split="train",
            streaming=True,
        )
        for i, row in enumerate(tqdm(ds, total=max_docs, desc="  Wikipedia-ar")):
            if i >= max_docs:
                break
            txt = row.get("text", "").strip()
            if len(txt) > 100:  # skip stubs
                texts.append(txt)
    except Exception as e:
        print(f"  [WARN] Wikipedia download error: {e}")
    print(f"  -> {len(texts):,} Wikipedia articles collected")
    return texts


def download_oscar_ar(max_chars: int) -> list[str]:
    """Stream OSCAR Arabic until we have enough characters."""
    print(f"\n[1] Downloading OSCAR Arabic (target ~{max_chars / 1e6:.0f}M chars)...")
    texts = []
    total_chars = 0
    try:
        # OSCAR is a gated dataset. You must add your HuggingFace token to Kaggle Secrets
        # and load it via os.environ.get("HF_TOKEN")
        token = os.environ.get("HF_TOKEN")
        if not token:
            print(
                "  [WARN] Skipping OSCAR: 'HF_TOKEN' environment variable is missing. (OSCAR is gated)"
            )
            return []

        ds = load_dataset(
            "oscar-corpus/oscar",
            "unshuffled_deduplicated_ar",
            split="train",
            streaming=True,
            token=token,
        )
        pbar = tqdm(desc="  OSCAR-ar", unit=" chars", unit_scale=True)
        for row in ds:
            txt = row.get("text", "").strip()
            if len(txt) > 50:
                texts.append(txt)
                total_chars += len(txt)
                pbar.update(len(txt))
            if total_chars >= max_chars:
                break
        pbar.close()
    except Exception as e:
        print(f"  [WARN] OSCAR download error: {e}")
    print(f"  -> {len(texts):,} OSCAR docs, {total_chars / 1e6:.1f}M chars")
    return texts


def download_mad_ar(max_docs: int) -> list[str]:
    """Load Mixed Arabic Dataset (books, news, Wikipedia mix, stories)."""
    print(f"\n[1] Downloading Mixed Arabic Dataset (max {max_docs:,} docs)...")
    texts = []
    try:
        ds = load_dataset(
            "M-A-D/Mixed-Arabic-Dataset-Main",
            split="train",
            streaming=True,
        )
        for i, row in enumerate(tqdm(ds, total=max_docs, desc="  MAD-ar")):
            if i >= max_docs:
                break
            # MAD stores text in a 'text' column
            txt = row.get("text", row.get("content", "")).strip()
            if len(txt) > 100:
                texts.append(txt)
    except Exception as e:
        print(f"  [WARN] MAD download error: {e}")
    print(f"  -> {len(texts):,} MAD docs collected")
    return texts


# ╔══════════════════════════════════════════════════════════╗
# ║  SECTION 2 — ARABIC TEXT CLEANING & NORMALISATION       ║
# ╚══════════════════════════════════════════════════════════╝

# Arabic Unicode ranges & sets
ARABIC_CHARS = re.compile(r"[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]")
TASHKEEL = re.compile(r"[\u064B-\u065F\u0670]")  # diacritics
TATWEEL = re.compile(r"\u0640")  # kashida
PUNCTUATION = re.compile(r"[.!?؟।\n]")

# Alif variants → bare Alif
ALIF_MAP = str.maketrans(
    {
        "\u0622": "\u0627",  # Alif Madda
        "\u0623": "\u0627",  # Alif with Hamza above
        "\u0625": "\u0627",  # Alif with Hamza below
        "\u0671": "\u0627",  # Alif Wasla
    }
)

# Yaa variants → bare Yaa
YAA_MAP = str.maketrans(
    {
        "\u0649": "\u064a",  # Alif Maqsura → Yaa
        "\ufeef": "\u064a",  # presentation form
        "\ufef0": "\u064a",
        "\ufef1": "\u064a",
        "\ufef2": "\u064a",
        "\ufef3": "\u064a",
        "\ufef4": "\u064a",
    }
)

# Haa variants → standard Haa (unify Taa Marbuta)
HAA_MAP = str.maketrans(
    {
        "\u0629": "\u0647",  # Taa Marbuta → Haa
    }
)


def normalise_arabic(text: str) -> str:
    """Full surface normalisation pipeline:
    1. Strip Tashkeel (diacritics)
    2. Remove Tatweel (decorative elongation)
    3. Unify Alif variants
    4. Unify Yaa variants
    5. Unify Taa Marbuta → Haa
    6. Remove non-Arabic/non-space noise
    7. Collapse multiple spaces
    """
    text = TASHKEEL.sub("", text)
    text = TATWEEL.sub("", text)
    text = text.translate(ALIF_MAP)
    text = text.translate(YAA_MAP)
    text = text.translate(HAA_MAP)
    # Keep Arabic letters, spaces, basic punctuation, Western digits
    text = re.sub(r"[^\u0600-\u06FF\u0750-\u077F\s0-9\.,!?؟\-]", " ", text)
    # Normalise whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def inject_sentence_boundaries(text: str) -> str:
    """Split on sentence-ending punctuation and wrap each sentence
    with <s> ... </s> boundary tokens, matching your n-gram model's
    existing tokenisation convention.
    """
    sentences = re.split(r"[.!?؟\n]+", text)
    pieces = []
    for sent in sentences:
        sent = sent.strip()
        if len(sent.split()) >= 3:  # skip very short fragments
            pieces.append(f"<s> {sent} </s>")
    return "\n".join(pieces)


def is_mostly_arabic(text: str, threshold: float = 0.60) -> bool:
    """Return True if at least `threshold` fraction of chars are Arabic."""
    if not text:
        return False
    arabic_count = sum(1 for c in text if "\u0600" <= c <= "\u06ff")
    return arabic_count / len(text) >= threshold


def clean_doc(raw: str) -> str | None:
    """Full cleaning pipeline for one document.
    Returns None if the document should be discarded.
    """
    if not raw or len(raw) < 50:
        return None
    if not is_mostly_arabic(raw):
        return None

    text = normalise_arabic(raw)
    if len(text) < 30:
        return None

    text = inject_sentence_boundaries(text)
    return text if text.strip() else None


# ╔══════════════════════════════════════════════════════════╗
# ║  SECTION 3 — CORPUS ASSEMBLY & SPLITS                   ║
# ╚══════════════════════════════════════════════════════════╝


def build_corpus():
    """Download all datasets, clean, deduplicate, split, and write to disk."""
    if CORPUS_FILE.exists() and CORPUS_FILE.stat().st_size > 1_000_000:
        print(
            f"\n[3] Corpus already exists ({CORPUS_FILE.stat().st_size / 1e6:.1f} MB). Skipping build."
        )
        return

    # ── 1. Download ─────────────────────────────────────────
    wiki_docs = download_wikipedia_ar(CFG["wiki_max_docs"])
    oscar_docs = download_oscar_ar(CFG["oscar_max_chars"])
    mad_docs = download_mad_ar(CFG["mad_max_docs"])

    all_docs = wiki_docs + oscar_docs + mad_docs
    print(f"\n[3] Total raw docs: {len(all_docs):,}")
    del wiki_docs, oscar_docs, mad_docs
    gc.collect()

    # ── 2. Clean ─────────────────────────────────────────────
    print("[3] Cleaning documents...")
    cleaned = []
    for doc in tqdm(all_docs, desc="  Cleaning"):
        result = clean_doc(doc)
        if result:
            cleaned.append(result)
    del all_docs
    gc.collect()
    print(f"  -> {len(cleaned):,} docs after cleaning")

    # ── 3. Paragraph-level deduplication ─────────────────────
    print("[3] Deduplicating at paragraph level...")
    para_counts: Counter = Counter()
    deduped = []
    for doc in tqdm(cleaned, desc="  Dedup pass 1"):
        for para in doc.split("\n"):
            para_counts[para.strip()] += 1

    for doc in tqdm(cleaned, desc="  Dedup pass 2"):
        paras = [p for p in doc.split("\n") if para_counts[p.strip()] <= 3]
        if paras:
            deduped.append("\n".join(paras))
    del cleaned, para_counts
    gc.collect()
    print(f"  -> {len(deduped):,} docs after deduplication")

    # ── 4. Shuffle ───────────────────────────────────────────
    random.shuffle(deduped)

    # ── 5. Split ─────────────────────────────────────────────
    n = len(deduped)
    n_val = max(1, int(n * CFG["val_frac"]))
    n_test = max(1, int(n * CFG["test_frac"]))
    n_train = n - n_val - n_test

    splits = {
        "train": deduped[:n_train],
        "val": deduped[n_train : n_train + n_val],
        "test": deduped[n_train + n_val :],
    }
    del deduped
    gc.collect()

    # ── 6. Write to disk ──────────────────────────────────────
    total_words = 0
    for split_name, docs in splits.items():
        out_path = BASE_DIR / f"corpus_{split_name}.txt"
        with open(out_path, "w", encoding="utf-8") as f:
            for doc in docs:
                f.write(doc + "\n")
        words = sum(len(d.split()) for d in docs)
        total_words += words
        print(
            f"  {split_name}: {len(docs):,} docs, ~{words / 1e6:.2f}M words → {out_path.name}"
        )

    # Combined file for SentencePiece training (train only)
    shutil.copy(BASE_DIR / "corpus_train.txt", CORPUS_FILE)
    print(
        f"\n[3] Corpus ready. Total words across all splits: ~{total_words / 1e6:.1f}M"
    )


build_corpus()


# ╔══════════════════════════════════════════════════════════╗
# ║  SECTION 4 — BPE TOKENISER TRAINING (SentencePiece)    ║
# ╚══════════════════════════════════════════════════════════╝

SPM_MODEL = SPM_PREFIX + ".model"


def train_sentencepiece():
    if Path(SPM_MODEL).exists():
        print("\n[4] SentencePiece model already exists. Skipping training.")
        return

    print(f"\n[4] Training SentencePiece BPE (vocab={CFG['vocab_size']})...")
    spm.SentencePieceTrainer.train(
        input=str(CORPUS_FILE),
        model_prefix=SPM_PREFIX,
        vocab_size=CFG["vocab_size"],
        character_coverage=0.9999,  # covers all Arabic Unicode chars
        model_type="bpe",
        pad_id=0,  # <pad>
        unk_id=1,  # <unk>
        bos_id=2,  # <s>  — matches your n-gram boundaries
        eos_id=3,  # </s>
        input_sentence_size=5_000_000,
        shuffle_input_sentence=True,
        normalization_rule_name="nfkc",
        num_threads=os.cpu_count() or 4,
        train_extremely_large_corpus=False,
    )
    sp = spm.SentencePieceProcessor(model_file=SPM_MODEL)
    print(f"  -> Done. Vocab size: {sp.vocab_size()}")
    print(f"  -> Example: 'يكتبون' => {sp.encode('يكتبون', out_type=str)}")


train_sentencepiece()

# Load the tokeniser globally
SP = spm.SentencePieceProcessor(model_file=SPM_MODEL)
VOCAB_SIZE = SP.vocab_size()
PAD_ID, UNK_ID, BOS_ID, EOS_ID = 0, 1, 2, 3
print(f"\n[4] Tokeniser loaded. Vocab size: {VOCAB_SIZE}")


# ╔══════════════════════════════════════════════════════════╗
# ║  SECTION 5 — DATASET CLASS & DATALOADERS               ║
# ╚══════════════════════════════════════════════════════════╝


class ArabicLMDataset(Dataset):
    """Reads a corpus text file, tokenises with SentencePiece, and serves
    (input_ids, target_ids) pairs of length `seq_len`.

    Targets are input shifted by 1 (next-token prediction).
    """

    def __init__(
        self,
        corpus_path: str,
        sp: spm.SentencePieceProcessor,
        seq_len: int,
        max_tokens: int | None = None,
    ):
        self.seq_len = seq_len
        self.sp = sp

        print(f"  Encoding {corpus_path}...")
        token_ids: list[int] = []

        with open(corpus_path, encoding="utf-8") as f:
            for line in tqdm(f, desc="  Tokenising", leave=False):
                line = line.strip()
                if line:
                    ids = sp.encode(line, out_type=int)
                    token_ids.extend(ids)
                    if max_tokens and len(token_ids) >= max_tokens:
                        token_ids = token_ids[:max_tokens]
                        break

        self.data = torch.tensor(token_ids, dtype=torch.long)
        # Number of complete non-overlapping windows
        self.n_windows = (len(self.data) - 1) // seq_len
        print(f"  -> {len(token_ids):,} tokens, {self.n_windows:,} windows")

    def __len__(self):
        return self.n_windows

    def __getitem__(self, idx: int):
        start = idx * self.seq_len
        x = self.data[start : start + self.seq_len]
        y = self.data[start + 1 : start + self.seq_len + 1]
        # Pad if the last window is short
        if len(x) < self.seq_len:
            pad_len = self.seq_len - len(x)
            x = F.pad(x, (0, pad_len), value=PAD_ID)
            y = F.pad(y, (0, pad_len), value=PAD_ID)
        return x, y


def make_dataloaders(batch_size: int, seq_len: int):
    print("\n[5] Building DataLoaders...")
    train_ds = ArabicLMDataset(str(BASE_DIR / "corpus_train.txt"), SP, seq_len)
    val_ds = ArabicLMDataset(str(BASE_DIR / "corpus_val.txt"), SP, seq_len)
    test_ds = ArabicLMDataset(str(BASE_DIR / "corpus_test.txt"), SP, seq_len)

    train_loader = DataLoader(
        train_ds,
        batch_size=batch_size,
        shuffle=True,
        num_workers=2,
        pin_memory=True,
        drop_last=True,
    )
    val_loader = DataLoader(
        val_ds, batch_size=batch_size, shuffle=False, num_workers=2, pin_memory=True
    )
    test_loader = DataLoader(
        test_ds, batch_size=batch_size, shuffle=False, num_workers=2, pin_memory=True
    )

    print(
        f"  Train batches: {len(train_loader):,}  |  "
        f"Val batches: {len(val_loader):,}  |  "
        f"Test batches: {len(test_loader):,}"
    )
    return train_loader, val_loader, test_loader


# ╔══════════════════════════════════════════════════════════╗
# ║  SECTION 6 — LSTM LANGUAGE MODEL ARCHITECTURE          ║
# ╚══════════════════════════════════════════════════════════╝


class ArabicLSTMLM(nn.Module):
    """2-layer LSTM Language Model for Arabic autocomplete.

    Architecture:
      Embedding(vocab, embed_dim)
        ↓  dropout
      LSTM(embed_dim → hidden, num_layers=2)
        ↓  dropout
      Linear(hidden → vocab)   ← weights TIED to embedding matrix

    Weight tying: embedding.weight == output_projection.weight^T
    This saves ~3M parameters and consistently improves perplexity.
    """

    def __init__(
        self,
        vocab_size: int,
        embed_dim: int,
        hidden_size: int,
        num_layers: int,
        dropout: float,
    ):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.embed_dim = embed_dim

        # ── Embedding ─────────────────────────────────────────
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=PAD_ID)
        nn.init.uniform_(self.embedding.weight, -0.1, 0.1)
        self.embedding.weight.data[PAD_ID].fill_(0)  # pad stays zero

        # ── LSTM ──────────────────────────────────────────────
        # dropout between LSTM layers is set here; PyTorch applies it
        # between layers 1→2 automatically (not after the last layer)
        self.lstm = nn.LSTM(
            input_size=embed_dim,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0.0,
            batch_first=True,
        )

        # ── Output projection ─────────────────────────────────
        # Linear with NO bias (standard for tied-weight LMs)
        self.output_proj = nn.Linear(hidden_size, vocab_size, bias=False)

        # ── Weight tying ──────────────────────────────────────
        # Project embedding from embed_dim to hidden_size if they differ.
        # When embed_dim == hidden_size we tie directly; otherwise we add
        # a small projection so the tying still works.
        if embed_dim == hidden_size:
            self.output_proj.weight = self.embedding.weight
            self.pre_output_proj = None
        else:
            # Project hidden → embed_dim, then tie to embedding
            self.pre_output_proj = nn.Linear(hidden_size, embed_dim, bias=False)
            self.output_proj.weight = self.embedding.weight

        # ── Dropout layers ────────────────────────────────────
        self.drop = nn.Dropout(dropout)

    def forward(
        self, input_ids: torch.Tensor, hidden: tuple | None = None
    ) -> tuple[torch.Tensor, tuple]:
        """Args:
            input_ids : (batch, seq_len)  integer token IDs
            hidden    : optional (h_0, c_0) tuple from previous step

        Returns:
            logits : (batch, seq_len, vocab_size)
            hidden : updated (h_n, c_n) for stateful inference
        """
        # Embed + dropout
        x = self.drop(self.embedding(input_ids))  # (B, T, E)

        # LSTM
        x, hidden = self.lstm(x, hidden)  # (B, T, H)

        # Dropout before projection
        x = self.drop(x)

        # Optional pre-projection (when embed_dim != hidden_size)
        if self.pre_output_proj is not None:
            x = self.pre_output_proj(x)  # (B, T, E)

        # Output logits
        logits = self.output_proj(x)  # (B, T, V)
        return logits, hidden

    def init_hidden(self, batch_size: int) -> tuple[torch.Tensor, torch.Tensor]:
        """Return zeroed (h_0, c_0) on the correct device."""
        h = torch.zeros(
            self.num_layers,
            batch_size,
            self.hidden_size,
            device=next(self.parameters()).device,
        )
        c = torch.zeros_like(h)
        return (h, c)


def count_parameters(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


# ╔══════════════════════════════════════════════════════════╗
# ║  SECTION 7 — TRAINING LOOP                             ║
# ╚══════════════════════════════════════════════════════════╝


def train_epoch(model, loader, criterion, optimiser, scheduler, grad_clip):
    model.train()
    total_loss = 0.0
    total_tokens = 0
    hidden = None

    pbar = tqdm(loader, desc="  Train", leave=False)
    for batch_idx, (x, y) in enumerate(pbar):
        x, y = x.to(DEVICE), y.to(DEVICE)
        batch_size = x.size(0)

        # Detach hidden state between batches (TBPTT)
        if hidden is not None:
            hidden = (hidden[0].detach(), hidden[1].detach())
        else:
            hidden = model.init_hidden(batch_size)

        # Handle batch size changes at epoch boundaries
        if hidden[0].size(1) != batch_size:
            hidden = model.init_hidden(batch_size)

        # Forward
        logits, hidden = model(x, hidden)  # (B, T, V)

        # Loss — reshape for CrossEntropyLoss
        logits_flat = logits.view(-1, VOCAB_SIZE)  # (B*T, V)
        targets_flat = y.view(-1)  # (B*T,)
        loss = criterion(logits_flat, targets_flat)

        # Backward
        optimiser.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
        optimiser.step()
        scheduler.step()

        # Track
        non_pad = (targets_flat != PAD_ID).sum().item()
        total_loss += loss.item() * non_pad
        total_tokens += non_pad

        if batch_idx % 200 == 0:
            pbar.set_postfix(
                loss=f"{loss.item():.4f}", lr=f"{scheduler.get_last_lr()[0]:.2e}"
            )

    return total_loss / max(total_tokens, 1)


@torch.no_grad()
def evaluate(model, loader, criterion):
    model.eval()
    total_loss = 0.0
    total_tokens = 0
    hidden = None

    for x, y in tqdm(loader, desc="  Eval", leave=False):
        x, y = x.to(DEVICE), y.to(DEVICE)
        batch_size = x.size(0)

        if hidden is None or hidden[0].size(1) != batch_size:
            hidden = model.init_hidden(batch_size)
        hidden = (hidden[0].detach(), hidden[1].detach())

        logits, hidden = model(x, hidden)
        logits_flat = logits.view(-1, VOCAB_SIZE)
        targets_flat = y.view(-1)
        loss = criterion(logits_flat, targets_flat)

        non_pad = (targets_flat != PAD_ID).sum().item()
        total_loss += loss.item() * non_pad
        total_tokens += non_pad

    avg_loss = total_loss / max(total_tokens, 1)
    return avg_loss, math.exp(avg_loss)  # (loss, perplexity)


def train():
    print("\n[7] Starting training...")
    train_loader, val_loader, test_loader = make_dataloaders(
        CFG["batch_size"], CFG["seq_len"]
    )

    model = ArabicLSTMLM(
        vocab_size=VOCAB_SIZE,
        embed_dim=CFG["embed_dim"],
        hidden_size=CFG["hidden_size"],
        num_layers=CFG["num_layers"],
        dropout=CFG["dropout"],
    ).to(DEVICE)

    n_params = count_parameters(model)
    print(f"  Model parameters: {n_params / 1e6:.2f}M")

    criterion = nn.CrossEntropyLoss(ignore_index=PAD_ID)

    optimiser = AdamW(
        model.parameters(),
        lr=CFG["peak_lr"],
        weight_decay=CFG["weight_decay"],
        betas=(0.9, 0.999),
        eps=1e-8,
    )

    total_steps = len(train_loader) * CFG["epochs"]
    scheduler = OneCycleLR(
        optimiser,
        max_lr=CFG["peak_lr"],
        total_steps=total_steps,
        pct_start=CFG["warmup_pct"],
        anneal_strategy="cos",
        final_div_factor=CFG["peak_lr"] / 1e-5,
    )

    best_val_ppl = float("inf")
    patience_counter = 0
    history = []

    print(
        f"  Training for up to {CFG['epochs']} epochs, "
        f"early-stopping patience = {CFG['patience']}\n"
    )

    for epoch in range(1, CFG["epochs"] + 1):
        t0 = time.time()
        train_loss = train_epoch(
            model, train_loader, criterion, optimiser, scheduler, CFG["grad_clip"]
        )
        val_loss, val_ppl = evaluate(model, val_loader, criterion)
        elapsed = time.time() - t0

        history.append(
            {
                "epoch": epoch,
                "train_loss": train_loss,
                "val_loss": val_loss,
                "val_ppl": val_ppl,
            }
        )

        print(
            f"  Epoch {epoch:02d}/{CFG['epochs']}  |  "
            f"train_loss={train_loss:.4f}  |  "
            f"val_loss={val_loss:.4f}  |  "
            f"val_ppl={val_ppl:.2f}  |  "
            f"time={elapsed:.0f}s"
        )

        # Checkpoint
        ckpt_path = CHECKPOINT_DIR / f"epoch_{epoch:02d}_ppl{val_ppl:.1f}.pt"
        torch.save(
            {
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "val_ppl": val_ppl,
                "cfg": CFG,
            },
            ckpt_path,
        )

        # Best model
        if val_ppl < best_val_ppl:
            best_val_ppl = val_ppl
            patience_counter = 0
            torch.save(model.state_dict(), CHECKPOINT_DIR / "best_model.pt")
            print(f"    ✓ New best val_ppl = {best_val_ppl:.2f} — saved best_model.pt")
        else:
            patience_counter += 1
            print(f"    No improvement ({patience_counter}/{CFG['patience']})")
            if patience_counter >= CFG["patience"]:
                print(f"\n  Early stopping triggered after epoch {epoch}.")
                break

    # Reload best weights
    model.load_state_dict(
        torch.load(CHECKPOINT_DIR / "best_model.pt", map_location=DEVICE)
    )
    print(f"\n  Training complete. Best val perplexity: {best_val_ppl:.2f}")

    # Save history
    with open(BASE_DIR / "training_history.json", "w") as f:
        json.dump(history, f, indent=2)

    return model, test_loader


model, test_loader = train()


# ╔══════════════════════════════════════════════════════════╗
# ║  SECTION 8 — EVALUATION (PPL + TOP-K ACCURACY)         ║
# ╚══════════════════════════════════════════════════════════╝


@torch.no_grad()
def compute_topk_accuracy(model, loader, k: int = 5, max_batches: int = 200):
    """Compute top-k word-level prediction accuracy on the test set.

    For each token position, we ask: is the true next token in the
    top-k predicted tokens? This is the subword-level proxy for
    word-level top-k accuracy (very close in practice).
    """
    model.eval()
    correct_topk = {1: 0, 3: 0, 5: 0}
    total = 0
    hidden = None

    for batch_idx, (x, y) in enumerate(
        tqdm(loader, desc="  TopK eval", leave=False, total=max_batches)
    ):
        if batch_idx >= max_batches:
            break
        x, y = x.to(DEVICE), y.to(DEVICE)
        bs = x.size(0)

        if hidden is None or hidden[0].size(1) != bs:
            hidden = model.init_hidden(bs)
        hidden = (hidden[0].detach(), hidden[1].detach())

        logits, hidden = model(x, hidden)  # (B, T, V)

        # Flatten
        logits_flat = logits.view(-1, VOCAB_SIZE)  # (B*T, V)
        targets_flat = y.view(-1)  # (B*T,)

        # Only score non-padding positions
        mask = targets_flat != PAD_ID
        logits_flat = logits_flat[mask]
        targets_flat = targets_flat[mask]

        # Top-k predictions
        _, topk_ids = torch.topk(logits_flat, k=5, dim=-1)  # (N, 5)

        for ki in [1, 3, 5]:
            hits = (topk_ids[:, :ki] == targets_flat.unsqueeze(1)).any(dim=1)
            correct_topk[ki] += hits.sum().item()

        total += targets_flat.size(0)

    results = {f"top{ki}": correct_topk[ki] / max(total, 1) for ki in [1, 3, 5]}
    return results


print("\n[8] Running final evaluation on test set...")
criterion = nn.CrossEntropyLoss(ignore_index=PAD_ID)
test_loss, test_ppl = evaluate(model, test_loader, criterion)
topk_acc = compute_topk_accuracy(model, test_loader, k=5)

print("\n  ── TEST SET RESULTS ──────────────────────────────")
print(f"  Test Loss       : {test_loss:.4f}")
print(f"  Test Perplexity : {test_ppl:.2f}")
print(f"  Top-1 Accuracy  : {topk_acc['top1'] * 100:.2f}%")
print(f"  Top-3 Accuracy  : {topk_acc['top3'] * 100:.2f}%")
print(f"  Top-5 Accuracy  : {topk_acc['top5'] * 100:.2f}%  ← primary metric")
print("  ─────────────────────────────────────────────────")

eval_results = {
    "test_loss": test_loss,
    "test_perplexity": test_ppl,
    **{k: round(v * 100, 2) for k, v in topk_acc.items()},
}
with open(BASE_DIR / "eval_results.json", "w") as f:
    json.dump(eval_results, f, indent=2)


# ╔══════════════════════════════════════════════════════════╗
# ║  SECTION 9 — HYBRID INFERENCE (LSTM + KN BLENDING)     ║
# ╚══════════════════════════════════════════════════════════╝
#
#  This section provides the complete inference engine.
#  It can be used standalone (without the Kneser-Ney model) if
#  you haven't integrated the KN model yet — the fallback is
#  graceful (alpha=1.0, neural-only).
# ──────────────────────────────────────────────────────────────


class HybridArabicPredictor:
    """Real-time Arabic next-word predictor combining:
      - LSTM neural language model (primary)
      - Kneser-Ney n-gram model (optional fallback / blending)

    Usage:
        predictor = HybridArabicPredictor(model, sp_model, kn_model=None)
        suggestions = predictor.predict("ذهبت إلى المدرسة", top_k=5)
    """

    def __init__(
        self,
        neural_model: ArabicLSTMLM,
        sp: spm.SentencePieceProcessor,
        kn_model=None,  # your existing KN object, or None
        cfg: dict = CFG,
    ):
        self.model = neural_model.eval()
        self.sp = sp
        self.kn = kn_model
        self.cfg = cfg
        self.ctx_len = cfg["infer_ctx_len"]

        # Pre-build id→word mapping for fast decoding
        self._build_vocab_lookup()

    def _build_vocab_lookup(self):
        """Map each token id to its string piece."""
        self.id_to_piece = {}
        for i in range(self.sp.vocab_size()):
            self.id_to_piece[i] = self.sp.id_to_piece(i)

    def _encode_context(self, text: str) -> torch.Tensor:
        """Normalise, encode, and take the last `ctx_len` tokens.
        Returns a (1, ctx_len) tensor.
        """
        text = normalise_arabic(text)
        ids = self.sp.encode(text, out_type=int)
        ids = ids[-self.ctx_len :]  # take last ctx_len tokens
        if not ids:
            ids = [BOS_ID]
        tensor = torch.tensor([ids], dtype=torch.long, device=DEVICE)
        return tensor

    @torch.no_grad()
    def _neural_next_token_probs(self, context_ids: torch.Tensor) -> torch.Tensor:
        """Run a forward pass and return a probability distribution over
        the vocabulary for the NEXT token after the context.

        Returns: (vocab_size,) probability tensor on CPU.
        """
        self.model.eval()
        logits, _ = self.model(context_ids)  # (1, T, V)
        # Take logits at the last position
        next_logits = logits[0, -1, :]  # (V,)
        probs = F.softmax(next_logits, dim=-1).cpu()
        return probs

    def _decode_tokens_to_words(
        self, token_probs: torch.Tensor, top_n: int = 50
    ) -> dict[str, float]:
        """Aggregate subword token probabilities into whole-word probabilities.

        Strategy:
          - Get top_n candidate tokens
          - Decode each to its string
          - If the piece starts a new word (no '▁' continuation marker),
            it IS a whole word candidate
          - Accumulate probability for identical decoded strings
        """
        top_probs, top_ids = torch.topk(token_probs, k=min(top_n, len(token_probs)))
        word_probs: dict[str, float] = defaultdict(float)

        for prob, tid in zip(top_probs.tolist(), top_ids.tolist()):
            piece = self.sp.id_to_piece(tid)
            # SentencePiece uses '▁' as a word-start marker
            word = piece.replace("▁", "").strip()
            if word and len(word) >= 2 and ARABIC_CHARS.search(word):
                word_probs[word] += prob

        return dict(word_probs)

    def predict(self, text: str, top_k: int = 5) -> list[tuple[str, float]]:
        """Predict the top-k next words given an Arabic text context.

        Args:
            text  : the text typed so far (Arabic string)
            top_k : how many predictions to return

        Returns:
            list of (word, combined_score) tuples, sorted best-first
        """
        # ── Neural predictions ──────────────────────────────
        ctx_ids = self._encode_context(text)
        tok_probs = self._neural_next_token_probs(ctx_ids)  # (V,)
        neural_words = self._decode_tokens_to_words(tok_probs, top_n=100)

        # Neural confidence: max probability of top prediction
        max_neural_prob = max(neural_words.values()) if neural_words else 0.0
        alpha = (
            self.cfg["alpha_high"]
            if max_neural_prob >= self.cfg["confidence_thresh"]
            else self.cfg["alpha_low"]
        )

        # ── KN predictions (optional) ────────────────────────
        kn_words: dict[str, float] = {}
        if self.kn is not None:
            words = text.strip().split()
            w1 = words[-2] if len(words) >= 2 else None
            w2 = words[-1] if len(words) >= 1 else None
            try:
                kn_preds = self.kn.predict(w1, w2, top_k=50)
                kn_words = {word: prob for word, prob in kn_preds}
            except Exception:
                pass

        # ── Blend scores ─────────────────────────────────────
        # Work in log-space to avoid underflow
        all_words = set(neural_words.keys()) | set(kn_words.keys())
        combined: dict[str, float] = {}

        log_eps = math.log(1e-10)

        for word in all_words:
            log_neural = math.log(neural_words.get(word, 1e-10))
            log_kn = math.log(kn_words.get(word, 1e-10)) if self.kn else log_eps
            if self.kn:
                score = alpha * log_neural + (1 - alpha) * log_kn
            else:
                score = log_neural  # neural-only mode
            combined[word] = score

        # Sort and return top-k
        top = sorted(combined.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return top


print("\n[9] Initialising hybrid predictor (neural-only mode if no KN model)...")
predictor = HybridArabicPredictor(
    neural_model=model,
    sp=SP,
    kn_model=None,  # ← plug your KN model object here if available
)
print("  Predictor ready.")


# ╔══════════════════════════════════════════════════════════╗
# ║  SECTION 10 — ONNX EXPORT & INT8 QUANTISATION          ║
# ╚══════════════════════════════════════════════════════════╝


def export_to_onnx(model: ArabicLSTMLM, path: str):
    """Export the model to ONNX format for cross-platform inference."""
    print(f"\n[10] Exporting to ONNX: {path}")
    model.eval()
    model.cpu()

    batch = 1
    seq = int(CFG["infer_ctx_len"])
    dummy_input = torch.randint(0, VOCAB_SIZE, (batch, seq))
    dummy_h0 = torch.zeros(int(CFG["num_layers"]), batch, int(CFG["hidden_size"]))
    dummy_c0 = torch.zeros_like(dummy_h0)

    # We export with dynamic batch and sequence axes.
    # We pass dynamo=False to force the stable legacy JIT exporter,
    # since PyTorch 2.2+ defaults to Dynamo which crashes on dynamic_axes with LSTMs.
    torch.onnx.export(
        model,
        (dummy_input, (dummy_h0, dummy_c0)),
        path,
        input_names=["input_ids", "h0", "c0"],
        output_names=["logits", "h_n", "c_n"],
        dynamic_axes={
            "input_ids": {0: "batch", 1: "seq_len"},
            "h0": {1: "batch"},
            "c0": {1: "batch"},
            "logits": {0: "batch", 1: "seq_len"},
            "h_n": {1: "batch"},
            "c_n": {1: "batch"},
        },
        opset_version=17,
        do_constant_folding=True,
        dynamo=False,
    )

    size_mb = os.path.getsize(path) / 1e6
    print(f"  -> ONNX model saved ({size_mb:.1f} MB)")

    # Move model back to DEVICE for any further usage
    model.to(DEVICE)


def quantise_onnx(fp32_path: str, int8_path: str):
    """Apply INT8 dynamic quantisation to reduce model size ~3-4×."""
    try:
        from onnxruntime.quantization import QuantType, quantize_dynamic

        print(f"\n[10] Quantising to INT8: {int8_path}")
        quantize_dynamic(fp32_path, int8_path, weight_type=QuantType.QInt8)
        fp32_mb = os.path.getsize(fp32_path) / 1e6
        int8_mb = os.path.getsize(int8_path) / 1e6
        print(
            f"  -> FP32: {fp32_mb:.1f} MB  |  INT8: {int8_mb:.1f} MB  "
            f"(reduction: {fp32_mb / int8_mb:.1f}x)"
        )
    except ImportError:
        print("  [WARN] onnxruntime-tools not found; skipping INT8 quantisation.")
        print("         Run: pip install onnxruntime-tools")


export_to_onnx(model, str(ONNX_PATH))
quantise_onnx(str(ONNX_PATH), str(ONNX_INT8_PATH))


# ╔══════════════════════════════════════════════════════════╗
# ║  SECTION 11 — QUICK DEMO                               ║
# ╚══════════════════════════════════════════════════════════╝

print("\n" + "═" * 58)
print("  ARABIC AUTOCOMPLETE — QUICK DEMO")
print("═" * 58)

demo_contexts = [
    "ذهبت إلى المدرسة",
    "في عام ألفين وعشرين",
    "قال الرئيس إن",
    "أحب أن أقرأ",
    "الطقس اليوم",
    "سافرت إلى",
]

model.to(DEVICE)
for ctx in demo_contexts:
    preds = predictor.predict(ctx, top_k=int(CFG["top_k"]))
    pred_str = "  |  ".join(f"{word} ({math.exp(score):.3f})" for word, score in preds)
    print(f"\n  Context : «{ctx}»")
    print(f"  Top-5   : {pred_str}")

print("\n" + "═" * 58)
print("  SAVED ARTEFACTS")
print("═" * 58)
artefacts = [
    (CORPUS_FILE, "Cleaned training corpus"),
    (SPM_MODEL, "SentencePiece BPE model"),
    (CHECKPOINT_DIR / "best_model.pt", "Best LSTM checkpoint (PyTorch)"),
    (ONNX_PATH, "LSTM model (ONNX FP32)"),
    (ONNX_INT8_PATH, "LSTM model (ONNX INT8 quantised)"),
    (BASE_DIR / "training_history.json", "Training history"),
    (BASE_DIR / "eval_results.json", "Evaluation results"),
]

for path, desc in artefacts:
    path = Path(str(path))
    if path.exists():
        size = path.stat().st_size
        size_str = f"{size / 1e6:.1f} MB" if size > 1e6 else f"{size / 1e3:.0f} KB"
        print(f"  {size_str:>8}  {path.name:40s}  {desc}")
    else:
        print(f"  {'N/A':>8}  {path.name:40s}  (not generated)")

print("\nDone. Your hybrid Arabic autocomplete model is ready.")
print("To integrate your KN model, pass it as kn_model= to HybridArabicPredictor.")
