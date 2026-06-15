"""Config for GED.

Authors:
    Amir Anwar
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict

GED_ROOT = Path(__file__).parent
DEFAULT_CONFIG_PATH = GED_ROOT / "config.yaml"


def _resolve_path(path: Path, *, base_dir: Path = GED_ROOT) -> Path:
    """Resolve paths relative to the GED root."""
    return path if path.is_absolute() else base_dir / path


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
        return _resolve_path(self.raw_dir) / filename

    def processed_path(self, filename: str) -> Path:
        """Return the path for a processed file."""
        return _resolve_path(self.processed_dir) / filename

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
        """Path generated trie artifacts."""
        return _resolve_path(self.processed_dir)


class LexiconSpellingSuspicionConfig(BaseModel):
    """Feature flags for spelling."""

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
        return _resolve_path(self.patterns_path)


class GEDConfig(BaseModel):
    """Top-level GED service configuration."""

    model_config = ConfigDict(extra="forbid")

    lexicon: LexiconConfig


@lru_cache(maxsize=4)
def load_ged_config(path: str | Path = DEFAULT_CONFIG_PATH) -> GEDConfig:
    """Load and validate GED configuration from YAML."""
    config_path = Path(path)
    with config_path.open(encoding="utf-8") as fh:
        raw_config = yaml.safe_load(fh) or {}
    return GEDConfig.model_validate(raw_config)
