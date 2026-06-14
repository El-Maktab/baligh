"""Shared test fixtures for rule-based subsystem.

Authors:
    Amir Anwar
"""

from __future__ import annotations

import pytest
from src.core.schemas import MorphAnalysis, Token


def make_token(
    form: str,
    span: tuple[int, int],
    index: int,
    *,
    affix_structure: str | None = None,
    norm_span: tuple[int, int] | None = None,
) -> Token:
    """Build a Token for use in tests."""
    return Token(
        index=index,
        form=form,
        span=span,
        norm_span=norm_span or span,
        affix_structure=affix_structure,
    )


def make_morph(
    token_index: int,
    pos: str,
    *,
    lemma: str | None = None,
    gender: str | None = None,
    number: str | None = None,
    person: str | None = None,
    definiteness: str | None = None,
    case: str | None = None,
    tense: str | None = None,
    voice: str | None = None,
    mood: str | None = None,
    diacritized: str | None = None,
    is_disambiguated: bool = True,
) -> MorphAnalysis:
    """Build a MorphAnalysis for use in tests."""
    return MorphAnalysis(
        token_index=token_index,
        pos=pos,
        lemma=lemma,
        gender=gender,
        number=number,
        person=person,
        definiteness=definiteness,
        case=case,
        tense=tense,
        voice=voice,
        mood=mood,
        diacritized=diacritized,
        is_disambiguated=is_disambiguated,
    )


# Pytest fixtures


@pytest.fixture()
def token_factory():
    """Return the make_token factory function."""
    return make_token


@pytest.fixture()
def morph_factory():
    """Return the make_morph factory function."""
    return make_morph
