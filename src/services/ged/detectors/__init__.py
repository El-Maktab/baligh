"""Detector interface for the GED service."""

from src.services.ged.detectors.base import BaseDetector
from src.services.ged.detectors.lexicon import LexiconDetector
from src.services.ged.detectors.ml import MLDetector
from src.services.ged.detectors.rule_based import RuleBasedDetector

__all__ = [
    "BaseDetector",
    "LexiconDetector",
    "MLDetector",
    "RuleBasedDetector",
]
