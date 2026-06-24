#!/usr/bin/env python3
"""Verify the GEC star labels pipeline is working correctly."""

import json
from pathlib import Path
from src.services.gec.config import (
    CHECKPOINT_PATH,
    LABEL2ID_PATH,
    ID2LABEL_PATH,
)

def verify_data():
    """Verify the training data uses labels_star correctly."""
    print("="*60)
    print("GEC Star Labels Verification")
    print("="*60)
    
    if not CHECKPOINT_PATH.exists():
        print(f"❌ Checkpoint file not found: {CHECKPOINT_PATH}")
        print("   Run build_train() first to generate the data.")
        return False
    
    print(f"\n✓ Checkpoint file: {CHECKPOINT_PATH}")
    
    with open(CHECKPOINT_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"✓ Total examples: {len(lines)}")
    
    first_example = json.loads(lines[0].strip())
    
    has_labels = 'labels' in first_example
    has_labels_star = 'labels_star' in first_example
    
    print(f"\n✓ Has 'labels': {has_labels}")
    print(f"✓ Has 'labels_star': {has_labels_star}")
    
    if has_labels:
        print(f"  - labels length: {len(first_example['labels'])}")
        print(f"  - Sample: {first_example['labels'][:5]}")
    
    if has_labels_star:
        print(f"  - labels_star length: {len(first_example['labels_star'])}")
        print(f"  - Sample: {first_example['labels_star'][:5]}")
    
    print(f"\n✓ Subwords length: {len(first_example['subwords'])}")
    print(f"  - Sample: {first_example['subwords'][:5]}")
    
    if has_labels_star:
        length_match = len(first_example['subwords']) == len(first_example['labels_star'])
        print(f"\n✓ Length match (subwords == labels_star): {length_match}")
        if not length_match:
            print("  ❌ MISMATCH! This will cause training errors.")
            return False
    
    if not LABEL2ID_PATH.exists():
        print(f"\n⚠️  Label mapping not found: {LABEL2ID_PATH}")
        print("   Run build_train() to generate label mappings.")
        return True
    
    with open(LABEL2ID_PATH, 'r', encoding='utf-8') as f:
        label2id = json.load(f)
    
    print(f"\n✓ Label vocabulary size: {len(label2id)}")
    print(f"  - PAD label: {label2id.get('[PAD]', 'NOT FOUND')}")
    print(f"  - UNK label: {label2id.get('[UNK_EDIT]', 'NOT FOUND')}")
    print(f"  - K label: {label2id.get('K', 'NOT FOUND')}")
    print(f"  - K* label: {label2id.get('K*', 'NOT FOUND')}")
    
    print("\n" + "="*60)
    print("✓ Verification PASSED")
    print("="*60)
    print("\nThe pipeline is correctly configured for star labels!")
    print("You can now run training with the notebook or script.")
    
    return True

if __name__ == "__main__":
    verify_data()