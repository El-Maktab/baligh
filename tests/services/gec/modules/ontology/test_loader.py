"""Tests for OntologyLoader."""

from src.services.gec.modules.ontology.loader import OntologyLoader


def test_ontology_loader_singleton():
    """Test that OntologyLoader correctly enforces the singleton pattern."""
    loader1 = OntologyLoader()
    loader2 = OntologyLoader()
    assert loader1 is loader2


def test_ontology_loader_load_and_query():
    """Test that oas_grammar.owl is parsed and can be queried via SPARQL."""
    loader = OntologyLoader()
    loader.load_graph()
    assert loader.is_loaded is True

    # Simple SPARQL query to select a single triple
    query_str = """
    SELECT ?s ?p ?o
    WHERE {
        ?s ?p ?o
    }
    LIMIT 1
    """
    results = list(loader.query(query_str))
    assert len(results) == 1

    # subject, predicate, object
    assert len(results[0]) == 3  # type: ignore
