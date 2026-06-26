"""Helpers for exposing the GED rule catalog to the frontend."""

from __future__ import annotations

from src.api.services.editor_contract import (
    GrammarRuleResponse,
    RuleCategory,
    RuleCategoryOptionResponse,
)
from src.services.ged.detectors.rule_based.detector import RuleBasedDetector
from src.services.ged.detectors.rule_based.models import RuleEntry
from src.services.ged.schemas import ErrorCategory

_RULE_DETECTOR = RuleBasedDetector()
_CATEGORY_LABELS: dict[RuleCategory, str] = {
    RuleCategory.SYNTAX: "النحو",
    RuleCategory.ORTHOGRAPHY: "الإملاء",
    RuleCategory.PUNCTUATION: "الترقيم",
    RuleCategory.SEMANTICS: "الاستعمال",
    RuleCategory.MORPHOLOGY: "الصرف",
    RuleCategory.MERGE: "الدمج",
    RuleCategory.SPLIT: "الفصل",
}
_CATEGORY_ORDER = [
    RuleCategory.SYNTAX,
    RuleCategory.ORTHOGRAPHY,
    RuleCategory.PUNCTUATION,
    RuleCategory.MORPHOLOGY,
    RuleCategory.SEMANTICS,
    RuleCategory.MERGE,
    RuleCategory.SPLIT,
]


def _to_rule_category(category: ErrorCategory) -> RuleCategory:
    """Map GED error categories to the rules browser taxonomy."""
    if category == ErrorCategory.ORTHOGRAPHY:
        return RuleCategory.ORTHOGRAPHY
    if category == ErrorCategory.PUNCTUATION:
        return RuleCategory.PUNCTUATION
    if category == ErrorCategory.MORPHOLOGY:
        return RuleCategory.MORPHOLOGY
    if category == ErrorCategory.SYNTAX:
        return RuleCategory.SYNTAX
    if category == ErrorCategory.MERGE:
        return RuleCategory.MERGE
    if category == ErrorCategory.SPLIT:
        return RuleCategory.SPLIT
    return RuleCategory.SEMANTICS


def _build_rule_title(rule: RuleEntry) -> str:
    """Use the GED explanation as the primary UI title when available."""
    title = (rule.explanation or "").strip()
    if title:
        return title
    return rule.rule_id.replace("_", " ")


def normalize_rule(rule: RuleEntry) -> GrammarRuleResponse:
    """Convert a GED rule entry into the frontend rules contract."""
    explanation = (rule.explanation or "").strip()
    return GrammarRuleResponse(
        id=rule.rule_id,
        category=_to_rule_category(rule.category),
        subtype=rule.subtype or "",
        tier=rule.tier.value,
        title=_build_rule_title(rule),
        explanation=explanation,
        incorrect="",
        correct="",
        note="",
    )


def list_rules() -> list[GrammarRuleResponse]:
    """Return the normalized GED rule catalog."""
    rules = _RULE_DETECTOR.list_rules()
    normalized = [normalize_rule(rule) for rule in rules]
    return sorted(normalized, key=lambda rule: (rule.category.value, rule.id))


def list_rule_categories() -> list[RuleCategoryOptionResponse]:
    """Return category options derived from the available rule catalog."""
    present_categories = {rule.category for rule in list_rules()}
    ordered_categories = [
        category for category in _CATEGORY_ORDER if category in present_categories
    ]
    return [RuleCategoryOptionResponse(value="all", label="الكل")] + [
        RuleCategoryOptionResponse(
            value=category,
            label=_CATEGORY_LABELS.get(category, category.value),
        )
        for category in ordered_categories
    ]
