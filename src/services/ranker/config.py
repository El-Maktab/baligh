from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel


class RankerConfig(BaseModel):
    W_ONTOLOGY: float = 0.25
    W_TAG: float = 0.15
    W_DICTIONARY: float = 0.10
    W_INDEPENDENT: float = 0.05
    W_GROUP_RANK: float = 0.10
    W_EDIT_CONF: float = 0.30
    W_GED_CONF: float = 0.10
    W_LOW_CONF: float = 0.15
    CONF_LOW_THRESHOLD: float = 0.30
    W_TIER1: float = 0.15
    W_TIER2: float = 0.08
    W_TIER3: float = 0.00
    W_CHAR_DIST: float = 0.10
    W_LENGTH_RATIO: float = 0.05
    W_EMPTY: float = 0.50
    W_SPELL_DICT: float = 0.10
    W_GRAM_ONT: float = 0.10
    W_EXPLAIN: float = 0.05
    W_AGREEMENT: float = 0.20
    W_MULTI_SRC: float = 0.05
    W_OOV: float = 0.05
    W_FIRST_ALT: float = 0.05
    W_OP_MISMATCH: float = 0.20

    @classmethod
    def from_yaml(cls, path: Path | str | None = None) -> RankerConfig:
        if path is None:
            path = Path(__file__).parent / "config.yaml"
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(**data)


_DEFAULT_CONFIG: RankerConfig | None = None


def get_ranker_config(path: Path | str | None = None) -> RankerConfig:
    global _DEFAULT_CONFIG
    if _DEFAULT_CONFIG is None:
        _DEFAULT_CONFIG = RankerConfig.from_yaml(path)
    return _DEFAULT_CONFIG