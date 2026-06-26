"""Ranking Engine for grammatical correction candidates."""

from src.core.utils.arabic import strip_diacritics
from src.services.gec.schemas import CandidateEdit


def levenshtein_distance(s1: str, s2: str) -> int:
    """Computes the Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (0 if c1 == c2 else 1)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


class RankingEngine:
    """Ranks grammatical candidates using composite confidence scoring."""

    def rank_complete_sentences(
        self,
        candidates: list[CandidateEdit],
        original_sentence: str,
    ) -> list[CandidateEdit]:
        """Ranks complete sentence candidates by Levenshtein distance.

        Args:
            candidates: List of complete sentence CandidateEdit objects.
            original_sentence: The original input sentence.

        Returns:
            Sorted list of candidates, closest to original first.
        """
        scored_candidates = []

        for candidate in candidates:
            dist_raw = levenshtein_distance(original_sentence, candidate.correction)
            dist_strip = levenshtein_distance(
                strip_diacritics(original_sentence),
                strip_diacritics(candidate.correction),
            )

            dist = (dist_raw + dist_strip) / 2.0
            lev_score = 1.0 / (1.0 + dist)
            composite_score = (lev_score * 0.7) + (candidate.edit_confidence * 0.3)

            scored_candidates.append((candidate, composite_score))

        scored_candidates.sort(key=lambda x: x[1], reverse=True)

        ranked = []
        for candidate, score in scored_candidates:
            candidate.edit_confidence = (score * 0.7) + (
                candidate.edit_confidence * 0.3
            )
            ranked.append(candidate)

        return ranked
