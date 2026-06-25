"""Test pipeline for GEC + Ranker integration.

This script demonstrates how to:
1. Load test data from QALB-2014-L1-Test
2. Run preprocessing (tokenization)
3. Run GED (error detection) - mock implementation
4. Run GEC modules (TAG, ONTOLOGY, DICTIONARY) - mock implementations
5. Run the Rule-Based Ranker
6. Output ranked corrections

Usage:
    python -m src.services.gec.notebooks.test_ranker_pipeline
"""

from __future__ import annotations

import json
from pathlib import Path

from src.core.schemas import Token
from src.services.ged.schemas import (
    ErrorCategory,
    ErrorSource,
    ErrorSpan,
    ProvenanceTier,
)
from src.services.gec.schemas import (
    CandidateEdit,
    DictionaryCandidateEdit,
    EditGroup,
    EditOperation,
    EditTaggerCandidateEdit,
    ModuleName,
    ModuleResult,
    ModuleStatus,
    OntologyCandidateEdit,
)
from src.services.ranker import RankerInput, RankerOutput, RankerService
from src.services.ranker.config import get_ranker_config


TEST_DATA_DIR = Path(__file__).parent.parent / "data" / "edit_tagger" / "raw" / "test"
SENT_FILE = TEST_DATA_DIR / "QALB-2014-L1-Test.sent"
COR_FILE = TEST_DATA_DIR / "QALB-2014-L1-Test.cor"


def load_test_data(num_samples: int = 5) -> list[tuple[str, str, str]]:
    """Load sentence/correction pairs from test data.
    
    Returns:
        List of (doc_id, original, corrected) tuples
    """
    samples = []
    with open(SENT_FILE) as sent_f, open(COR_FILE) as cor_f:
        for sent_line, cor_line in zip(sent_f, cor_f):
            sent_line = sent_line.strip()
            cor_line = cor_line.strip()
            if not sent_line or not cor_line:
                continue
            
            parts = sent_line.split(" ", 1)
            if len(parts) != 2:
                continue
            doc_id, text = parts
            
            cor_parts = cor_line.split(" ", 1)
            if len(cor_parts) != 2:
                continue
            _, correction = cor_parts
            
            samples.append((doc_id, text, correction))
            
            if len(samples) >= num_samples:
                break
    
    return samples


def mock_tokenize(text: str) -> list[Token]:
    """Simple whitespace tokenizer for demo purposes.
    
    In production, this would use Farasa/CAMeL from preprocessing service.
    """
    tokens = []
    start = 0
    for i, token in enumerate(text.split()):
        token_start = text.find(token, start)
        token_end = token_start + len(token)
        tokens.append(
            Token(
                index=i,
                form=token,
                span=(token_start, token_end),
                norm_span=(token_start, token_end),
                is_oov=False,
            )
        )
        start = token_end
    return tokens


def mock_ged(text: str, tokens: list[Token], corrected: str) -> list[ErrorSpan]:
    """Mock GED that finds differences between original and corrected text.
    
    This is a simplified implementation for testing the ranker.
    In production, GED would use rule-based and ML models.
    """
    error_spans = []
    
    words_orig = text.split()
    words_corr = corrected.split()
    
    for i, (w_orig, w_corr) in enumerate(zip(words_orig, words_corr)):
        if w_orig != w_corr:
            char_start = text.find(w_orig, 0)
            char_end = char_start + len(w_orig)
            
            error_spans.append(
                ErrorSpan(
                    span=(char_start, char_end),
                    token_refs=[i],
                    category=ErrorCategory.ORTHOGRAPHY,
                    subtype="spelling",
                    confidence=0.85,
                    sources=[ErrorSource.RULE_BASED],
                    provenance_tier=ProvenanceTier.TIER_1_RULE_DERIVED,
                    explanation_eligible=True,
                    explanation_text="خطأ إملائي",
                )
            )
    
    return error_spans


