"""Tests for ArramoozClient."""

from src.services.gec.modules.dictionary.arramooz_client import ArramoozClient


def test_arramooz_client_init():
    """Test that ArramoozClient initializes dictionary connection."""
    client = ArramoozClient()
    assert client._dict_conn is not None


def test_check_word_exists():
    """Test check_word_exists with valid and invalid words."""
    client = ArramoozClient()

    assert client.check_word_exists("مدرسة") is True
    assert client.check_word_exists("كتب") is True


def test_get_word_features():
    """Test that get_word_features retrieves expected attributes for a word."""
    client = ArramoozClient()
    features = client.get_word_features("مدرسة")

    assert len(features) > 0
    assert any(f.get("root") == "درس" for f in features)
    assert any(f.get("table") == "nouns" for f in features)
    assert any(f.get("vocalized") == "مَدْرَسَةٌ" for f in features)
