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
from src.services.gec.schemas import CandidateEdit
from src.services.ged.schemas import ErrorCategory, ErrorSpan

from .constraint_validator import ConstraintValidator, ConstraintViolation
from .explanation_generator import ExplanationGenerator
from .loader import OntologyLoader
from .ranking_engine import RankingEngine
from .relation_discoverer import RelationDiscoverer

_UNFLAGGED_SYNTAX_CONFIDENCE = 0.5


class CandidateGenerator:
    """Generates sentence-localized corrections using ontology-driven approach."""

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
        text: str,
        tokens: list[Token],
        spans: list[ErrorSpan],
        morph_features: list[list[MorphAnalysis]],
    ) -> list[CandidateEdit]:
        """Generate localized correction candidates sentence by sentence.

        Args:
            text: Original input text.
            tokens: Preprocessed text tokens.
            spans: Detected error spans from GED.
            morph_features: Morphological features for each token.

        Returns:
            List of CandidateEdit objects localized to the changed sentence spans.
        """
        logger.info("tokens={} spans={}", len(tokens), len(spans))

        sentence_edits: list[CandidateEdit] = []
        for start, end in self._sentence_ranges(text, tokens):
            sentence_tokens = tokens[start:end]
            sentence_morph_features = morph_features[start:end]
            sentence_spans = self._spans_for_sentence(sentence_tokens, spans)
            sentence_edits.extend(
                self._generate_sentence_candidates(
                    sentence_tokens,
                    sentence_spans,
                    sentence_morph_features,
                )
            )

        return sentence_edits

    def _generate_sentence_candidates(
        self,
        tokens: list[Token],
        spans: list[ErrorSpan],
        morph_features: list[list[MorphAnalysis]],
    ) -> list[CandidateEdit]:
        """Generate ranked localized edits for a single sentence slice."""
        if not tokens:
            return []

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

            alternatives = self._generate_alternatives_for_token(
                tokens, morph_features, violation, confidence
            )

            if alternatives:
                token_alternatives[tidx] = alternatives
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

        # Step 4: Generate sentence-level candidates by combining alternatives
        original_sentence = "".join(
            token.form + (" " if i < len(tokens) - 1 else "")
            for i, token in enumerate(tokens)
        )

        complete_sentences = self._generate_complete_sentences(
            tokens, original_sentence, token_alternatives
        )

        # Step 5: Rank sentence candidates, then emit only localized changed spans
        ranked_edits = self._rank_complete_sentences(
            tokens,
            original_sentence,
            complete_sentences,
            token_explanations,
        )

        logger.info("Generated {} localized ontology edits", len(ranked_edits))
        return ranked_edits

    @staticmethod
    def _sentence_ranges(text: str, tokens: list[Token]) -> list[tuple[int, int]]:
        """Split tokens into sentence-like ranges using punctuation and newlines."""
        if not tokens:
            return []

        sentence_breakers = {".", "!", "?", "؟", ";", "؛"}
        ranges: list[tuple[int, int]] = []
        start = 0

        for index, token in enumerate(tokens[:-1]):
            next_token = tokens[index + 1]
            gap = text[token.span[1] : next_token.span[0]]
            if token.form in sentence_breakers or "\n" in gap or "\r" in gap:
                ranges.append((start, index + 1))
                start = index + 1

        ranges.append((start, len(tokens)))
        return [
            (range_start, range_end)
            for range_start, range_end in ranges
            if range_start < range_end
        ]

    @staticmethod
    def _spans_for_sentence(
        sentence_tokens: list[Token],
        spans: list[ErrorSpan],
    ) -> list[ErrorSpan]:
        """Filter GED spans to those that belong to the current sentence."""
        if not sentence_tokens:
            return []

        local_index_by_global_ref = {
            token.index: local_index
            for local_index, token in enumerate(sentence_tokens)
        }
        sentence_start = sentence_tokens[0].span[0]
        sentence_end = sentence_tokens[-1].span[1]

        sentence_spans: list[ErrorSpan] = []
        for span in spans:
            local_token_refs = [
                local_index_by_global_ref[token_ref]
                for token_ref in span.token_refs
                if token_ref in local_index_by_global_ref
            ]
            overlaps_sentence = (
                span.span[0] < sentence_end and span.span[1] > sentence_start
            )
            if not local_token_refs and not overlaps_sentence:
                continue
            sentence_spans.append(
                span.model_copy(
                    update={
                        "token_refs": local_token_refs,
                    }
                )
            )

        return sentence_spans

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

        is_annex = (
            violation.relation_name == "مضاف_اليه"
            or violation.violation_type == "nun_deletion"
        )

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

        token_indices = sorted(token_alternatives.keys())

        all_alternatives = []
        for tidx in token_indices:
            forms = [alt[0] for alt in token_alternatives[tidx]]
            all_alternatives.append(forms)

        complete_sentences = []
        if all_alternatives:
            for combination in itertools.product(*all_alternatives):
                token_forms = list(zip(token_indices, combination, strict=False))
                sentence = self._build_sentence(tokens, token_forms)

                min_conf = min(token_alternatives[tidx][0][2] for tidx in token_indices)

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
        form_map = dict(token_forms)

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
    ) -> list[CandidateEdit]:
        """Rank sentence candidates and emit localized changed-token edits."""
        if not complete_sentences:
            return []

        sentence_edits = []
        metadata_by_edit_id: dict[int, list[tuple[int, str]]] = {}
        for cs in complete_sentences:
            sentence = cs["sentence"]
            token_forms = cs["token_forms"]
            confidence = cs["min_confidence"]

            edit = CandidateEdit(
                span=(0, len(original_sentence)),
                token_refs=list(range(len(tokens))),
                correction=sentence,
                edit_confidence=confidence,
            )
            sentence_edits.append(edit)
            metadata_by_edit_id[id(edit)] = token_forms

        ranked_sentences = self._ranking_engine.rank_complete_sentences(
            sentence_edits, original_sentence
        )
        if not ranked_sentences:
            return []

        best_sentence = ranked_sentences[0]
        return self._localize_ranked_edit(
            tokens=tokens,
            token_forms=metadata_by_edit_id[id(best_sentence)],
            confidence=best_sentence.edit_confidence,
            token_explanations=token_explanations,
        )

    def _localize_ranked_edit(
        self,
        tokens: list[Token],
        token_forms: list[tuple[int, str]],
        confidence: float,
        token_explanations: dict[int, str],
    ) -> list[CandidateEdit]:
        """Convert a ranked sentence candidate into localized changed-span edits."""
        if not token_forms:
            return []

        sorted_token_forms = sorted(token_forms)
        replacement_forms = dict(token_forms)
        grouped_indices: list[list[int]] = []

        for token_index, _ in sorted_token_forms:
            if not grouped_indices or token_index != grouped_indices[-1][-1] + 1:
                grouped_indices.append([token_index])
            else:
                grouped_indices[-1].append(token_index)

        localized_edits: list[CandidateEdit] = []
        for group in grouped_indices:
            first_token = group[0]
            last_token = group[-1]
            replacement = " ".join(
                replacement_forms.get(index, tokens[index].form)
                for index in range(first_token, last_token + 1)
            )
            localized_edits.append(
                CandidateEdit(
                    span=(tokens[first_token].span[0], tokens[last_token].span[1]),
                    token_refs=[tokens[index].index for index in group],
                    correction=replacement,
                    edit_confidence=confidence,
                    explanation=token_explanations.get(first_token),
                )
            )

        return localized_edits
