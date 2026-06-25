"""Constraint validation for grammatical relations."""

from loguru import logger
from pydantic import BaseModel

from src.core.schemas import MorphAnalysis, Token
from src.core.utils.features import get_disambiguated_analysis
from src.services.gec.features.camel_adapter import (
    InternalMorphFeatures,
    normalize_camel,
)
from src.services.gec.modules.ontology.constants import (
    ONTOLOGY_CLASSES,
    ONTOLOGY_PROPERTIES,
)
from src.services.gec.modules.ontology.loader import OntologyLoader
from src.services.gec.modules.ontology.relation_discoverer import RelationMetadata
from src.services.gec.modules.ontology.sparql_queries import RELATION_RESTRICTIONS_QUERY


class ConstraintViolation(BaseModel):
    """Represents a violated grammatical constraint."""

    relation_uri: str
    relation_name: str
    violation_type: str
    source_token_idx: int
    target_token_idx: int
    error_token_idx: int
    expected_features: dict[str, str | None]
    actual_features: dict[str, str | None]
    token_root: str
    token_pos: str
    original_token: str


def map_ontology_to_internal_feature(
    prop_uri: str, class_uri: str
) -> tuple[str, str] | None:
    """Maps ontology property and expected class URIs to internal features."""
    prop_name = prop_uri.split("#")[-1]
    class_name = class_uri.split("#")[-1]

    feature_name = ONTOLOGY_PROPERTIES.get(prop_name, None)
    feature_value = ONTOLOGY_CLASSES.get(class_name, None)

    if feature_name and feature_value:
        return feature_name, feature_value
    return None


