"""Shared runtime configuration for the Baligh backend."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNTIME_CONFIG_PATH = REPO_ROOT / "config" / "runtime.yaml"


def _resolve_repo_path(path: Path) -> Path:
    """Resolve a path relative to the repository root."""
    return path if path.is_absolute() else REPO_ROOT / path


class ToggleConfig(BaseModel):
    """Simple enabled/disabled toggle."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True


class ApiConfig(BaseModel):
    """Application-level runtime configuration."""

    model_config = ConfigDict(extra="forbid")

    mongodb_uri: str | None = None
    nws_config_path: Path | None = None

    @property
    def resolved_nws_config_path(self) -> Path | None:
        """Return the optional NWS config path resolved from the repo root."""
        if self.nws_config_path is None:
            return None
        return _resolve_repo_path(self.nws_config_path)


class LexiconDictionaryConfig(BaseModel):
    """Dictionary and trie configuration for lexicon GED."""

    model_config = ConfigDict(extra="forbid")

    raw_dir: Path
    processed_dir: Path
    words_source: str
    entities_source: str
    words_trie: str
    entity_phrases_trie: str
    entity_tokens_trie: str
    metadata: str

    def raw_path(self, filename: str) -> Path:
        """Return the path for a raw file."""
        return _resolve_repo_path(self.raw_dir) / filename

    def processed_path(self, filename: str) -> Path:
        """Return the path for a processed file."""
        return _resolve_repo_path(self.processed_dir) / filename

    @property
    def words_path(self) -> Path:
        """Raw Arabic wordlist path."""
        return self.raw_path(self.words_source)

    @property
    def entities_path(self) -> Path:
        """Raw WIKIFANE entity gazetteer path."""
        return self.raw_path(self.entities_source)

    @property
    def processed_output_dir(self) -> Path:
        """Path to generated trie artifacts."""
        return _resolve_repo_path(self.processed_dir)


class LexiconSpellingSuspicionConfig(BaseModel):
    """Feature flags for lexicon spelling suspicion."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True


class LexiconConfig(BaseModel):
    """Lexicon subsystem configuration."""

    model_config = ConfigDict(extra="forbid")

    patterns_path: Path
    dictionary: LexiconDictionaryConfig
    spelling_suspicion: LexiconSpellingSuspicionConfig = (
        LexiconSpellingSuspicionConfig()
    )

    @property
    def resolved_patterns_path(self) -> Path:
        """Curated pattern YAML path."""
        return _resolve_repo_path(self.patterns_path)


class MLConfig(BaseModel):
    """ML GED model configuration."""

    model_config = ConfigDict(extra="forbid")

    bundle_dir: Path

    @property
    def resolved_bundle_dir(self) -> Path:
        """Return the model path relative to the repo root."""
        return _resolve_repo_path(self.bundle_dir)


class GEDDetectorsConfig(BaseModel):
    """Detector enablement for the GED service."""

    model_config = ConfigDict(extra="forbid")

    rule_based: ToggleConfig = ToggleConfig()
    lexicon: ToggleConfig = ToggleConfig()
    ml: ToggleConfig = ToggleConfig()


class GEDConfig(BaseModel):
    """Top-level GED service configuration."""

    model_config = ConfigDict(extra="forbid")

    detectors: GEDDetectorsConfig = GEDDetectorsConfig()
    lexicon: LexiconConfig
    ml: MLConfig


class GECModulesConfig(BaseModel):
    """Module enablement for the GEC service."""

    model_config = ConfigDict(extra="forbid")

    ontology: ToggleConfig = ToggleConfig()
    dictionary: ToggleConfig = ToggleConfig()
    tagger: ToggleConfig = ToggleConfig()


class GECEditTaggerConfig(BaseModel):
    """Edit-tagger paths and constants."""

    model_config = ConfigDict(extra="forbid")

    model_dir: Path
    raw_data_dir: Path
    processed_data_dir: Path
    test_jsonl_path: Path
    checkpoint_path: Path
    train_sent_path: Path
    train_cor_path: Path
    label2id_path: Path
    id2label_path: Path
    nopnx_train_output: Path
    pnx_train_output: Path
    min_label_frequency: int = 3
    default_label: str = "K"
    unk_label: str = "[UNK_EDIT]"
    pad_label: str = "[PAD]"

    def resolve(self, path: Path) -> Path:
        """Resolve a repo-relative path."""
        return _resolve_repo_path(path)

    @property
    def resolved_model_dir(self) -> Path:
        """Location of the trained edit-tagger model."""
        return self.resolve(self.model_dir)

    @property
    def resolved_raw_data_dir(self) -> Path:
        """Location of raw edit-tagger data."""
        return self.resolve(self.raw_data_dir)

    @property
    def resolved_processed_data_dir(self) -> Path:
        """Location of processed edit-tagger data."""
        return self.resolve(self.processed_data_dir)

    @property
    def resolved_test_jsonl_path(self) -> Path:
        """Path to the test JSONL dataset."""
        return self.resolve(self.test_jsonl_path)

    @property
    def resolved_checkpoint_path(self) -> Path:
        """Path to the training checkpoint JSONL."""
        return self.resolve(self.checkpoint_path)

    @property
    def resolved_train_sent_path(self) -> Path:
        """Path to the training source sentences."""
        return self.resolve(self.train_sent_path)

    @property
    def resolved_train_cor_path(self) -> Path:
        """Path to the training target sentences."""
        return self.resolve(self.train_cor_path)

    @property
    def resolved_label2id_path(self) -> Path:
        """Path to the label2id mapping."""
        return self.resolve(self.label2id_path)

    @property
    def resolved_id2label_path(self) -> Path:
        """Path to the id2label mapping."""
        return self.resolve(self.id2label_path)

    @property
    def resolved_nopnx_train_output(self) -> Path:
        """Path to the non-punctuation training export."""
        return self.resolve(self.nopnx_train_output)

    @property
    def resolved_pnx_train_output(self) -> Path:
        """Path to the punctuation training export."""
        return self.resolve(self.pnx_train_output)


class GECConfig(BaseModel):
    """Top-level GEC service configuration."""

    model_config = ConfigDict(extra="forbid")

    modules: GECModulesConfig = GECModulesConfig()
    edit_tagger: GECEditTaggerConfig


class NWSConfig(BaseModel):
    """NWS runtime section."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True


