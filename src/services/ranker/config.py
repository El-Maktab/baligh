from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel

class RankingConfig(BaseModel):
    min_candidate_confidence: float = 0.1
    ontology_bonus: float = 0.1
    dictionary_bonus: float = 0.05
    tag_bonus: float = 0.0

