"""Lexicon GED detector.

Authors:
    Amir Anwar
"""

from __future__ import annotations

from pathlib import Path

from src.core.schemas import MorphAnalysis, Token
from src.core.utils.arabic import (
    ALL_PUNCTUATION,
    is_arabic_word,
    normalize_arabic_surface,
)
from src.services.ged.confidence import TIER_CONFIDENCE
from src.services.ged.config import LexiconConfig, load_ged_config
from src.services.ged.features.subsystems.base import BaseDetector
from src.services.ged.features.subsystems.lexicon.loader import load_patterns
from src.services.ged.features.subsystems.lexicon.models import LexiconPattern
from src.services.ged.features.subsystems.lexicon.trie_store import (
    LexiconTrieStore,
    load_processed_lexicon,
)
from src.services.ged.schemas import (
    ErrorCategory,
    ErrorSource,
    ErrorSpan,
    ProvenanceTier,
)

_SPELLING_TIER = ProvenanceTier.TIER_2_RULE_SUPPORTED
_SPELLING_EXPLANATION = (
    "الكلمة غير موجودة في المعجم المتاح ولم يقدم المحلل الصرفي تحليلا موثوقا."
)


class LexiconDetector(BaseDetector):
    """Runs all registered lexicon-based checks and returns their error spans."""

    def __init__(
        self,
        patterns: list[LexiconPattern] | None = None,
        *,
        config: LexiconConfig | None = None,
        trie_store: LexiconTrieStore | None = None,
        enable_spelling_suspicion: bool | None = None,
        processed_dir: Path | None = None,
    ) -> None:
        """Initialize the detector with curated lexicon patterns."""
        self.config = config or load_ged_config().lexicon
        patterns_path = self.config.resolved_patterns_path
        self.patterns = (
            patterns if patterns is not None else load_patterns(patterns_path)
        )
        self.trie_store = trie_store
        self.enable_spelling_suspicion = (
            self.config.spelling_suspicion.enabled
            if enable_spelling_suspicion is None
            else enable_spelling_suspicion
        )
        self.processed_dir = processed_dir

    @property
    def name(self) -> str:
        """Subsystem name."""
        return "lexicon_matcher"

    def detect(
        self,
        text: str,
        normalized_text: str,  # noqa: ARG002
        tokens: list[Token],
        morph_features: list[list[MorphAnalysis]],
    ) -> list[ErrorSpan]:
        """Run the tokens through the lexicon and checks for spelling errors.

        Args:
            text: Original input text
            normalized_text: Normalised version of the text (unused)
            tokens: Token list from preprocessing
            morph_features: Per-token morphological candidates

        Returns:
            Combined list of ErrorSpans
        """
        spans: list[ErrorSpan] = []
        token_keys = [normalize_arabic_surface(token.form) for token in tokens]

        for pattern in self.patterns:
            if pattern.match_type in {"token", "merge"}:
                spans.extend(self._match_single_token(pattern, tokens, token_keys))
            elif pattern.match_type == "split":
                spans.extend(self._match_split(pattern, tokens, token_keys))

        if self.enable_spelling_suspicion:
            trie_store = self._get_trie_store()
            if trie_store is not None:
                curated_refs = {
                    token_ref for span in spans for token_ref in span.token_refs
                }
                entity_refs = {
                    token_ref
                    for match in trie_store.match_entity_phrases(tokens)
                    for token_ref in match.token_refs
                }
                spans.extend(
                    self._detect_spelling_suspicion(
                        tokens=tokens,
                        morph_features=morph_features,
                        trie_store=trie_store,
                        protected_token_refs=curated_refs | entity_refs,
                    )
                )

        return spans

    def _get_trie_store(self) -> LexiconTrieStore | None:
        """Load processed trie resources if available."""
        if self.trie_store is not None:
            return self.trie_store

        try:
            self.trie_store = (
                load_processed_lexicon(self.processed_dir)
                if self.processed_dir is not None
                else load_processed_lexicon()
            )
        except OSError:
            return None
        return self.trie_store

    def _match_single_token(
        self,
        pattern: LexiconPattern,
        tokens: list[Token],
        token_keys: list[str],
    ) -> list[ErrorSpan]:
        """Match token and merge patterns against one input token."""
        if pattern.wrong is None:
            return []

        wrong_key = normalize_arabic_surface(pattern.wrong)
        spans: list[ErrorSpan] = []
        for token, token_key in zip(tokens, token_keys, strict=True):
            if token_key == wrong_key:
                spans.append(self._build_span(pattern, [token]))
        return spans

    def _match_split(
        self,
        pattern: LexiconPattern,
        tokens: list[Token],
        token_keys: list[str],
    ) -> list[ErrorSpan]:
        """Match split patterns against adjacent input tokens."""
        if not pattern.wrong_tokens:
            return []

        wrong_keys = [normalize_arabic_surface(token) for token in pattern.wrong_tokens]
        window_size = len(wrong_keys)
        spans: list[ErrorSpan] = []

        for start in range(0, len(tokens) - window_size + 1):
            end = start + window_size
            if token_keys[start:end] == wrong_keys:
                spans.append(self._build_span(pattern, tokens[start:end]))

        return spans

    @staticmethod
    def _build_span(pattern: LexiconPattern, matched_tokens: list[Token]) -> ErrorSpan:
        """Build an ErrorSpan for a matched lexicon pattern."""
        return ErrorSpan(
            span=(matched_tokens[0].span[0], matched_tokens[-1].span[1]),
            token_refs=[token.index for token in matched_tokens],
            category=pattern.category,
            subtype=pattern.subtype,
            confidence=pattern.confidence,
            sources=[ErrorSource.LEXICON_MATCHER],
            provenance_tier=pattern.tier,
            explanation_eligible=True,
            explanation_text=pattern.explanation,
        )

    def _detect_spelling_suspicion(
        self,
        *,
        tokens: list[Token],
        morph_features: list[list[MorphAnalysis]],
        trie_store: LexiconTrieStore,
        protected_token_refs: set[int],
    ) -> list[ErrorSpan]:
        """Detect conservative dictionary-backed spelling suspicion."""
        spans: list[ErrorSpan] = []
        for token in tokens:
            if token.index in protected_token_refs:
                continue
            if self._skip_spelling_token(token, morph_features, trie_store):
                continue
            spans.append(self._build_spelling_span(token))
        return spans

    def _skip_spelling_token(
        self,
        token: Token,
        morph_features: list[list[MorphAnalysis]],
        trie_store: LexiconTrieStore,
    ) -> bool:
        """Return True when spelling suspicion should not flag this token."""
        if not token.form or all(char in ALL_PUNCTUATION for char in token.form):
            return True
        if not is_arabic_word(token.form):
            return True
        if self._has_plausible_morphology(token, morph_features):
            return True
        return (
            trie_store.has_word(token.form)
            or trie_store.has_entity_token(token.form)
            or trie_store.has_entity_phrase(token.form)
        )

    @staticmethod
    def _has_plausible_morphology(
        token: Token,
        morph_features: list[list[MorphAnalysis]],
    ) -> bool:
        """Return True if morphology produced a plausible analysis."""
        if token.is_oov:
            return False
        if token.index >= len(morph_features):
            return False

        analyses = morph_features[token.index]
        return any(analysis.pos not in {"PUNC", "NUM"} for analysis in analyses)

    @staticmethod
    def _build_spelling_span(token: Token) -> ErrorSpan:
        """Build an ErrorSpan for dictionary-backed spelling suspicion."""
        return ErrorSpan(
            span=token.span,
            token_refs=[token.index],
            category=ErrorCategory.ORTHOGRAPHY,
            subtype="spelling",
            confidence=TIER_CONFIDENCE[_SPELLING_TIER],
            sources=[ErrorSource.LEXICON_MATCHER],
            provenance_tier=_SPELLING_TIER,
            explanation_eligible=True,
            explanation_text=_SPELLING_EXPLANATION,
        )

    def list_patterns(self) -> list[LexiconPattern]:
        """Return all loaded lexicon patterns."""
        return list(self.patterns)
