# CRF Layer Integration Plan for GEC Edit Tagger

## Overview

This document outlines the plan to add a Conditional Random Field (CRF) layer on top of the AraBERT-based edit tagger model. The CRF layer will model dependencies between adjacent label predictions, improving sequence labeling accuracy by considering label transitions.

## Current Architecture

```
Input Text → AraBERT → Token Representations → Classification Head → Label Predictions
```

## Target Architecture

```
Input Text → AraBERT → Token Representations → CRF Layer → Label Predictions
```

---

## Phase 1: Install CRF Dependencies

### 1.1 Add CRF Library

Add `pytorch-crf` to project dependencies:

```bash
pip install pytorch-crf
```

**File to update:** `requirements.txt` (if it exists) or document in setup instructions

---

## Phase 2: Create CRF Wrapper Module

### 2.1 New File: `src/services/gec/modules/edit_tagger/model/crf_wrapper.py`

**Purpose:** Wrap the pre-trained AraBERT model with a CRF layer without modifying the original model architecture.

**Key Components:**

```python
import torch
import torch.nn as nn
from torchcrf import CRF

class BertCRFForTokenClassification(nn.Module):
    def __init__(self, base_model, num_labels, label2id=None):
        super().__init__()
        self.bert = base_model
        self.classifier = base_model.classifier  # Reuse existing classifier
        self.crf = CRF(num_labels, batch_first=True)
        self.num_labels = num_labels
        self.label2id = label2id or {}
    
    def forward(self, input_ids, attention_mask=None, labels=None):
        # Get emissions from BERT + classifier
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        emissions = self.classifier(outputs.last_hidden_state)
        
        # Apply CRF
        if labels is not None:
            # Training: compute negative log-likelihood loss
            loss = -self.crf(emissions, labels, mask=attention_mask.bool(), reduction="mean")
            return {"loss": loss, "logits": emissions}
        else:
            # Inference: Viterbi decoding
            predictions = self.crf.decode(emissions, mask=attention_mask.bool())
            return {"logits": torch.tensor(predictions, device=emissions.device)}
```

**Design Decisions:**
- Wrap existing model rather than modifying it
- CRF operates on emissions from the classification head
- Maintain compatibility with HuggingFace Trainer API
- Support both training (with labels) and inference modes

---

## Phase 3: Refactor Model Loading

### 3.1 New File: `src/services/gec/modules/edit_tagger/model/model_loader.py`

**Purpose:** Centralize model loading logic with optional CRF integration.

**Key Functions:**

```python
def load_base_model(checkpoint_path, num_labels, label2id):
    """Load the base AraBERT model for token classification"""
    from transformers import AutoModelForTokenClassification
    
    model = AutoModelForTokenClassification.from_pretrained(
        checkpoint_path,
        num_labels=num_labels,
        id2label={v: k for k, v in label2id.items()},
        label2id=label2id,
    )
    return model

def wrap_with_crf(model, num_labels, label2id):
    """Wrap a loaded model with CRF layer"""
    from src.services.gec.modules.edit_tagger.model.crf_wrapper import BertCRFForTokenClassification
    
    crf_model = BertCRFForTokenClassification(
        base_model=model,
        num_labels=num_labels,
        label2id=label2id,
    )
    return crf_model

def load_model_with_optional_crf(checkpoint_path, num_labels, label2id, use_crf=False):
    """Load model with optional CRF wrapper"""
    base_model = load_base_model(checkpoint_path, num_labels, label2id)
    
    if use_crf:
        return wrap_with_crf(base_model, num_labels, label2id)
    
    return base_model
```

### 3.2 Update: `src/services/gec/config.py`

Add CRF-related configuration:

```python
# CRF Configuration
USE_CRF = False  # Toggle CRF usage
CRF_CHECKPOINT_SUFFIX = "_crf"  # Suffix for CRF model checkpoints
```

---

## Phase 4: Update Training Pipeline

### 4.1 Update: `src/services/gec/modules/edit_tagger/training/trainer.py`

**Changes:**
- Add `use_crf` parameter to `build_trainer`
- Update model loading to support CRF wrapper
- Ensure loss computation works with CRF model

