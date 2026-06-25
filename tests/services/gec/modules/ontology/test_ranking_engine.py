from src.services.gec.modules.ontology.ranking_engine import (
    RankingEngine,
    levenshtein_distance,
)
from src.services.gec.schemas import OntologyCandidateEdit


def test_levenshtein_distance():
    assert levenshtein_distance("كتب", "كتب") == 0
    assert levenshtein_distance("كتب", "كتبوا") == 2
    assert levenshtein_distance("كتبوا", "كتب") == 2
    assert levenshtein_distance("سيارة", "سيارات") == 2


def test_ranking_engine():
    ranker = RankingEngine()

    # We have an original token: "كتبوا"
    # And candidate corrections: "كتب", "يكتب"
    cand1 = OntologyCandidateEdit(
        span=(0, 5),
        token_refs=[0],
        correction="كتب",
        edit_confidence=0.5,
        explanation="test",
    )

    cand2 = OntologyCandidateEdit(
        span=(0, 5),
        token_refs=[0],
        correction="يكتب",
        edit_confidence=0.5,
        explanation="test",
    )

    ranked = ranker.rank_candidates([cand2, cand1], "كتبوا")

    assert len(ranked) == 2
    # cand1 ("كتب") has smaller edit distance to "كتبوا" than cand2 ("يكتب"), so it should rank higher
    assert ranked[0].correction == "كتب"
    assert ranked[1].correction == "يكتب"


def test_rank_complete_sentences():
    """Test ranking of complete sentence candidates."""
    ranker = RankingEngine()

    original = "كتبوا المهندسون"

    # Candidate 1: Corrected sentence (closer to original)
    cand1 = OntologyCandidateEdit(
        span=(0, 15),
        token_refs=[0, 1],
        correction="كتب المهندسون",
        edit_confidence=0.9,
        explanation="VSO number agreement",
    )

    # Candidate 2: More different sentence
    cand2 = OntologyCandidateEdit(
        span=(0, 15),
        token_refs=[0, 1],
        correction="كتب المهندس",
        edit_confidence=0.9,
        explanation="VSO number agreement",
    )

    ranked = ranker.rank_complete_sentences([cand2, cand1], original)

    assert len(ranked) == 2
    # cand1 should rank higher (closer Levenshtein distance)
    assert ranked[0].correction == "كتب المهندسون"
    assert ranked[1].correction == "كتب المهندس"
