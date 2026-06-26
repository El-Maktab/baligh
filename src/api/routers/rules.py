"""Routers for the GED rules reference catalog."""

from fastapi import APIRouter
from src.api.services.editor_contract import (
    GrammarRuleResponse,
    RuleCategoryOptionResponse,
)
from src.api.services.rules import list_rule_categories, list_rules

router = APIRouter()


@router.get("", response_model=list[GrammarRuleResponse])
async def get_rules():
    """Return the normalized GED rule catalog."""
    return list_rules()


@router.get("/categories", response_model=list[RuleCategoryOptionResponse])
async def get_rule_categories():
    """Return the rule category filters used by the frontend."""
    return list_rule_categories()