def mock_gec(
    text: str,
    tokens: list[Token],
    error_spans: list[ErrorSpan],
    corrected: str,
) -> list[ModuleResult]:
    """Mock GEC that generates candidate edits from each module.
    
    Each module proposes corrections for detected errors.
    """
    results = []
    
    tag_candidates = []
    ontology_candidates = []
    dictionary_candidates = []
    
    for error_span in error_spans:
        orig_text = text[error_span.span[0] : error_span.span[1]]
        corr_word = corrected.split()[error_span.token_refs[0]]
        
        tag_candidates.append(
            EditTaggerCandidateEdit(
                span=error_span.span,
                token_refs=error_span.token_refs,
                correction=corr_word,
                edit_confidence=0.75,
                edit_operation=[EditOperation.REPLACE],
            )
        )
        
        ontology_candidates.append(
            OntologyCandidateEdit(
                span=error_span.span,
                token_refs=error_span.token_refs,
                correction=corr_word,
                edit_confidence=0.90,
                group=EditGroup(
                    group_id=f"g_{error_span.token_refs[0]}",
                    group_rank=1,
                    explanation="قاعدة إملائية",
                ),
                is_independent=True,
                group_explanation="تصحيح إملائي مستقل",
            )
        )
        
        dictionary_candidates.append(
            DictionaryCandidateEdit(
                span=error_span.span,
                token_refs=error_span.token_refs,
                correction=corr_word,
                edit_confidence=0.80,
                alternatives=[corr_word, orig_text],
            )
        )
    
    results.append(
        ModuleResult(
            module_name=ModuleName.TAG,
            status=ModuleStatus.CORRECT,
            candidate_edits=tag_candidates,
        )
    )
    results.append(
        ModuleResult(
            module_name=ModuleName.ONTOLOGY,
            status=ModuleStatus.CORRECT,
            candidate_edits=ontology_candidates,
        )
    )
    results.append(
        ModuleResult(
            module_name=ModuleName.DICTIONARY,
            status=ModuleStatus.CORRECT,
            candidate_edits=dictionary_candidates,
        )
    )
    
    return results


def run_pipeline(num_samples: int = 5) -> list[dict]:
    """Run the complete GEC + Ranker pipeline on test data.
    
    Args:
        num_samples: Number of test samples to process
        
    Returns:
        List of results with input, output, and metadata
    """
    print(f"Loading {num_samples} test samples...")
    samples = load_test_data(num_samples)
    print(f"Loaded {len(samples)} samples\n")
    
    config = get_ranker_config()
    ranker_service = RankerService(config)
    
    results = []
    
    for doc_id, text, corrected in samples:
        print(f"Processing {doc_id}...")
        print(f"  Original: {text[:80]}...")
        print(f"  Corrected: {corrected[:80]}...")
        
        tokens = mock_tokenize(text)
        print(f"  Tokens: {len(tokens)}")
        
        error_spans = mock_ged(text, tokens, corrected)
        print(f"  Errors detected: {len(error_spans)}")
        
        gec_results = mock_gec(text, tokens, error_spans, corrected)
        print(f"  GEC modules: {len(gec_results)}")
        
        ranker_input = RankerInput(
            text=text,
            tokens=tokens,
            errors_span=error_spans,
            errors_corrections=gec_results,
        )
        
        ranker_output = ranker_service.rank(ranker_input)
        
        print(f"  Ranked edits: {len(ranker_output.ranked_edits)}")
        print(f"  Global confidence: {ranker_output.ranking_metadata.global_confidence:.3f}")
        print(f"  Module utilization: {ranker_output.ranking_metadata.module_utilization}")
        
        if ranker_output.ranked_edits:
            for edit in ranker_output.ranked_edits:
                orig = text[edit.span[0] : edit.span[1]]
                print(f"    - [{edit.selected_module}] '{orig}' → '{edit.correction}' (score: {edit.final_score:.3f})")
        
        results.append(
            {
                "doc_id": doc_id,
                "original": text,
                "corrected": corrected,
                "ranker_output": ranker_output.model_dump(),
                "num_errors": len(error_spans),
                "num_ranked_edits": len(ranker_output.ranked_edits),
            }
        )
        print()
    
    return results


def main():
    """Main entry point."""
    print("=" * 80)
    print("GEC + Ranker Test Pipeline")
    print("=" * 80)
    print()
    
    results = run_pipeline(num_samples=5)
    
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    total_errors = sum(r["num_errors"] for r in results)
    total_ranked = sum(r["num_ranked_edits"] for r in results)
    print(f"Total samples: {len(results)}")
    print(f"Total errors detected: {total_errors}")
    print(f"Total ranked edits: {total_ranked}")
    print(f"Average edits per sample: {total_ranked / len(results):.2f}")
    
    output_file = Path(__file__).parent / "pipeline_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    main()