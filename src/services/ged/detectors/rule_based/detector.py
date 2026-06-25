"""Rule-based GED detector , public entry point.

This module defines RuleBasedDetector, the concrete BaseDetector
subclass that runs all registered rules (both YAML-loaded and Python
procedural) and returns their combined error spans.

Initialisation order (done when imported)
##################################################################
1. registry.py  , creates the rule_registry singleton.
2. loader.py    , loads all rules/*.yaml files and registers them.
3. orthography.py, syntax.py, punctuation.py
    Python procedural rules register themselves via the
    @rule_registry.register decorator on import.

By the time the RuleBasedDetector class body is evaluated all rules are
already are in the rule_registry.

Authors:
    Amir Anwar
"""

from __future__ import annotations

from pathlib import Path

from loguru import logger

from src.core.schemas import MorphAnalysis, Token
from src.services.ged.detectors.base import BaseDetector

# #########################################################################
# Bootstrap: load YAML rules then import Python rule modules.
# Import order matters:
# 1. registry
# 2. loader (YAML rules)
# 3. rule modules (Python rules).
# #########################################################################
from src.services.ged.detectors.rule_based.loader import (
    load_yaml_rules,  # noqa: E402
)
from src.services.ged.detectors.rule_based.registry import (
    rule_registry,  # noqa: E402
)
from src.services.ged.schemas import ErrorSpan

_RULES_DIR = Path(__file__).parent / "rules"
_yaml_count = load_yaml_rules(_RULES_DIR, rule_registry)
logger.debug("Loaded {} YAML rules from {}", _yaml_count, _RULES_DIR)

# Importing these modules triggers their @rule_registry.register decorators.
import src.services.ged.detectors.rule_based.orthography  # noqa: E402, F401
import src.services.ged.detectors.rule_based.punctuation  # noqa: E402, F401
import src.services.ged.detectors.rule_based.syntax  # noqa: E402, F401

# #########################################################################
# Detector
# #########################################################################


class RuleBasedDetector(BaseDetector):
    """Runs all registered rulebased returns their error spans.

    This class is intentionally small/thin.
    """

    @property
    def name(self) -> str:
        """Subsystem name used for logging and error attribution."""
        return "rule_based"

    def detect(
        self,
        text: str,
        normalized_text: str,  # noqa: ARG002
        tokens: list[Token],
        morph_features: list[list[MorphAnalysis]],
    ) -> list[ErrorSpan]:
        """Run all registered rules and return collected error spans.

        Individual rule failures are caught and logged by the registry
        they do not prevent other rules from running.

        Args:
            text: Original input text
            normalized_text: Normalised version of the text (unused)
            tokens: Token list from preprocessing.
            morph_features: Per-token morphological candidates
                index 0 is the disambiguated candidate.

        Returns:
            Combined list of ErrorSpans
        """
        return rule_registry.run_all(text, tokens, morph_features)

    def list_rules(self):
        """Returns all rules."""
        return rule_registry.list_rules()
