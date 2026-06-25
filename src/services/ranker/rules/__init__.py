from src.services.ranker.config import RankerConfig, FeatureTogglesConfig
from src.services.ranker.rules.module_provenance import (
    OntologyBonusRule,
    TagBonusRule,
    DictionaryBonusRule,
    OntologyIndependentRule,
    OntologyGroupRankRule,
)
from src.services.ranker.rules.confidence import (
    EditConfidenceRule,
    GEDConfidenceRule,
    LowConfidencePenaltyRule,
)
from src.services.ranker.rules.provenance_tier import (
    Tier1BoostRule,
    Tier2BoostRule,
    Tier3DampenRule,
)
from src.services.ranker.rules.edit_cost import (
    CharDistanceRule,
    LengthRatioRule,
    EmptyCorrectionRule,
)
from src.services.ranker.rules.category_alignment import (
    SpellingDictRule,
    GrammarOntologyRule,
    ExplanationBonusRule,
)
from src.services.ranker.rules.agreement import (
    MultiModuleAgreementRule,
    GEDMultiSourceRule,
)
from src.services.ranker.rules.structural import (
    OOVTokenRule,
    IdenticalEditRule,
    DictionaryFirstAltRule,
    OperationMismatchRule,
)
from src.services.ranker.rules.base import BaseRule


_MODULE_PROVENANCE_RULES = [
    OntologyBonusRule,
    TagBonusRule,
    DictionaryBonusRule,
    OntologyIndependentRule,
    OntologyGroupRankRule,
]
_CONFIDENCE_RULES = [
    EditConfidenceRule,
    GEDConfidenceRule,
    LowConfidencePenaltyRule,
]
_PROVENANCE_TIER_RULES = [
    Tier1BoostRule,
    Tier2BoostRule,
    Tier3DampenRule,
]
_EDIT_COST_RULES = [
    CharDistanceRule,
    LengthRatioRule,
    EmptyCorrectionRule,
]
_CATEGORY_ALIGNMENT_RULES = [
    SpellingDictRule,
    GrammarOntologyRule,
    ExplanationBonusRule,
]
_AGREEMENT_RULES = [
    MultiModuleAgreementRule,
    GEDMultiSourceRule,
]
_STRUCTURAL_RULES = [
    OOVTokenRule,
    IdenticalEditRule,
    DictionaryFirstAltRule,
    OperationMismatchRule,
]


_RULE_GROUPS: list[tuple[str, list[type[BaseRule]]]] = [
    ("enable_module_provenance", _MODULE_PROVENANCE_RULES),
    ("enable_confidence", _CONFIDENCE_RULES),
    ("enable_provenance_tier", _PROVENANCE_TIER_RULES),
    ("enable_edit_cost", _EDIT_COST_RULES),
    ("enable_category_alignment", _CATEGORY_ALIGNMENT_RULES),
    ("enable_agreement", _AGREEMENT_RULES),
    ("enable_structural", _STRUCTURAL_RULES),
]


def get_all_rules(config: RankerConfig) -> list[BaseRule]:
    toggles: FeatureTogglesConfig = config.feature_toggles
    rules: list[BaseRule] = []
    for toggle_name, rule_classes in _RULE_GROUPS:
        if getattr(toggles, toggle_name, False):
            for cls in rule_classes:
                rules.append(cls())
    return rules


__all__ = [
    "get_all_rules",
    "BaseRule",
]
