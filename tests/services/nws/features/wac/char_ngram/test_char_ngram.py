"""Tests for the Character N-gram LM pipeline."""

import math
from src.services.nws.features.wac.char_ngram.counter import NGramCounter
from src.services.nws.features.wac.char_ngram.smoother import KneserNeySmoother
from src.services.nws.features.wac.char_ngram.model import CharNGramLM


def test_ngram_counter_basic():
    counter = NGramCounter(max_n=3)
    # Contexts generated for "abc" with max_n=3:
    # 1-grams: "a", "b", "c"
    # 2-grams: ("a",) -> "b", ("b",) -> "c"
    # 3-grams: ("a", "b") -> "c"
    counter.add_sequence("abc")
    
    assert counter.counts[1][tuple()]["a"] == 1
    assert counter.counts[1][tuple()]["b"] == 1
    assert counter.counts[1][tuple()]["c"] == 1
    
    assert counter.counts[2][("a",)]["b"] == 1
    assert counter.counts[2][("b",)]["c"] == 1
    
    assert counter.counts[3][("a", "b")]["c"] == 1


def test_ngram_counter_pruning():
    counter = NGramCounter(max_n=3)
    counter.add_sequence("abx")
    counter.add_sequence("aby")
    counter.add_sequence("abz")
    counter.add_sequence("aba")
    
    # "a", "b", "x", "y", "z", "a"
    # 3-gram ("a", "b") -> "x", "y", "z", "a"
    # All have count 1.
    
    counter.prune(min_count=2, min_n_to_prune=3)
    # The 3-gram counts for ("a", "b") should be gone since they are all count < 2
    assert ("a", "b") not in counter.counts[3]


def test_smoother_and_model():
    counter = NGramCounter(max_n=3)
    # Add a lot of "abc" so counts are high
    for _ in range(10):
        counter.add_sequence("abc ")
        
    smoother = KneserNeySmoother(counter)
    model_data = smoother.build_model(min_count=1, min_n_to_prune=3)
    
    lm = CharNGramLM(model_data)
    
    # "abc " should have high probability
    prob_abc = lm.score_word("abc ", [])
    
    # "abx " should have lower probability than "abc "
    prob_abx = lm.score_word("abx ", [])
    
    assert prob_abc > prob_abx

    # Test backoff logic: "xbc "
    # We've never seen "x", so it backs off to bigram/unigram.
    prob_xbc = lm.score_word("xbc ", [])
    assert prob_xbc < prob_abc
