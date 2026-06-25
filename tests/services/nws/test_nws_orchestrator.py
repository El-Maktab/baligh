import pytest
from unittest.mock import MagicMock

from src.core.schemas import Token
from src.services.nws.orchestrator import NWSOrchestrator
from src.services.nws.schemas import NWSInput, NWSSource, Suggestion


@pytest.fixture
def mock_cache_manager():
    manager = MagicMock()
    # By default, pretend cache misses
    manager.lookup.return_value = None
    manager.build_key.return_value = "mock_key"
    return manager


@pytest.fixture
def mock_nwp_model():
    model = MagicMock()
    # By default, return some tuples of (word, score)
    model.predict.return_value = [("المدرسة", 0.9), ("البيت", 0.05)]
    return model


@pytest.fixture
def mock_wac_model():
    model = MagicMock()
    # By default, return some tuples
    model.predict.return_value = [("المعلم", 0.95), ("المعلمات", 0.01)]
    return model


@pytest.fixture
def orchestrator(mock_cache_manager, mock_nwp_model, mock_wac_model):
    return NWSOrchestrator(
        cache_manager=mock_cache_manager,
        nwp_model=mock_nwp_model,
        wac_model=mock_wac_model,
        min_cache_confidence=0.10,
    )


def test_cache_hit_returns_immediately(orchestrator, mock_cache_manager, mock_nwp_model, mock_wac_model):
    """Test that a cache hit bypasses ML models and returns immediately."""
    cached_suggs = [Suggestion(rank=0, word="test", score=1.0, source=NWSSource.USER_CACHE)]
    mock_cache_manager.lookup.return_value = cached_suggs

    input_data = NWSInput(
        tokens=[Token(form="ذهب")],
        morph_features=[],
        current_fragment=None,
        mode="NWP",
        top_k=5
    )

    output = orchestrator.predict(input_data)

    assert output.suggestions == cached_suggs
    mock_nwp_model.predict.assert_not_called()
    mock_wac_model.predict.assert_not_called()


def test_cache_miss_routes_to_wac(orchestrator, mock_cache_manager, mock_wac_model):
    """Test that a cache miss in WAC mode routes to the CharNGramLM and updates cache safely."""
    input_data = NWSInput(
        tokens=[Token(form="ذهب")],
        morph_features=[],
        current_fragment="المع",
        mode="WAC",
        top_k=5
    )

    output = orchestrator.predict(input_data)

    mock_wac_model.predict.assert_called_once_with("ذهب المع", top_k=5)
    
    # We expect 2 suggestions in output
    assert len(output.suggestions) == 2
    assert output.suggestions[0].word == "المعلم"
    assert output.suggestions[0].score == 0.95
    assert output.suggestions[1].word == "المعلمات"
    assert output.suggestions[1].score == 0.01

    # Check that cache was updated ONLY with the high confidence suggestion
    mock_cache_manager.update.assert_called_once()
    cached_args = mock_cache_manager.update.call_args[0][1]
    assert len(cached_args) == 1
    assert cached_args[0].word == "المعلم"


def test_cache_miss_routes_to_nwp(orchestrator, mock_cache_manager, mock_nwp_model):
    """Test that a cache miss in NWP mode routes to the Hybrid Predictor and updates cache safely."""
    input_data = NWSInput(
        tokens=[Token(form="ذهب"), Token(form="إلى")],
        morph_features=[],
        current_fragment=None,
        mode="NWP",
        top_k=5
    )

    output = orchestrator.predict(input_data)

    mock_nwp_model.predict.assert_called_once_with("ذهب إلى", top_k=5)
    
    assert len(output.suggestions) == 2
    
    # Check that cache was updated ONLY with the high confidence suggestion
    mock_cache_manager.update.assert_called_once()
    cached_args = mock_cache_manager.update.call_args[0][1]
    assert len(cached_args) == 1
    assert cached_args[0].word == "المدرسة"


def test_no_cache_update_if_all_low_confidence(orchestrator, mock_cache_manager, mock_nwp_model):
    """Test that the cache is NOT updated if all predictions fall below the confidence threshold."""
    mock_nwp_model.predict.return_value = [("تخريف", 0.05), ("غلط", 0.01)]
    
    input_data = NWSInput(
        tokens=[Token(form="ذهب")],
        morph_features=[],
        current_fragment=None,
        mode="NWP",
        top_k=5
    )

    output = orchestrator.predict(input_data)
    
    assert len(output.suggestions) == 2
    mock_cache_manager.update.assert_not_called()


def test_wac_no_context_only_fragment(orchestrator, mock_wac_model):
    """Test edge case where WAC is called with no preceding tokens, only a fragment."""
    input_data = NWSInput(
        tokens=[],
        morph_features=[],
        current_fragment="المع",
        mode="WAC",
        top_k=5
    )

    orchestrator.predict(input_data)

    # Should just pass the fragment to WAC
    mock_wac_model.predict.assert_called_once_with("المع", top_k=5)


def test_nwp_no_tokens_empty_string(orchestrator, mock_nwp_model):
    """Test edge case where NWP is called with no preceding tokens."""
    input_data = NWSInput(
        tokens=[],
        morph_features=[],
        current_fragment=None,
        mode="NWP",
        top_k=5
    )

    orchestrator.predict(input_data)

    # Should pass empty string to NWP
    mock_nwp_model.predict.assert_called_once_with("", top_k=5)
