"""Tests for the feature adaptation and mapping pipeline."""

from src.core.schemas import MorphAnalysis
from src.services.gec.features.camel_adapter import (
    InternalMorphFeatures,
    normalize_camel,
)
from src.services.gec.features.ontology_mapper import BASE_URI, map_to_ontology_concepts


def test_feature_mapper_pipeline():
    """Test full adapter and mapper flow using a MorphAnalysis object."""
    noun_analysis = MorphAnalysis(
        token_index=0,
        lemma="طالب",
        pos="NOUN",
        gender="masculine",
        number="plural",
        person=None,
        definiteness="definite",
        case="nominative",
        tense=None,
        voice=None,
        mood=None,
        diacritized="الطُّلَابُ",
        affix_structure="DET+STEM",
        is_disambiguated=True,
    )

    # 1. Normalize
    internal_features = normalize_camel(noun_analysis)
    assert isinstance(internal_features, InternalMorphFeatures)
    assert internal_features.pos == "noun"
    assert internal_features.gender == "masculine"
    assert internal_features.number == "plural"
    assert internal_features.definiteness == "definite"
    assert internal_features.case == "nominative"
    assert internal_features.lemma == "طالب"

    # 2. Map to Ontology
    ontology_concepts = map_to_ontology_concepts(internal_features)
    assert ontology_concepts["pos"] == f"{BASE_URI}اسم"
    assert ontology_concepts["gender"] == f"{BASE_URI}مذكر"
    assert ontology_concepts["number"] == f"{BASE_URI}جمع"
    assert ontology_concepts["definiteness"] == f"{BASE_URI}معرفة"
    assert ontology_concepts["case"] == f"{BASE_URI}اسم_مرفوع"


def test_feature_mapper_dict_input():
    """Test adapter and mapper with raw dictionary input representing MorphAnalysis."""
    raw_dict = {
        "token_index": 1,
        "pos": "VERB",
        "gender": "feminine",
        "number": "singular",
        "case": None,
    }

    # 1. Normalize
    internal_features = normalize_camel(raw_dict)
    assert internal_features.pos == "verb"
    assert internal_features.gender == "feminine"
    assert internal_features.number == "singular"
    assert internal_features.case is None

    # 2. Map to Ontology
    ontology_concepts = map_to_ontology_concepts(internal_features)
    assert ontology_concepts["pos"] == f"{BASE_URI}فعل"
    assert ontology_concepts["gender"] == f"{BASE_URI}مؤنث"
    assert ontology_concepts["number"] == f"{BASE_URI}مفرد"
    assert ontology_concepts["case"] is None