```python
def build_trainer(
    model,
    train_dataset,
    tokenizer,
    output_dir="./gec_output",
    num_train_epochs=10,
    weight_decay=0.01,
    warmup_ratio=0.1,
    label2id_path=None,
    use_crf=False,  # New parameter
):
    id2label = _load_id2label(label2id_path)
    metrics_fn = partial(compute_metrics, id2label=id2label)
    
    # ... rest of the function remains the same
```

### 4.2 Update: `src/services/gec/scripts/train.py`

**Changes:**
- Add command-line flag for CRF usage
- Load model with CRF wrapper if enabled

```python
# Add argument parser option
parser.add_argument("--use-crf", action="store_true", help="Use CRF layer")

# In training setup
model = load_model_with_optional_crf(
    checkpoint_path=BASE_CHECKPOINT,
    num_labels=len(label2id),
    label2id=label2id,
    use_crf=args.use_crf,
)
```

---

## Phase 5: Update Inference Pipeline

### 5.1 Update: `src/services/gec/modules/edit_tagger/inference/inference.py`

**Changes:**
- Handle CRF model output format (list of predictions vs argmax)
- Ensure compatibility with both standard and CRF models

```python
def predict(self, text: str) -> tuple[list[str], list[str]]:
    # ... existing setup code ...
    
    with torch.no_grad():
        outputs = self.model(
            input_ids=input_ids,
            attention_mask=attention_mask,
        )
    
    # Handle CRF vs standard model output
    if hasattr(outputs, 'logits') and outputs.logits.dim() == 3:
        # Standard model: (batch, seq_len, num_labels)
        pred_ids = outputs.logits.argmax(dim=-1)[0].tolist()
    else:
        # CRF model: already decoded predictions
        pred_ids = outputs.logits[0].tolist()
    
    # ... rest of the function remains the same
```

### 5.2 Update: `src/services/gec/modules/edit_tagger/inference/predictor.py`

**Changes:**
- Add CRF support flag
- Update prediction logic to handle CRF output

---

## Phase 6: Update Evaluation Script

### 6.1 Move Logic from Notebook to: `src/services/gec/scripts/evaluate.py`

**Purpose:** Extract evaluation logic from `test_edit_tagger.ipynb` into a reusable script.

**Key Functions:**

```python
def evaluate_model(model, test_loader, id2label, device):
    """Run inference on test set and collect predictions"""
    all_preds = []
    all_labels = []
    
    with torch.no_grad():
        for batch in tqdm(test_loader, desc="Evaluating"):
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"]
            
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            
            # Handle CRF vs standard output
            if hasattr(outputs, 'logits') and outputs.logits.dim() == 3:
                pred_ids = outputs.logits.argmax(dim=-1).cpu().numpy()
            else:
                pred_ids = outputs.logits.cpu().numpy()
            
            all_preds.append(pred_ids)
            all_labels.append(labels.numpy())
    
    return np.concatenate(all_preds, axis=0), np.concatenate(all_labels, axis=0)

def compute_overall_metrics(all_preds, all_labels, ignore_index=-100):
    """Compute accuracy, precision, recall, F0.5"""
    # ... existing metrics logic from notebook ...

def compute_per_label_metrics(all_preds, all_labels, id2label, ignore_index=-100):
    """Compute per-label precision, recall, F0.5"""
    # ... existing per-label logic from notebook ...

def compute_operation_metrics(all_preds, all_labels, id2label, ignore_index=-100):
    """Compute metrics by operation type (K, R, I, D)"""
    # ... existing operation metrics logic from notebook ...

def print_sample_predictions(test_raw, all_preds, id2label, num_samples=5):
    """Print sample predictions with mismatches"""
    # ... existing sample printing logic from notebook ...
```

### 6.2 Update: `src/services/gec/scripts/test.py`

**Purpose:** Main entry point for evaluation (replaces notebook workflow).

**Key Components:**

