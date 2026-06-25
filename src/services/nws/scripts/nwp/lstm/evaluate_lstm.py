#!/usr/bin/env python3
import json
import math
from pathlib import Path
from tqdm.auto import tqdm

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import sentencepiece as spm

from src.services.nws.features.nwp.lstm.model import ArabicLSTMLM, PAD_ID
from src.services.nws.scripts.nwp.lstm.train_lstm import ArabicLMDataset, CFG

@torch.no_grad()
def evaluate(model, loader, criterion, device):
    model.eval()
    total_loss, total_tokens = 0.0, 0
    hidden = None

    for x, y in tqdm(loader, desc="Evaluating Perplexity"):
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

@torch.no_grad()
def compute_topk_accuracy(model, loader, device, k: int = 5, max_batches: int = 200):
    model.eval()
    correct_topk = {1: 0, 3: 0, 5: 0}
    total_tokens = 0
    hidden = None

    for i, (x, y) in enumerate(tqdm(loader, desc="Evaluating Top-K Accuracy")):
        if i >= max_batches:
            break
            
        x, y = x.to(device), y.to(device)
        batch_size = x.size(0)

        if hidden is None or hidden[0].size(1) != batch_size:
            hidden = model.init_hidden(batch_size)
        hidden = (hidden[0].detach(), hidden[1].detach())

        logits, hidden = model(x, hidden)
        
        # Flatten for top-k
        logits_flat = logits.view(-1, CFG["vocab_size"])
        targets_flat = y.view(-1)
        
        # Filter padding
        mask = targets_flat != PAD_ID
        logits_valid = logits_flat[mask]
        targets_valid = targets_flat[mask]
        
        total_tokens += targets_valid.size(0)
        
        # Get top-5 predictions
        _, top5_preds = torch.topk(logits_valid, 5, dim=-1)
        
        # Match against targets
        for idx in range(targets_valid.size(0)):
            target = targets_valid[idx].item()
            preds = top5_preds[idx].tolist()
            
            if target == preds[0]:
                correct_topk[1] += 1
            if target in preds[:3]:
                correct_topk[3] += 1
            if target in preds[:5]:
                correct_topk[5] += 1

    return {k_val: correct_topk[k_val] / total_tokens for k_val in correct_topk}

def run_evaluation():
    base_dir = "src/services/nws/data"
    corpus_dir = f"{base_dir}/lstm_corpus"
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    print("Loading Tokenizer...")
    sp = spm.SentencePieceProcessor(model_file=f"{base_dir}/arabic_bpe.model")
    
    print("Loading Test Dataset...")
    test_ds = ArabicLMDataset(f"{corpus_dir}/corpus_test.txt", sp, CFG["seq_len"])
    test_loader = DataLoader(test_ds, batch_size=CFG["batch_size"], shuffle=False)
    
    print("Loading LSTM Model...")
    model = ArabicLSTMLM(
        vocab_size=CFG["vocab_size"],
        embed_dim=CFG["embed_dim"],
        hidden_size=CFG["hidden_size"],
        num_layers=CFG["num_layers"],
        dropout=0.0
    ).to(device)
    
    ckpt = torch.load(f"{base_dir}/best_model.pt", map_location=device, weights_only=False)
    if "model_state_dict" in ckpt:
        model.load_state_dict(ckpt["model_state_dict"])
    else:
        model.load_state_dict(ckpt)
    criterion = nn.CrossEntropyLoss(ignore_index=PAD_ID)
    
    print("\n--- Starting Evaluation ---")
    loss, ppl = evaluate(model, test_loader, criterion, device)
    print(f"Test Loss: {loss:.4f} | Test Perplexity: {ppl:.2f}")
    
    topk_acc = compute_topk_accuracy(model, test_loader, device)
    print(f"Top-1 Accuracy: {topk_acc[1]:.2%}")
    print(f"Top-3 Accuracy: {topk_acc[3]:.2%}")
    print(f"Top-5 Accuracy: {topk_acc[5]:.2%}")
    
    results = {
        "perplexity": ppl,
        "top_1_accuracy": topk_acc[1],
        "top_3_accuracy": topk_acc[3],
        "top_5_accuracy": topk_acc[5]
    }
    
    out_path = Path("artifacts/nws/evaluation/nwp")
    out_path.mkdir(parents=True, exist_ok=True)
    with open(out_path / "lstm_report.json", "w") as f:
        json.dump(results, f, indent=4)
        
    print(f"\nEvaluation complete. Report saved to {out_path / 'lstm_report.json'}")

if __name__ == "__main__":
    run_evaluation()
