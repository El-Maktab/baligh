#!/usr/bin/env python3
"""Standalone script to document the LSTM training loop used on Kaggle."""

import json
import math
import time
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from torch.optim import AdamW
from torch.optim.lr_scheduler import OneCycleLR
import sentencepiece as spm

from src.services.nws.features.nwp.lstm.model import ArabicLSTMLM, PAD_ID

CFG = {
    "vocab_size": 12000,
    "embed_dim": 256,
    "hidden_size": 512,
    "num_layers": 2,
    "dropout": 0.30,
    "seq_len": 64,
    "batch_size": 128,
    "epochs": 20,
    "peak_lr": 3e-3,
    "weight_decay": 1e-2,
    "grad_clip": 1.0,
    "warmup_pct": 0.05,
    "patience": 3,
}

class ArabicLMDataset(Dataset):
    def __init__(self, corpus_path: str, sp: spm.SentencePieceProcessor, seq_len: int):
        self.seq_len = seq_len
        token_ids = []
        with open(corpus_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    token_ids.extend(sp.encode(line, out_type=int))
        self.data = torch.tensor(token_ids, dtype=torch.long)
        self.n_windows = (len(self.data) - 1) // seq_len

    def __len__(self):
        return self.n_windows

    def __getitem__(self, idx: int):
        start = idx * self.seq_len
        x = self.data[start: start + self.seq_len]
        y = self.data[start + 1: start + self.seq_len + 1]
        if len(x) < self.seq_len:
            pad_len = self.seq_len - len(x)
            x = F.pad(x, (0, pad_len), value=PAD_ID)
            y = F.pad(y, (0, pad_len), value=PAD_ID)
        return x, y

def train_epoch(model, loader, criterion, optimiser, scheduler, grad_clip, device):
    model.train()
    total_loss, total_tokens = 0.0, 0
    hidden = None

    for x, y in loader:
        x, y = x.to(device), y.to(device)
        batch_size = x.size(0)

        if hidden is not None:
            hidden = (hidden[0].detach(), hidden[1].detach())
        else:
            hidden = model.init_hidden(batch_size)
            
        if hidden[0].size(1) != batch_size:
            hidden = model.init_hidden(batch_size)

        logits, hidden = model(x, hidden)
        
        logits_flat = logits.view(-1, CFG["vocab_size"])
        targets_flat = y.view(-1)
        loss = criterion(logits_flat, targets_flat)

        optimiser.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
        optimiser.step()
        scheduler.step()

        non_pad = (targets_flat != PAD_ID).sum().item()
        total_loss += loss.item() * non_pad
        total_tokens += non_pad

    return total_loss / max(total_tokens, 1)

@torch.no_grad()
def evaluate(model, loader, criterion, device):
    model.eval()
    total_loss, total_tokens = 0.0, 0
    hidden = None

    for x, y in loader:
        x, y = x.to(device), y.to(device)
        batch_size = x.size(0)

        if hidden is None or hidden[0].size(1) != batch_size:
            hidden = model.init_hidden(batch_size)
        hidden = (hidden[0].detach(), hidden[1].detach())

        logits, hidden = model(x, hidden)
        loss = criterion(logits.view(-1, CFG["vocab_size"]), y.view(-1))

        non_pad = (y.view(-1) != PAD_ID).sum().item()
        total_loss += loss.item() * non_pad
        total_tokens += non_pad

    avg_loss = total_loss / max(total_tokens, 1)
    return avg_loss, math.exp(avg_loss)

def train(base_dir: str, sp_model_path: str):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    sp = spm.SentencePieceProcessor(model_file=sp_model_path)
    
    train_ds = ArabicLMDataset(f"{base_dir}/corpus_train.txt", sp, CFG["seq_len"])
    val_ds = ArabicLMDataset(f"{base_dir}/corpus_val.txt", sp, CFG["seq_len"])
    
    train_loader = DataLoader(train_ds, batch_size=CFG["batch_size"], shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=CFG["batch_size"], shuffle=False)

    model = ArabicLSTMLM(
        vocab_size=CFG["vocab_size"],
        embed_dim=CFG["embed_dim"],
        hidden_size=CFG["hidden_size"],
        num_layers=CFG["num_layers"],
        dropout=CFG["dropout"]
    ).to(device)

    criterion = nn.CrossEntropyLoss(ignore_index=PAD_ID)
    optimiser = AdamW(model.parameters(), lr=CFG["peak_lr"], weight_decay=CFG["weight_decay"])
    
    total_steps = len(train_loader) * CFG["epochs"]
    scheduler = OneCycleLR(optimiser, max_lr=CFG["peak_lr"], total_steps=total_steps, pct_start=CFG["warmup_pct"])

    best_val_ppl = float('inf')
    for epoch in range(1, CFG["epochs"] + 1):
        train_loss = train_epoch(model, train_loader, criterion, optimiser, scheduler, CFG["grad_clip"], device)
        val_loss, val_ppl = evaluate(model, val_loader, criterion, device)
        
        print(f"Epoch {epoch} | train_loss={train_loss:.4f} | val_loss={val_loss:.4f} | val_ppl={val_ppl:.2f}")
        
        if val_ppl < best_val_ppl:
            best_val_ppl = val_ppl
            torch.save(model.state_dict(), f"{base_dir}/best_model.pt")

if __name__ == "__main__":
    print("This script is provided for documentation of the Kaggle training loop.")
    print("It is not intended to be run locally due to hardware constraints.")