```python
import argparse
import json
import torch
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForTokenClassification
from torch.utils.data import DataLoader
from transformers import DataCollatorForTokenClassification

from src.services.gec.config import (
    PROCESSED_DATA_DIR,
    LABEL2ID_PATH,
    MAX_LENGTH,
    BATCH_SIZE,
)
from src.services.gec.modules.edit_tagger.training.datasets import GECTrainingDataset
from src.services.gec.modules.edit_tagger.model.model_loader import load_model_with_optional_crf
from src.services.gec.scripts.evaluate import (
    evaluate_model,
    compute_overall_metrics,
    compute_per_label_metrics,
    compute_operation_metrics,
    print_sample_predictions,
)

def main():
    parser = argparse.ArgumentParser(description="Evaluate GEC edit tagger model")
    parser.add_argument("--model-path", type=str, required=True, help="Path to model checkpoint")
    parser.add_argument("--test-jsonl", type=str, help="Path to test JSONL file")
    parser.add_argument("--use-crf", action="store_true", help="Use CRF layer")
    parser.add_argument("--num-samples", type=int, default=5, help="Number of sample predictions to show")
    
    args = parser.parse_args()
    
    # Load configuration
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # Load label vocabulary
    with open(LABEL2ID_PATH, encoding="utf-8") as f:
        label2id = json.load(f)
    id2label = {v: k for k, v in label2id.items()}
    
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained("aubmindlab/bert-base-arabertv02")
    
    # Load model
    model = load_model_with_optional_crf(
        checkpoint_path=args.model_path,
        num_labels=len(label2id),
        label2id=label2id,
        use_crf=args.use_crf,
    )
    model = model.to(device)
    model.eval()
    
    # Load test dataset
    test_dataset = GECTrainingDataset(
        jsonl_path=args.test_jsonl,
        tokenizer=tokenizer,
        label2id=label2id,
        max_length=MAX_LENGTH,
    )
    
    # Create data loader
    data_collator = DataCollatorForTokenClassification(tokenizer=tokenizer)
    test_loader = DataLoader(
        test_dataset,
        batch_size=BATCH_SIZE,
        collate_fn=data_collator,
        shuffle=False,
    )
    
    # Run evaluation
    print("Running evaluation...")
    all_preds, all_labels = evaluate_model(model, test_loader, id2label, device)
    
    # Compute and print metrics
    print("\n" + "=" * 50)
    print("Overall Metrics")
    print("=" * 50)
    compute_overall_metrics(all_preds, all_labels)
    
    print("\n" + "=" * 50)
    print("Per-Label Metrics (Top 50)")
    print("=" * 50)
    compute_per_label_metrics(all_preds, all_labels, id2label)
    
    print("\n" + "=" * 50)
    print("Operation-Type Metrics")
    print("=" * 50)
    compute_operation_metrics(all_preds, all_labels, id2label)
    
    print("\n" + "=" * 50)
    print("Sample Predictions")
    print("=" * 50)
    print_sample_predictions(args.test_jsonl, all_preds, id2label, args.num_samples)

if __name__ == "__main__":
    main()
```

---

## Phase 7: Training with CRF

### 7.1 New File: `src/services/gec/scripts/train_crf.py`

**Purpose:** Dedicated training script for CRF-enhanced model.

**Key Differences from Standard Training:**
- Load model with CRF wrapper
- Adjust learning rate (CRF typically needs lower LR)
- Potentially fine-tune only CRF layer initially, then full model

```python
def train_crf_model():
    # Load base model (frozen or fine-tuned)
    base_model = load_base_model(...)
    
    # Freeze BERT layers for initial CRF training (optional)
    for param in base_model.bert.parameters():
        param.requires_grad = False
    
    # Wrap with CRF
    crf_model = wrap_with_crf(base_model, ...)
    
    # Train CRF layer only (phase 1)
    trainer = build_trainer(crf_model, ..., use_crf=True)
    trainer.train()
    
    # Unfreeze BERT for full fine-tuning (phase 2, optional)
    for param in crf_model.bert.parameters():
        param.requires_grad = True
    
    # Fine-tune entire model
    trainer = build_trainer(crf_model, ..., use_crf=True)
    trainer.train()
```

---

## Phase 8: Testing and Validation

### 8.1 Unit Tests

