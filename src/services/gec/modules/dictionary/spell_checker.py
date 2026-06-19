"""Implements the spell checker submodule for GEC."""

from collections import defaultdict

from loguru import logger
from pyarabic.araby import normalize_hamza

from src.core.schemas import Token
from src.core.utils.arabic import extract_affixes, strip_diacritics
from src.services.gec.utils.distance_utils import levenshtein

from .arramooz_client import ArramoozClient


class SpellChecker:
    """Handles OOV detection and candidate generation for tokens."""

    def __init__(self, arramooz_client: ArramoozClient):
        """Initializes the SpellChecker."""
        self.arramooz_client = arramooz_client
        self.words_by_len: defaultdict[int, list[str]] = defaultdict(list)
        self.vocabulary: set[str] = set()

        all_words = self.arramooz_client.get_all_normalized_words()
        self.vocabulary = set(all_words)
        for word in all_words:
            self.words_by_len[len(word)].append(word)
        logger.info(
            "SpellChecker initialized | vocabulary_size={}", len(self.vocabulary)
        )

    def is_oov(self, token: Token) -> bool:
        """Checks if a token is Out-of-Vocabulary.

        Uses the token's affix_structure to extract the stem, then checks
        if the stem exists in the vocabulary.

        Args:
            token: The Token to check.

        Returns:
            True if the token's stem is not in the dictionary vocabulary.
        """
        prefix, stem, suffix = extract_affixes(token)
        normalized_stem = normalize_hamza(stem)
        is_oov = normalized_stem not in self.vocabulary and stem not in self.vocabulary
        return is_oov

    def _add_candidates(
        self,
        normalized: str,
        token: Token,
        candidates: list[Token],
        max_dist: int,
        prefix: str = "",
        suffix: str = "",
    ) -> None:
        for length in range(
            max(1, len(normalized) - max_dist),
            len(normalized) + max_dist + 1,
        ):
            for candidate_word in self.words_by_len.get(length, []):
                dist = levenshtein(normalized, candidate_word)
                if not (0 < dist <= max_dist):
                    continue

                for features in self.arramooz_client.get_word_features(candidate_word):
                    candidate = token.model_copy()
                    candidate.form = (
                        prefix + features.get("unvocalized", candidate_word) + suffix
                    )
                    candidates.append(candidate)

    def generate_candidates(self, token: Token, max_dist: int = 2) -> list[Token]:
        """Generates spelling candidates for an OOV token.

        Extracts the stem using affix_structure, performs edit-distance
        search in the vocabulary, and re-attaches prefix and suffix.

        Args:
            token: The Token for which to generate candidates.
            max_dist: Maximum edit distance for candidate search.

        Returns:
            List of candidate full-surface forms (prefix + stem + suffix).
        """
        if not self.is_oov(token):
            return []

        prefix, stem, suffix = extract_affixes(token)
        normalized_stem = normalize_hamza(stem)
        normalized_word = normalize_hamza(strip_diacritics(token.form))

        if len(normalized_stem) <= 2:
            logger.warning(
                "Token '{}' stem too short for candidate generation (len={})",
                token.form,
                len(normalized_stem),
            )
            return []

        candidates: list[Token] = []

        self._add_candidates(
            normalized_stem, token, candidates, max_dist, prefix, suffix
        )
        self._add_candidates(
            normalized_word,
            token,
            candidates,
            max_dist,
        )

        if not candidates:
            logger.warning(
                "No candidates for OOV token '{}' after stem and word search",
                token.form,
            )
        else:
            logger.debug("Total candidates for '{}': {}", token.form, len(candidates))

        return candidates
