"""Generates grammatical correction candidates using the OAS ontology.

Following the paper methodology: generates ALL possible syntactically correct
sentences from extracted words, then compares with original to find corrections.
"""

from loguru import logger

from src.core.schemas import MorphAnalysis, Token
from src.core.utils.arabic import strip_diacritics
from src.core.utils.features import get_disambiguated_analysis
from src.services.gec.features.camel_adapter import normalize_camel
from src.services.gec.modules.dictionary.morph_generator import MorphologicalGenerator
from src.services.gec.schemas import OntologyCandidateEdit
from src.services.ged.schemas import ErrorCategory, ErrorSpan

from .constraint_validator import ConstraintValidator, ConstraintViolation
from .explanation_generator import ExplanationGenerator
from .loader import OntologyLoader
from .ranking_engine import RankingEngine
from .relation_discoverer import RelationDiscoverer

_UNFLAGGED_SYNTAX_CONFIDENCE = 0.5


class CandidateGenerator:
    """Generates full sentence corrections using ontology-driven approach."""

    def __init__(
        self,
        loader: OntologyLoader,
        morph_generator: MorphologicalGenerator,
        explanation_generator: ExplanationGenerator,
    ) -> None:
        """Initializes the CandidateGenerator."""
        self._loader = loader
        self._morph_generator = morph_generator
        self._explanation_generator = explanation_generator

        self._relation_discoverer = RelationDiscoverer(self._loader)
        self._constraint_validator = ConstraintValidator(self._loader)
        self._ranking_engine = RankingEngine()

    def generate_candidates(
        self,
        tokens: list[Token],
        spans: list[ErrorSpan],
        morph_features: list[list[MorphAnalysis]],
    ) -> list[OntologyCandidateEdit]:
        """Generates full sentence correction candidates.

        Following the paper methodology:
        1. Discover all grammatical relations from ontology
        2. Validate constraints and detect violations
        3. For each violation, generate alternative forms for affected tokens
        4. Build complete corrected sentences by combining alternatives
        5. Rank complete sentences by Levenshtein distance and other signals

        Args:
            tokens: Preprocessed text tokens.
            spans: Detected error spans from GED.
            morph_features: Morphological features for each token.

        Returns:
            List of OntologyCandidateEdit objects, each containing a full sentence correction.
        """
        logger.info("tokens={} spans={}", len(tokens), len(spans))

        ged_syntax_spans = [
            span for span in spans if span.category == ErrorCategory.SYNTAX
        ]

        ged_syntax_indices = {}
        for span in ged_syntax_spans:
            for idx in span.token_refs:
                ged_syntax_indices[idx] = span.confidence

        # Step 1: Discover all grammatical relations
        relations = self._relation_discoverer.discover_relations(tokens, morph_features)
        logger.debug("Discovered relations: {}", len(relations))

        # Step 2: Validate constraints and find violations
        violations = self._constraint_validator.validate_constraints(
            tokens, morph_features, relations
        )
        logger.debug("Discovered violations: {}", len(violations))

        if not violations:
            return []

        # Step 3: Group violations by token and generate alternatives for each token
        token_alternatives: dict[int, list[tuple[str, str, float]]] = {}
        token_explanations: dict[int, str] = {}
        processed_indices: set[int] = set()

        for violation in violations:
            tidx = violation.error_token_idx
            if tidx in processed_indices:
                continue
            processed_indices.add(tidx)

            if tidx not in ged_syntax_indices:
                confidence = _UNFLAGGED_SYNTAX_CONFIDENCE
            else:
                confidence = ged_syntax_indices[tidx]

            # Generate alternative forms for this token
            alternatives = self._generate_alternatives_for_token(
                tokens, morph_features, violation, confidence
            )

            if alternatives:
                token_alternatives[tidx] = alternatives
                # Store explanation for the first violation at this token
                if tidx not in token_explanations:
                    token_explanations[tidx] = (
                        self._explanation_generator.generate_explanation(
                            violation.relation_uri,
                            violation.expected_features,
                            violation.actual_features,
                        )
                    )

        if not token_alternatives:
            return []

        # Step 4: Generate complete sentences by combining alternatives
        # Start with original sentence
        original_sentence = "".join(
            token.form + (" " if i < len(tokens) - 1 else "")
            for i, token in enumerate(tokens)
        )

        # Generate all combinations of alternatives
        complete_sentences = self._generate_complete_sentences(
            tokens, original_sentence, token_alternatives
        )

        # Step 5: Rank complete sentences
        ranked_edits = self._rank_complete_sentences(
            tokens,
            original_sentence,
            complete_sentences,
            token_explanations,
            ged_syntax_indices,
        )

        logger.info("Generated {} complete sentence candidates", len(ranked_edits))
        return ranked_edits

    def _generate_alternatives_for_token(
        self,
        tokens: list[Token],
        morph_features: list[list[MorphAnalysis]],
        violation: ConstraintViolation,
        confidence: float,
    ) -> list[tuple[str, str, float]]:
        """Generate alternative forms for a single token.

        Returns list of (form, explanation, confidence) tuples.
        """
        tidx = violation.error_token_idx
        target_analysis = get_disambiguated_analysis(morph_features, tidx)
        if not target_analysis:
            return []

        target_internal = normalize_camel(target_analysis)
        expected_features = violation.expected_features

        # Determine constraints for morphological generation
        is_annex = (
            violation.relation_name == "مضاف_اليه"
            or violation.violation_type == "nun_deletion"
        )

        # Preserve original number for case/gender corrections
        number_val = target_internal.number
        if violation.violation_type == "number_mismatch":
            number_val = expected_features.get("number") or target_internal.number

        case_val = expected_features.get("case") or target_internal.case
        if case_val is None and target_internal.pos in ("noun", "adj"):
            if violation.relation_name in ("فاعل", "نائب_الفاعل"):
                case_val = "nominative"
            elif violation.relation_name == "مضاف_اليه":
                case_val = "genitive"
            else:
                case_val = target_internal.case or "nominative"

        constraints = {
            "lemma": target_internal.lemma,
            "gender": expected_features.get("gender") or target_internal.gender,
            "number": number_val,
            "case": case_val,
            "definiteness": expected_features.get("definiteness")
            or target_internal.definiteness,
            "original_token": tokens[tidx].form,
            "prefix": "",
            "annex": is_annex,
        }

        corrected_forms = self._morph_generator.generate_form(
            target_internal.lemma or "", target_internal.pos, constraints
        )
        if not corrected_forms:
            return []

        original_form = tokens[tidx].form
        is_vocalized = strip_diacritics(original_form) != original_form

        alternatives = []
        seen_forms = set()
        for form in corrected_forms:
            candidate_form = form if is_vocalized else strip_diacritics(form)
            if candidate_form == original_form:
                continue
            if candidate_form in seen_forms:
                continue
            seen_forms.add(candidate_form)
            alternatives.append((candidate_form, violation.relation_uri, confidence))

        return alternatives

    def _generate_complete_sentences(
        self,
        tokens: list[Token],
        original_sentence: str,
        token_alternatives: dict[int, list[tuple[str, str, float]]],
    ) -> list[dict]:
        """Generate all complete sentence combinations from token alternatives.

        Returns list of dicts with:
        - sentence: the complete corrected sentence string
        - token_forms: list of (token_index, form) tuples for changed tokens
        - min_confidence: minimum confidence across all changes
        """
        import itertools

        # Get all token indices with alternatives
        token_indices = sorted(token_alternatives.keys())

        # Get all alternative forms for each token
        all_alternatives = []
        for tidx in token_indices:
            forms = [alt[0] for alt in token_alternatives[tidx]]
            all_alternatives.append(forms)

        # Generate all combinations
        complete_sentences = []
        if all_alternatives:
            for combination in itertools.product(*all_alternatives):
                # Build sentence with this combination of alternatives
                token_forms = list(zip(token_indices, combination))
                sentence = self._build_sentence(tokens, token_forms)

                # Calculate minimum confidence across changes
                min_conf = min(
                    token_alternatives[tidx][0][
                        2
                    ]  # Use confidence from first alternative
                    for tidx in token_indices
                )

                complete_sentences.append(
                    {
                        "sentence": sentence,
                        "token_forms": token_forms,
                        "min_confidence": min_conf,
                    }
                )

        return complete_sentences

    def _build_sentence(
        self,
        tokens: list[Token],
        token_forms: list[tuple[int, str]],
    ) -> str:
        """Build a complete sentence from token forms.

        Args:
            tokens: Original tokens
            token_forms: List of (token_index, new_form) tuples for changed tokens

        Returns:
            Complete sentence string
        """
        # Create a mapping of changed tokens
        form_map = dict(token_forms)

        # Build sentence with original or changed forms
        forms = []
        for i, token in enumerate(tokens):
            if i in form_map:
                forms.append(form_map[i])
            else:
                forms.append(token.form)

        return " ".join(forms)

    def _rank_complete_sentences(
        self,
        tokens: list[Token],
        original_sentence: str,
        complete_sentences: list[dict],
        token_explanations: dict[int, str],
        ged_syntax_indices: dict[int, float],
    ) -> list[OntologyCandidateEdit]:
        """Rank complete sentences and convert to OntologyCandidateEdit objects."""
        if not complete_sentences:
            return []

        # Full sentence span and all token references
        full_span = (0, sum(len(token.form) + 1 for token in tokens) - 1)
        all_token_refs = list(range(len(tokens)))

        edits = []
        for cs in complete_sentences:
            sentence = cs["sentence"]
            token_forms = cs["token_forms"]
            confidence = cs["min_confidence"]

            # Use explanation from first changed token
            explanation = None
            if token_forms:
                first_tidx = token_forms[0][0]
                explanation = token_explanations.get(first_tidx)

            edit = OntologyCandidateEdit(
                span=full_span,
                token_refs=all_token_refs,
                correction=sentence,
                edit_confidence=confidence,
                explanation=explanation,
                alternatives=None,  # Will be populated by ranking if needed
            )
            edits.append(edit)

        # Rank by Levenshtein distance from original
        ranked = self._ranking_engine.rank_complete_sentences(edits, original_sentence)
        return ranked
