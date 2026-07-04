"""Tests for the unified runtime configuration."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError
from src.runtime_config import (
    DEFAULT_RUNTIME_CONFIG_PATH,
    Settings,
    load_runtime_config,
)


def test_runtime_config_loads_default_file() -> None:
    """The repo runtime config should load with valid file-backed values."""
    config = load_runtime_config()

    assert DEFAULT_RUNTIME_CONFIG_PATH.exists()
    assert isinstance(config.ged.detectors.rule_based.enabled, bool)
    assert isinstance(config.ged.detectors.lexicon.enabled, bool)
    assert isinstance(config.ged.detectors.ml.enabled, bool)
    assert isinstance(config.gec.modules.ontology.enabled, bool)
    assert isinstance(config.gec.modules.dictionary.enabled, bool)
    assert isinstance(config.gec.modules.tagger.enabled, bool)
    assert isinstance(config.nws.enabled, bool)
    assert config.ged.lexicon.resolved_patterns_path.exists()
    assert config.gec.edit_tagger.resolved_model_dir == (
        Path("src/services/gec/models/edit_tagger_v1/checkpoint-3642").resolve()
    )


def test_runtime_config_rejects_invalid_toggle_value(tmp_path: Path) -> None:
    """Invalid enabled flags should fail validation clearly."""
    config_path = tmp_path / "runtime.yaml"
    config_path.write_text(
        """
api:
  mongodb_uri: mongodb://localhost:27017/test
ged:
  detectors:
    rule_based:
      enabled: definitely
  lexicon:
    patterns_path: src/services/ged/detectors/lexicon/resources/patterns.yaml
    dictionary:
      raw_dir: src/services/ged/detectors/lexicon/dictionary
      processed_dir: src/services/ged/detectors/lexicon/dictionary/processed
      words_source: arabic-wordlist-1.6.txt
      entities_source: WIKIFANE_gazet_NE_wordlist.txt
      words_trie: words.marisa
      entity_phrases_trie: entity_phrases.marisa
      entity_tokens_trie: entity_tokens.marisa
      metadata: metadata.json
  ml:
    bundle_dir: artifacts/ged/ml/crf-surface-morph-v2/v0.2.0
gec:
  edit_tagger:
    model_dir: src/services/gec/models/edit_tagger_v1/checkpoint-3642
    raw_data_dir: src/services/gec/data/edit_tagger/raw
    processed_data_dir: src/services/gec/data/edit_tagger/processed
    test_jsonl_path: src/services/gec/data/edit_tagger/processed/test_tokens_labels
    checkpoint_path: src/services/gec/data/edit_tagger/processed/tokens_labels.jsonl
    train_sent_path: src/services/gec/data/edit_tagger/raw/train/QALB-2014-L1-Train.sent
    train_cor_path: src/services/gec/data/edit_tagger/raw/train/QALB-2014-L1-Train.cor
    label2id_path: src/services/gec/data/edit_tagger/processed/label2id.json
    id2label_path: src/services/gec/data/edit_tagger/processed/id2label.json
    nopnx_train_output: src/services/gec/data/edit_tagger/processed/qalb14_nopnx_train.jsonl
    pnx_train_output: src/services/gec/data/edit_tagger/processed/qalb14_pnx_train.jsonl
""",
        encoding="utf-8",
    )

    with pytest.raises(ValidationError):
        load_runtime_config.cache_clear()
        load_runtime_config(config_path)


def test_settings_allow_minimal_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """Operational env vars should override the file-backed config."""
    config = load_runtime_config()
    monkeypatch.setenv("MONGODB_URI", "mongodb://override:27017/baligh")
    settings = Settings(runtime_config=config)

    assert settings.mongodb_uri == "mongodb://override:27017/baligh"