**File:** `tests/test_crf_integration.py`

**Test Cases:**
1. CRF wrapper forward pass with labels (training mode)
2. CRF wrapper forward pass without labels (inference mode)
3. CRF model saves and loads correctly
4. CRF predictions are valid label sequences
5. Metrics computation works with CRF output format

### 8.2 Integration Tests

**Test Cases:**
1. End-to-end training with CRF enabled
2. End-to-end evaluation with CRF enabled
3. Compare CRF vs non-CRF performance on validation set

---

## Phase 9: Documentation

### 9.1 Update README

Add section on CRF usage:

```markdown
## Using CRF Layer

The GEC edit tagger supports an optional CRF layer for improved sequence labeling.

### Training with CRF

```bash
python -m src.services.gec.scripts.train_crf \
    --base-checkpoint aubmindlab/bert-base-arabertv02 \
    --train-jsonl data/edit_tagger/processed/train.jsonl \
    --label2id data/edit_tagger/processed/label2id.json \
    --output-dir gec_models/edit_tagger_crf_v1
```

### Evaluation with CRF

```bash
python -m src.services.gec.scripts.test \
    --model-path gec_models/edit_tagger_crf_v1 \
    --test-jsonl data/edit_tagger/processed/test.jsonl \
    --use-crf
```
```

---

## File Structure After Integration

```
src/services/gec/
├── config.py (updated)
├── modules/edit_tagger/
│   ├── model/
│   │   ├── __init__.py (new)
│   │   ├── crf_wrapper.py (new)
│   │   └── model_loader.py (new)
│   ├── training/
│   │   ├── trainer.py (updated)
│   │   ├── datasets.py
│   │   └── metrics.py
│   ├── inference/
│   │   ├── inference.py (updated)
│   │   └── predictor.py (updated)
│   └── preprocessing/
│       └── ... (unchanged)
├── scripts/
│   ├── train.py (updated)
│   ├── train_crf.py (new)
│   ├── test.py (updated with evaluation logic)
│   └── evaluate.py (new - extracted from notebook)
└── notebooks/
    └── test_edit_tagger.ipynb (deprecated or kept for reference)
```

---

## Migration Path

### For Existing Models
- Existing non-CRF models continue to work without changes
- CRF is opt-in via `--use-crf` flag
- No breaking changes to existing APIs

### For Training Pipeline
- Standard training: `python -m src.services.gec.scripts.train`
- CRF training: `python -m src.services.gec.scripts.train_crf`

### For Evaluation
- Standard evaluation: `python -m src.services.gec.scripts.test --model-path <path>`
- CRF evaluation: `python -m src.services.gec.scripts.test --model-path <path> --use-crf`

---

## Performance Considerations

1. **Training Speed:** CRF adds ~20-30% overhead to training time due to forward-backward algorithm
2. **Inference Speed:** Viterbi decoding is slightly slower than argmax but still efficient
3. **Memory:** CRF adds minimal memory overhead (transition matrix: num_labels² parameters)
4. **Accuracy:** Expected 2-5% F0.5 improvement based on similar sequence labeling tasks

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| CRF training instability | Use gradient clipping, lower learning rate for CRF layer |
| Incompatibility with existing models | Wrap approach preserves original model architecture |
| Performance regression | Provide easy toggle to disable CRF |
| Increased complexity | Clear documentation and separate training scripts |

---

## Timeline Estimate

| Phase | Estimated Time |
|-------|---------------|
| Phase 1-2: Dependencies & CRF wrapper | 2 hours |
| Phase 3-4: Model loading & training updates | 3 hours |
| Phase 5-6: Inference & evaluation updates | 3 hours |
| Phase 7: CRF training script | 2 hours |
| Phase 8: Testing | 2 hours |
| Phase 9: Documentation | 1 hour |
| **Total** | **~13 hours** |

---

## Next Steps

1. Review and approve this plan
2. Create feature branch for CRF integration
3. Implement phases 1-3 (core infrastructure)
4. Test with small subset of data
5. Implement phases 4-6 (full pipeline)
6. Run full training and evaluation experiments
7. Document results and merge to main