"""SPARQL queries for the Ontology of Arabic Syntax."""

from .constants import OAS_BASE_URI, OWL_BASE_URI, RDF_BASE_URI, RDFS_BASE_URI

PROPERTIES_QUERY = f"""
PREFIX owl: <{OWL_BASE_URI}>
PREFIX rdfs: <{RDFS_BASE_URI}>
SELECT DISTINCT ?relation ?domain ?range WHERE {{
    ?relation a owl:ObjectProperty .
    ?relation rdfs:domain ?domain .
    ?relation rdfs:range ?range .
}}
"""


def RELATION_RESTRICTIONS_QUERY(relation_uri: str) -> str:
    """Relation restrictions query."""
    return f"""
PREFIX owl: <{OWL_BASE_URI}>
PREFIX rdfs: <{RDFS_BASE_URI}>
PREFIX rdf: <{RDF_BASE_URI}>
PREFIX oas: <{OAS_BASE_URI}>

SELECT DISTINCT ?role ?property ?expectedClass WHERE {{
    {{
        <{relation_uri}> rdfs:domain ?class .
        BIND("domain" AS ?role)
    }} UNION {{
        <{relation_uri}> rdfs:range ?class .
        BIND("range" AS ?role)
    }}

    ?class rdfs:subClassOf* ?targetClass .
    
    {{
        ?targetClass owl:equivalentClass ?rest .
        ?rest owl:onProperty ?property .
        ?rest owl:allValuesFrom ?expectedClass .
    }} UNION {{
        ?targetClass owl:equivalentClass ?rest .
        ?rest owl:intersectionOf ?list .
        ?list rdf:rest*/rdf:first ?item .
        ?item owl:onProperty ?property .
        ?item owl:allValuesFrom ?expectedClass .
    }} UNION {{
        ?targetClass rdfs:subClassOf ?rest .
        ?rest a owl:Restriction .
        ?rest owl:onProperty ?property .
        ?rest owl:allValuesFrom ?expectedClass .
    }}
}}
"""
