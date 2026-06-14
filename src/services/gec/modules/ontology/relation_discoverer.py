"""Generic relation discovery from the Arabic Syntax Ontology."""

from typing import Any

from loguru import logger
from pydantic import BaseModel
from rdflib import BNode, Node, URIRef
from rdflib.collection import Collection

from src.core.schemas import MorphAnalysis, Token
from src.core.utils.features import get_disambiguated_analysis
from src.services.gec.features.camel_adapter import (
    InternalMorphFeatures,
    normalize_camel,
)
from src.services.gec.modules.ontology.constants import (
    EQUIVALENT_CLASS_URI,
    INTERSECTION_OF_URI,
    NOUN_CASES,
    OAS_NOUN_CASE_ACCUSATIVE_URI,
    OAS_NOUN_CASE_GENITIVE_URI,
    OAS_NOUN_CASE_NOMINATIVE_URI,
    OAS_NOUN_DEFINITE_URI,
    OAS_NOUN_INDEFINITE_URI,
    OAS_NOUN_URI,
    OAS_VERB_MOOD_INDICATIVE_URI,
    OAS_VERB_MOOD_JUSSIVE_URI,
    OAS_VERB_MOOD_SUBJUNCTIVE_URI,
    OAS_VERB_TAM_URI,
    OAS_VERB_URI,
    SUBCLASS_OF_URI,
    UNION_OF_URI,
    VERB_MOODS,
)
from src.services.gec.modules.ontology.loader import OntologyLoader
from src.services.gec.modules.ontology.sparql_queries import PROPERTIES_QUERY


class RelationMetadata(BaseModel):
    """Metadata for a discovered grammatical relation."""

    relation_uri: str
    relation_name: str
    domain_class: str
    range_class: str
    source_token_idx: int
    target_token_idx: int
    priority: int = 0  # Lower is better (more specific)


def _to_rdf_term(val: Any) -> Any:
    """Converts a value to its appropriate RDF term (URIRef or BNode)."""
    if isinstance(val, URIRef | BNode):
        return val
    if isinstance(val, str):
        if val.startswith("_:"):
            return BNode(val[2:])
        return URIRef(val)
    return val


