"""Config for NWS.

Authors:
    - Akram Hany
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict

NWS_ROOT = Path(__file__).parent
DEFAULT_CONFIG_PATH = NWS_ROOT / "config.yaml"


def _resolve_path(path: Path, *, base_dir: Path = NWS_ROOT) -> Path:
    """Resolve paths relative to the NWS root."""
    return path if path.is_absolute() else base_dir / path


class NWSCacheConfig(BaseModel):
    """Configuration for NWS cache layers."""

    model_config = ConfigDict(extra="forbid")

    idioms_path: Path
    phrases_path: Path
    user_lru_maxsize: int

    @property
    def resolved_idioms_path(self) -> Path:
        """Resolved path to the static idioms cache YAML file."""
        return _resolve_path(self.idioms_path)

    @property
    def resolved_phrases_path(self) -> Path:
        """Resolved path to the static famous phrases cache YAML file."""
        return _resolve_path(self.phrases_path)


class NWSWacConfig(BaseModel):
    """Configuration for WAC (Word Auto-Completion) pipeline."""

    model_config = ConfigDict(extra="forbid")

    trie_path: Path

    @property
    def resolved_trie_path(self) -> Path:
        """Resolved path to the WAC marisa-trie file."""
        return _resolve_path(self.trie_path)


class NWSNwpConfig(BaseModel):
    """Configuration for NWP (Next-Word Prediction) pipeline."""

    model_config = ConfigDict(extra="forbid")

    model_path: Path

    @property
    def resolved_model_path(self) -> Path:
        """Resolved path to the language model file."""
        return _resolve_path(self.model_path)


class NWSConfig(BaseModel):
    """Top-level NWS service configuration."""

    model_config = ConfigDict(extra="forbid")

    context_window_size: int
    top_k_default: int
    cache: NWSCacheConfig
    wac: NWSWacConfig
    nwp: NWSNwpConfig


@lru_cache(maxsize=4)
def load_nws_config(path: str | Path = DEFAULT_CONFIG_PATH) -> NWSConfig:
    """Load and validate NWS configuration from YAML."""
    config_path = Path(path)
    with config_path.open(encoding="utf-8") as fh:
        raw_config = yaml.safe_load(fh) or {}
    return NWSConfig.model_validate(raw_config)
