"""Translates CAMeL morph features to internal domain for Ontology."""

from pydantic import BaseModel

from src.services.ged.schemas import MorphAnalysis


class InternalMorphFeatures(BaseModel):
    """Standardized representation of morphological features used within GEC."""

    pos: str
    gender: str | None = None
    number: str | None = None
    person: str | None = None
    definiteness: str | None = None
    case: str | None = None
    tense: str | None = None
    voice: str | None = None
    mood: str | None = None
    lemma: str | None = None
    diacritized: str | None = None
    affix_structure: str | None = None


def normalize_camel(analysis: MorphAnalysis | dict) -> InternalMorphFeatures:
    """Normalizes CAMeL morph features into a clean InternalMorphFeatures model.

    Args:
        analysis: A MorphAnalysis object or a raw dictionary containing
            morphological features.

    Returns:
        InternalMorphFeatures: The normalized, standardized feature set.
    """
    if isinstance(analysis, MorphAnalysis):
        data = analysis.model_dump()
    elif isinstance(analysis, dict):
        data = analysis
    else:
        raise TypeError("analysis must be a MorphAnalysis instance or a dictionary")

    def clean_str(val: str | None) -> str | None:
        if val is None:
            return None
        stripped = val.strip().lower()
        return stripped if stripped else None

    pos = clean_str(data.get("pos")) or "unknown"

    return InternalMorphFeatures(
        pos=pos,
        gender=clean_str(data.get("gender")),
        number=clean_str(data.get("number")),
        person=clean_str(data.get("person")),
        definiteness=clean_str(data.get("definiteness")),
        case=clean_str(data.get("case")),
        tense=clean_str(data.get("tense")),
        voice=clean_str(data.get("voice")),
        mood=clean_str(data.get("mood")),
        lemma=data.get("lemma"),  # Keep lemma unchanged (Arabic string)
        diacritized=data.get("diacritized"),
        affix_structure=data.get("affix_structure"),
    )
