"""Tests for exposing GED rules to the frontend catalog."""

from src.api.services.rules import list_rule_categories, list_rules


def test_list_rules_returns_normalized_catalog_items():
    """Rules should be normalized into the frontend contract."""
    rules = list_rules()

    assert rules
    assert any(rule.id == "SY_LAM_JUSSIVE" for rule in rules)
    assert all(rule.title for rule in rules)
    assert all(rule.incorrect == "" for rule in rules)
    assert all(rule.correct == "" for rule in rules)


def test_list_rules_exposes_punctuation_as_its_own_bucket():
    """Punctuation rules should remain visible as a separate rules category."""
    rules = list_rules()
    punctuation_rule = next(rule for rule in rules if rule.id == "PC_SPACE_BEFORE_PUNC")

    assert punctuation_rule.category.value == "punctuation"


def test_list_rule_categories_matches_frontend_filters():
    """The backend category options should match the rules browser tabs."""
    categories = list_rule_categories()

    assert [category.value for category in categories] == [
        "all",
        "syntax",
        "orthography",
        "punctuation",
        "semantics",
    ]
