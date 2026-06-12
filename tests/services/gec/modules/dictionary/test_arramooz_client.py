"""Tests for ArramoozClient."""

import pytest
from src.services.gec.modules.dictionary.arramooz_client import ArramoozClient


@pytest.mark.asyncio
async def test_arramooz_client_init():
    """Test that ArramoozClient initializes nouns and verbs dictionaries."""
    client = ArramoozClient()
    assert client.nouns_dict is not None
    assert client.verbs_dict is not None


@pytest.mark.asyncio
async def test_check_word_exists():
    """Test check_word_exists with valid and invalid words."""
    client = ArramoozClient()

    # Valid noun and verb
    assert await client.check_word_exists("مدرسة") is True
    assert await client.check_word_exists("كتب") is True

    # Invalid word
    assert await client.check_word_exists("مردسةتف") is False


@pytest.mark.asyncio
async def test_get_word_features():
    """Test that get_word_features retrieves expected attributes for a word."""
    client = ArramoozClient()
    features = await client.get_word_features("مدرسة")

    assert len(features) > 0
    assert any(f.get("root") == "درس" for f in features)
    assert any(f.get("table") == "nouns" for f in features)
    assert any(f.get("vocalized") == "مَدْرَسَةٌ" for f in features)