class RankerRuntimeConfig(BaseModel):
    """Placeholder ranker runtime section."""

    model_config = ConfigDict(extra="allow")


class RuntimeConfig(BaseModel):
    """Unified runtime configuration for the backend."""

    model_config = ConfigDict(extra="forbid")

    api: ApiConfig = ApiConfig()
    ged: GEDConfig
    gec: GECConfig
    nws: NWSConfig = Field(default_factory=NWSConfig)
    ranker: RankerRuntimeConfig = Field(default_factory=RankerRuntimeConfig)


def _normalize_config_path(path: str | Path) -> Path:
    """Resolve config paths relative to the repo root."""
    path_obj = Path(path)
    return path_obj if path_obj.is_absolute() else REPO_ROOT / path_obj


def _read_yaml(path: Path) -> dict:
    """Load a YAML document, defaulting to an empty mapping."""
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


@lru_cache(maxsize=4)
def load_runtime_config(
    path: str | Path = DEFAULT_RUNTIME_CONFIG_PATH,
) -> RuntimeConfig:
    """Load and validate the unified runtime config."""
    config_path = _normalize_config_path(path)
    return RuntimeConfig.model_validate(_read_yaml(config_path))


class Settings:
    """Operational settings with minimal env overrides."""

    def __init__(self, runtime_config: RuntimeConfig | None = None) -> None:
        self.runtime_config = runtime_config or load_runtime_config()

    @property
    def mongodb_uri(self) -> str:
        """Return the configured MongoDB URI."""
        value = os.getenv("MONGODB_URI") or self.runtime_config.api.mongodb_uri
        if not value:
            raise ValueError(
                "MongoDB URI is not configured. Set MONGODB_URI or api.mongodb_uri."
            )
        return value

    @property
    def nws_config_path(self) -> str | None:
        """Return the optional NWS config path."""
        value = os.getenv("NWS_CONFIG_PATH")
        if value is not None:
            return value
        resolved = self.runtime_config.api.resolved_nws_config_path
        return str(resolved) if resolved is not None else None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Build and cache operational settings."""
    return Settings()