class ConstraintValidator:
    """Validates grammatical constraints using the rule registry."""

    def __init__(self, loader: OntologyLoader) -> None:
        """Initializes the ConstraintValidator."""
        self._loader = loader

    def validate_constraints(
        self,
        tokens: list[Token],
        morph_features: list[list[MorphAnalysis]],
        relations: list[RelationMetadata],
    ) -> list[ConstraintViolation]:
        """Validates all discovered relations against actual token features."""
        violations = []

        for relation in relations:
            source_analysis = get_disambiguated_analysis(
                morph_features, relation.source_token_idx
            )
            target_analysis = get_disambiguated_analysis(
                morph_features, relation.target_token_idx
            )

            if not source_analysis or not target_analysis:
                continue

            source_internal = normalize_camel(source_analysis)
            target_internal = normalize_camel(target_analysis)

            rule_violations = self._check_rule(
                relation,
                tokens,
                source_internal,
                target_internal,
            )
            violations.extend(rule_violations)

        return violations

    def _query_relation_constraints(
        self, relation_uri: str
    ) -> dict[str, dict[str, str]]:
        """Queries ontology for constraints on domain and range of a relation."""
        constraints: dict[str, dict[str, str]] = {"domain": {}, "range": {}}

        query = RELATION_RESTRICTIONS_QUERY(relation_uri)
        try:
            results = self._loader.query(query)
            for row in results:
                if isinstance(row, bool):
                    continue
                role = str(row[0])
                prop_uri = str(row[1])
                class_uri = str(row[2])

                mapped = map_ontology_to_internal_feature(prop_uri, class_uri)
                if mapped:
                    feat_name, feat_val = mapped
                    constraints[role][feat_name] = feat_val
        except Exception as e:
            logger.error(
                "Failed to query constraints for relation {}: {}", relation_uri, e
            )

        return constraints

    def _constraint_violation(
        self,
        relation: RelationMetadata,
        morph_features: InternalMorphFeatures,
        feature_name: str,
        expected_features: dict[str, str | None],
        actual_features: dict[str, str | None],
        original_token: str,
        error_token_idx: int | None = None,
    ) -> ConstraintViolation:
        """Creates a constraint violation instance."""
        if error_token_idx is None:
            error_token_idx = relation.source_token_idx

        return ConstraintViolation(
            relation_uri=relation.relation_uri,
            relation_name=relation.relation_name,
            violation_type=f"{feature_name}_mismatch",
            source_token_idx=relation.source_token_idx,
            target_token_idx=relation.target_token_idx,
            error_token_idx=error_token_idx,
            expected_features=expected_features,
            actual_features=actual_features,
            token_root=morph_features.lemma or "",
            token_pos=morph_features.pos,
            original_token=original_token,
        )

    def _check_rule(
        self,
        relation: RelationMetadata,
        tokens: list[Token],
        source_internal: InternalMorphFeatures,
        target_internal: InternalMorphFeatures,
    ) -> list[ConstraintViolation]:
        """Checks if the token features violate the rule using ontology constraints."""
        constraints = self._query_relation_constraints(relation.relation_uri)
        properties_to_check = ["case", "gender", "number", "definiteness"]

        violations: list[ConstraintViolation] = []
        if relation.relation_name in ("فاعل", "نائب_الفاعل"):
            if "case" in properties_to_check:
                source_case = source_internal.case
                if source_case and source_case != "nominative":
                    violations.append(
                        self._constraint_violation(
                            relation=relation,
                            morph_features=source_internal,
                            feature_name="case",
                            expected_features={"case": "nominative"},
                            actual_features={"case": source_case},
                            original_token=tokens[relation.target_token_idx].form,
                        )
                    )

            if "number" in properties_to_check:
                source_num = source_internal.number
                target_num = target_internal.number
                if source_num and target_num:
                    if relation.target_token_idx < relation.source_token_idx:
                        # VSO: Verb (target) must be singular.
                        if target_num != "singular":
                            violations.append(
                                self._constraint_violation(
                                    relation=relation,
                                    morph_features=target_internal,
                                    feature_name="number",
                                    expected_features={"number": "singular"},
                                    actual_features={"number": target_num},
                                    original_token=tokens[
                                        relation.target_token_idx
                                    ].form,
                                    error_token_idx=relation.target_token_idx,
                                )
                            )
                    else:
                        # SVO: Verb (target) must match subject (source) in number.
                        if target_num != source_num:
                            violations.append(
                                self._constraint_violation(
                                    relation=relation,
                                    morph_features=target_internal,
                                    feature_name="number",
                                    expected_features={"number": source_num},
                                    actual_features={"number": target_num},
                                    original_token=tokens[
                                        relation.target_token_idx
                                    ].form,
                                    error_token_idx=relation.target_token_idx,
                                )
                            )

            if "gender" in properties_to_check:
                source_gen = source_internal.gender
                target_gen = target_internal.gender
                if source_gen and target_gen and target_gen != source_gen:
                    # First violation: target should match source's gender
                    violations.append(
                        self._constraint_violation(
                            relation=relation,
                            morph_features=target_internal,
                            feature_name="gender",
                            expected_features={"gender": source_gen},
                            actual_features={"gender": target_gen},
                            original_token=tokens[relation.target_token_idx].form,
                            error_token_idx=relation.target_token_idx,
                        )
                    )
                    # Second violation: source should match target's gender
                    violations.append(
                        self._constraint_violation(
                            relation=relation,
                            morph_features=source_internal,
                            feature_name="gender",
                            expected_features={"gender": target_gen},
                            actual_features={"gender": source_gen},
                            original_token=tokens[relation.source_token_idx].form,
                            error_token_idx=relation.source_token_idx,
                        )
                    )

            return violations

        elif relation.relation_name == "مضاف_اليه":
            # For مضاف_اليه (idafa):
            # - The مضاف (source) must be indefinite
            # - The مضاف إليه (target) must be genitive
            # - If مضاف is sound masculine plural or dual, nun must be deleted

            violations = []

            # Check nun deletion for sound masculine plural or dual
            source_num = source_internal.number
            if (
                source_num in ("plural", "dual")
                and source_internal.gender == "masculine"
            ):
                # For sound masculine plural/dual, check if nun should be deleted
                # The form should be واو/ألف without نون
                violations.append(
                    self._constraint_violation(
                        relation=relation,
                        morph_features=source_internal,
                        feature_name="nun_deletion",
                        expected_features={"nun_deletion": "true"},
                        actual_features={"nun_deletion": "false"},
                        original_token=tokens[relation.source_token_idx].form,
                        error_token_idx=relation.source_token_idx,
                    )
                )

            # Return only nun_deletion violations for idafa
            # (case/gender/number agreement don't apply between مضاف and مضاف إليه)
            return violations

        elif relation.relation_name == "نعت":
            # For نعت (adjective), source is the noun (المنعوت), target is the adjective (النعت)
            # The adjective must agree with the noun
            if target_internal.pos != "adj":
                return []

            violations = []
            for prop in properties_to_check:
                source_val = getattr(source_internal, prop, None)
                target_val = getattr(target_internal, prop, None)
                if source_val and target_val and source_val != target_val:
                    violations.append(
                        self._constraint_violation(
                            relation=relation,
                            morph_features=target_internal,
                            feature_name=prop,
                            expected_features={prop: source_val},
                            actual_features={prop: target_val},
                            original_token=tokens[relation.target_token_idx].form,
                            error_token_idx=relation.target_token_idx,
                        )
                    )
            return violations

        violations = []
        for prop in properties_to_check:
            static_domain = constraints["domain"].get(prop)
            if static_domain:
                source_val = getattr(source_internal, prop, None)
                if source_val and source_val != static_domain:
                    violations.append(
                        self._constraint_violation(
                            relation=relation,
                            morph_features=source_internal,
                            feature_name=prop,
                            expected_features={prop: static_domain},
                            actual_features={prop: source_val},
                            original_token=tokens[relation.source_token_idx].form,
                        )
                    )

            static_range = constraints["range"].get(prop)
            if static_range:
                target_val = getattr(target_internal, prop, None)
                if target_val and target_val != static_range:
                    violations.append(
                        self._constraint_violation(
                            relation=relation,
                            morph_features=target_internal,
                            feature_name=prop,
                            expected_features={prop: static_range},
                            actual_features={prop: target_val},
                            original_token=tokens[relation.target_token_idx].form,
                        )
                    )

            if not static_domain and not static_range:
                source_val = getattr(source_internal, prop, None)
                target_val = getattr(target_internal, prop, None)
                if source_val and target_val and source_val != target_val:
                    violations.append(
                        self._constraint_violation(
                            relation=relation,
                            morph_features=source_internal,
                            feature_name=prop,
                            expected_features={prop: target_val},
                            actual_features={prop: source_val},
                            original_token=tokens[relation.source_token_idx].form,
                        )
                    )

        return violations
