from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel


class ModuleProvenanceConfig(BaseModel):
    W_ONTOLOGY: float = 0.25
    W_TAG: float = 0.15
    W_DICTIONARY: float = 0.10
    W_INDEPENDENT: float = 0.05
    W_GROUP_RANK: float = 0.10


class ConfidenceConfig(BaseModel):
    W_EDIT_CONF: float = 0.30
    W_GED_CONF: float = 0.10
    W_LOW_CONF: float = 0.15
    CONF_LOW_THRESHOLD: float = 0.30


class ProvenanceTierConfig(BaseModel):
    W_TIER1: float = 0.15
    W_TIER2: float = 0.08
    W_TIER3: float = 0.00


class EditCostConfig(BaseModel):
    W_CHAR_DIST: float = 0.10
    W_LENGTH_RATIO: float = 0.05
    W_EMPTY: float = 0.50


class CategoryAlignmentConfig(BaseModel):
    W_SPELL_DICT: float = 0.10
    W_GRAM_ONT: float = 0.10
    W_EXPLAIN: float = 0.05


class AgreementConfig(BaseModel):
    W_AGREEMENT: float = 0.20
    W_MULTI_SRC: float = 0.05


class StructuralConfig(BaseModel):
    W_OOV: float = 0.05
    W_FIRST_ALT: float = 0.05
    W_OP_MISMATCH: float = 0.20


class FeatureTogglesConfig(BaseModel):
    enable_module_provenance: bool = True
    enable_confidence: bool = True
    enable_provenance_tier: bool = True
    enable_edit_cost: bool = True
    enable_category_alignment: bool = True
    enable_agreement: bool = True
    enable_structural: bool = True


class DebugConfig(BaseModel):
    log_score_breakdown: bool = False
    verbosity: int = 0


class RankerConfig(BaseModel):
    module_provenance: ModuleProvenanceConfig = ModuleProvenanceConfig()
    confidence: ConfidenceConfig = ConfidenceConfig()
    provenance_tier: ProvenanceTierConfig = ProvenanceTierConfig()
    edit_cost: EditCostConfig = EditCostConfig()
    category_alignment: CategoryAlignmentConfig = CategoryAlignmentConfig()
    agreement: AgreementConfig = AgreementConfig()
    structural: StructuralConfig = StructuralConfig()
    feature_toggles: FeatureTogglesConfig = FeatureTogglesConfig()
    debug: DebugConfig = DebugConfig()

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