class RelationDiscoverer:
    """Discovers all applicable grammatical relations dynamically from ontology."""

    def __init__(self, loader: OntologyLoader) -> None:
        """Initializes the RelationDiscoverer."""
        self._loader = loader
        self._properties: list[tuple[URIRef, str, URIRef, URIRef]] = []
        self._loaded = False

    def _ensure_properties(self) -> None:
        """Ensures that all object properties are loaded from the ontology."""
        if self._loaded:
            return

        self._loader.load_graph()
        g = self._loader.graph

        try:
            results = g.query(PROPERTIES_QUERY)
            for row in results:
                if isinstance(row, bool):
                    continue
                rel = _to_rdf_term(row[0])
                domain = _to_rdf_term(row[1])
                range_ = _to_rdf_term(row[2])
                rel_name = str(rel).split("#")[-1]
                self._properties.append((rel, rel_name, domain, range_))
        except Exception as e:
            logger.error("Failed to load ObjectProperties from ontology: {}", e)

        self._loaded = True

    def discover_relations(
        self,
        tokens: list[Token],
        morph_features: list[list[MorphAnalysis]],
    ) -> list[RelationMetadata]:
        """Discovers all applicable grammatical relations between tokens."""
        relations = []

        for i in range(len(tokens) - 1):
            for j in range(i + 1, len(tokens)):
                relations.extend(self._check_pair(i, j, morph_features))
                relations.extend(self._check_pair(j, i, morph_features))

        # Global filtering: for each token pair, keep only best priority relations
        if relations:
            # Group by unordered (source, target) pair
            pair_best: dict[frozenset, list[RelationMetadata]] = {}
            for r in relations:
                # Use frozenset to group both directions of same pair
                pair = frozenset([r.source_token_idx, r.target_token_idx])
                if pair not in pair_best:
                    pair_best[pair] = []
                pair_best[pair].append(r)

            # Keep only best priority relations for each pair
            filtered = []
            for rels in pair_best.values():
                rels.sort(key=lambda r: r.priority)
                best_priority = rels[0].priority
                filtered.extend([r for r in rels if r.priority == best_priority])

            relations = filtered

        # Deduplicate by (relation_name, source, target)
        seen = set()
        deduped = []
        for r in relations:
            key = (r.relation_name, r.source_token_idx, r.target_token_idx)
            if key not in seen:
                seen.add(key)
                deduped.append(r)

        return deduped

    def _get_union_members(self, graph: Any, class_uri: URIRef) -> list[URIRef]:
        """Gets all members of an owl:unionOf class restriction."""
        members: list[URIRef] = []

        for union_node in graph.objects(class_uri, URIRef(UNION_OF_URI)):
            coll = Collection(graph, union_node)

            for item in coll:
                if isinstance(item, URIRef):
                    members.append(item)

        return members

    def _is_subclass_of(
        self,
        graph: Any,
        cls1: Node,
        cls2: Node,
        visited: set[Node] | None = None,
    ) -> bool:
        """Helper to recursively check if cls1 is a subclass of cls2."""
        if cls1 == cls2:
            return True

        if visited is None:
            visited = set()

        if cls1 in visited:
            return False

        visited.add(cls1)

        for parent in graph.objects(cls1, URIRef(SUBCLASS_OF_URI)):
            if self._is_subclass_of(graph, parent, cls2, visited):
                return True

        for equiv in graph.objects(cls1, URIRef(EQUIVALENT_CLASS_URI)):
            if self._is_subclass_of(graph, equiv, cls2, visited):
                return True

            for intersection in graph.objects(equiv, URIRef(INTERSECTION_OF_URI)):
                for item in Collection(graph, intersection):
                    if self._is_subclass_of(graph, item, cls2, visited):
                        return True

        return False

    def _is_case_or_mood_class(self, class_uri: URIRef) -> bool:
        """Checks if a class is an arabic case or mood class."""
        name = str(class_uri).split("#")[-1]
        return name in (NOUN_CASES + VERB_MOODS)

    def _check_compatibility(
        self,
        graph: Any,
        token_class: URIRef,
        expected_class: URIRef,
    ) -> bool:
        """Checks if a token class is compatible with an expected domain/range class."""
        if token_class == expected_class:
            return True

        union_members = self._get_union_members(graph, expected_class)
        if union_members:
            return any(
                self._check_compatibility(graph, token_class, member)
                for member in union_members
            )

        token_members = self._get_union_members(graph, token_class)
        if token_members:
            return any(
                self._check_compatibility(graph, member, expected_class)
                for member in token_members
            )

        if self._is_case_or_mood_class(expected_class):
            if self._is_subclass_of(graph, expected_class, token_class):
                return True

        if self._is_subclass_of(graph, token_class, expected_class):
            return True

        return False

    def _check_pair(
        self,
        source_idx: int,
        target_idx: int,
        morph_features: list[list[MorphAnalysis]],
    ) -> list[RelationMetadata]:
        """Checks for relations where source_idx is domain and target_idx is range."""
        self._ensure_properties()

        source_analysis = get_disambiguated_analysis(morph_features, source_idx)
        target_analysis = get_disambiguated_analysis(morph_features, target_idx)

        if not source_analysis or not target_analysis:
            return []

        source_internal = normalize_camel(source_analysis)
        target_internal = normalize_camel(target_analysis)

        source_classes = self._get_ontology_classes(source_analysis)
        target_classes = self._get_ontology_classes(target_analysis)

        if not source_classes or not target_classes:
            return []

        g = self._loader.graph
        relations = []

        for rel_uri, rel_name, domain_class, range_class in self._properties:
            domain_match = any(
                self._check_compatibility(g, URIRef(src), domain_class)
                for src in source_classes
            )
            range_match = any(
                self._check_compatibility(g, URIRef(tgt), range_class)
                for tgt in target_classes
            )

            if domain_match and range_match:
                # Calculate priority based on POS specificity
                priority = self._calculate_priority(
                    rel_name, source_internal, target_internal
                )
                relations.append(
                    RelationMetadata(
                        relation_uri=str(rel_uri),
                        relation_name=rel_name,
                        domain_class=str(domain_class),
                        range_class=str(range_class),
                        source_token_idx=source_idx,
                        target_token_idx=target_idx,
                        priority=priority,
                    )
                )

        # Sort by priority and filter to keep only best relations
        if relations:
            # Group by (source, target) pair and keep best priority per pair
            pair_best: dict[tuple[int, int], list[RelationMetadata]] = {}
            for r in relations:
                pair = (r.source_token_idx, r.target_token_idx)
                if pair not in pair_best:
                    pair_best[pair] = []
                pair_best[pair].append(r)

            # Keep only best priority relations for each pair
            filtered = []
            for rels in pair_best.values():
                rels.sort(key=lambda r: r.priority)
                best_priority = rels[0].priority
                filtered.extend([r for r in rels if r.priority == best_priority])

            relations = filtered

        # Deduplicate by (relation_name, source, target)
        seen = set()
        deduped = []
        for r in relations:
            key = (r.relation_name, r.source_token_idx, r.target_token_idx)
            if key not in seen:
                seen.add(key)
                deduped.append(r)

        return deduped

    def _calculate_priority(
        self,
        rel_name: str,
        source_internal: InternalMorphFeatures,
        target_internal: InternalMorphFeatures,
    ) -> int:
        """Calculates priority for a relation based on POS specificity.

        Lower priority = better match. Priority rules:
        - Adjective relations (نعت) get priority 0 when target is adj
        - Idafa relations get priority 0 when target is definite genitive
        - Subject-verb (فاعل) gets priority 0 for noun-verb pairs
        - Badal relations get priority 10 (less specific)
        - Tamyeez relations get priority 8 (less specific than idafa)
        - Object relations get priority 7 (less specific than subject)
        - Other relations get priority 5
        """
        # نعت (adjective) relation should be preferred when target is adjective
        if rel_name == "نعت" and target_internal.pos == "adj":
            return 0

        # مضاف_اليه (idafa) should be preferred when:
        # - source is indefinite (نكرة)
        # - target is definite (معرفة) and genitive
        if rel_name == "مضاف_اليه":
            if (
                source_internal.definiteness == "indefinite"
                and target_internal.definiteness == "definite"
                and target_internal.case == "genitive"
            ):
                return 0

        # فاعل (subject) should be preferred for noun-verb pairs
        if rel_name == "فاعل":
            if source_internal.pos in ("noun", "adj") and target_internal.pos == "verb":
                return 0

        # نائب_الفاعل (passive subject) also for noun-verb pairs
        if rel_name == "نائب_الفاعل":
            if source_internal.pos in ("noun", "adj") and target_internal.pos == "verb":
                return 0

        # تمييز_ذات (tamyeez) is less specific than idafa
        if rel_name == "تمييز_ذات":
            return 8

        # تمييز_نسبة (tamyeez) is also less specific
        if rel_name == "تمييز_نسبة":
            return 8

        # Object relations (مفعول) are less specific than subject
        if rel_name.startswith("مفعول"):
            return 7

        # بدل (badal/apposition) is less specific, give lower priority
        if rel_name.startswith("بدل"):
            return 10

        # توكيد (emphasis) is also less specific
        if rel_name.startswith("توكيد"):
            return 10

        # Default priority
        return 5

    def _get_ontology_classes(self, analysis: MorphAnalysis) -> list[str]:
        """Maps morphological features to ontology classes."""
        internal = normalize_camel(analysis)

        classes = []
        if internal.pos == "verb":
            classes.append(OAS_VERB_URI)
            classes.append(OAS_VERB_TAM_URI)
            if internal.mood == "indicative":
                classes.append(OAS_VERB_MOOD_INDICATIVE_URI)
            elif internal.mood == "subjunctive":
                classes.append(OAS_VERB_MOOD_SUBJUNCTIVE_URI)
            elif internal.mood == "jussive":
                classes.append(OAS_VERB_MOOD_JUSSIVE_URI)
        elif internal.pos in ("noun", "adj"):
            classes.append(OAS_NOUN_URI)
            if internal.case == "nominative":
                classes.append(OAS_NOUN_CASE_NOMINATIVE_URI)
            elif internal.case == "accusative":
                classes.append(OAS_NOUN_CASE_ACCUSATIVE_URI)
            elif internal.case == "genitive":
                classes.append(OAS_NOUN_CASE_GENITIVE_URI)

            if internal.definiteness == "definite":
                classes.append(OAS_NOUN_DEFINITE_URI)
            elif internal.definiteness == "indefinite":
                classes.append(OAS_NOUN_INDEFINITE_URI)

        return classes
