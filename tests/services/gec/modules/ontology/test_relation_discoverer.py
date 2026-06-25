from unittest.mock import MagicMock

from src.core.schemas import MorphAnalysis
from src.services.gec.modules.ontology.relation_discoverer import RelationDiscoverer


def test_relation_discoverer_get_classes():
    discoverer = RelationDiscoverer(loader=MagicMock())

    # Verb
    analysis = MorphAnalysis(
        pos="verb",
        stem="كتب",
        lemma="كتب",
        root="كتب",
        is_disambiguated=True,
        confidence=0.9,
        token_index=0,
    )
    classes = discoverer._get_ontology_classes(analysis)
    assert "http://arabicontology.org/oas_grammar.owl#فعل" in classes

    # Noun
    analysis = MorphAnalysis(
        pos="noun",
        case="nominative",
        stem="مهندس",
        lemma="مهندس",
        root="هندس",
        is_disambiguated=True,
        confidence=0.9,
        token_index=0,
    )
    classes = discoverer._get_ontology_classes(analysis)
    assert "http://arabicontology.org/oas_grammar.owl#اسم" in classes
    assert "http://arabicontology.org/oas_grammar.owl#اسم_مرفوع" in classes


def test_relation_discoverer_check_pair():
    loader = MagicMock()
    # Mock the query result returning relation_uri, relation_name, domain, range
    loader.graph.query.return_value = [
        (
            "http://arabicontology.org/oas_grammar.owl#فاعل",
            "http://arabicontology.org/oas_grammar.owl#اسم_مرفوع",
            "http://arabicontology.org/oas_grammar.owl#فعل",
        )
    ]
    discoverer = RelationDiscoverer(loader=loader)

    # Verb
    verb = MorphAnalysis(
        pos="verb",
        stem="كتب",
        lemma="كتب",
        root="كتب",
        is_disambiguated=True,
        confidence=0.9,
        token_index=0,
    )
    # Noun
    noun = MorphAnalysis(
        pos="noun",
        case="nominative",
        stem="مهندس",
        lemma="مهندس",
        root="هندس",
        is_disambiguated=True,
        confidence=0.9,
        token_index=1,
    )

    features = [[verb], [noun]]

    # So we call _check_pair(1, 0, features, set()) since 1 is noun, 0 is verb
    relations = discoverer._check_pair(1, 0, features)

    assert len(relations) == 1
    assert relations[0].relation_name == "فاعل"
    assert relations[0].source_token_idx == 1
    assert relations[0].target_token_idx == 0
