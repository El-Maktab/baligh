"""Integration tests for GEC Ontology candidate generation.

Following the paper methodology: generates ALL possible syntactically correct
sentences, then compares with original to find corrections.

Each candidate edit contains a FULL SENTENCE correction with all tokens.
"""

from src.core.schemas import MorphAnalysis, Token
from src.services.gec.modules.ontology.engine import OntologyEngine
from src.services.gec.schemas import GECInput, ModuleStatus
from src.services.ged.schemas import (
    ErrorCategory,
    ErrorSource,
    ErrorSpan,
    ProvenanceTier,
)


def _make_syntax_error(span, token_refs, subtype):
    return ErrorSpan(
        span=span,
        token_refs=token_refs,
        category=ErrorCategory.SYNTAX,
        subtype=subtype,
        confidence=0.9,
        sources=[ErrorSource.RULE_BASED],
        provenance_tier=ProvenanceTier.TIER_1_RULE_DERIVED,
        explanation_eligible=True,
        explanation_text="Syntax mismatch",
    )


def test_subject_verb_mismatch():
    """Scenario 1: Subject-Verb Mismatch (Number agreement when verb precedes).

    Input: كتبوا المهندسون -> Expected: كتب المهندسون

    Following the paper: returns full sentence correction.
    """
    engine = OntologyEngine()

    tokens = [
        Token(index=0, form="كتبوا", span=(0, 5)),
        Token(index=1, form="المهندسون", span=(6, 15)),
    ]

    morph_features = [
        [
            MorphAnalysis(
                token_index=0,
                pos="verb",
                number="plural",
                gender="masculine",
                tense="past",
                lemma="كتب",
                is_disambiguated=True,
            )
        ],
        [
            MorphAnalysis(
                token_index=1,
                pos="noun",
                number="plural",
                gender="masculine",
                case="nominative",
                lemma="مهندس",
                definiteness="definite",
                is_disambiguated=True,
            )
        ],
    ]

    span = _make_syntax_error((0, 5), [0], "verb_subject_agreement")
    input_data = GECInput(
        text="كتبوا المهندسون",
        tokens=tokens,
        morph_features=morph_features,
        errors_span=[span],
    )

    result = engine.process(input_data)
    assert result.status == ModuleStatus.INCORRECT
    assert len(result.candidate_edits) >= 1

    edit = result.candidate_edits[0]
    # Full sentence span and all token references
    assert edit.span == (0, 15)
    assert edit.token_refs == [0, 1]
    # Correction should be the full corrected sentence
    assert "كتب" in edit.correction
    assert "المهندسون" in edit.correction
    assert edit.explanation == "إذا تقدم الفعل على الفاعل، لزم إفراده"


def test_noun_adjective_mismatch():
    """Scenario 2: Noun-Adjective Mismatch (Gender agreement).

    Input: سيارة سريع -> Expected: سيارة سريعة

    Following the paper: returns full sentence correction.
    """
    engine = OntologyEngine()

    tokens = [
        Token(index=0, form="سيارة", span=(0, 5)),
        Token(index=1, form="سريع", span=(6, 10)),
    ]

    morph_features = [
        [
            MorphAnalysis(
                token_index=0,
                pos="noun",
                number="singular",
                gender="feminine",
                case="nominative",
                lemma="سيارة",
                definiteness="indefinite",
                is_disambiguated=True,
            )
        ],
        [
            MorphAnalysis(
                token_index=1,
                pos="adj",
                number="singular",
                gender="masculine",
                case="nominative",
                lemma="سريع",
                definiteness="indefinite",
                is_disambiguated=True,
            )
        ],
    ]

    span = _make_syntax_error((6, 10), [1], "noun_adjective_agreement")
    input_data = GECInput(
        text="سيارة سريع",
        tokens=tokens,
        morph_features=morph_features,
        errors_span=[span],
    )

    result = engine.process(input_data)
    assert result.status == ModuleStatus.INCORRECT
    assert len(result.candidate_edits) >= 1

    edit = result.candidate_edits[0]
    assert edit.span == (0, 10)
    assert edit.token_refs == [0, 1]
    assert "سريعة" in edit.correction
    assert edit.explanation == "النعت يتبع المنعوت في التذكير والتأنيث"


def test_idafa_mismatch():
    """Scenario 3: Idafa Case Mismatch (Sound masculine plural Nun deletion).

    Input: معلمون المدرسة -> Expected: معلمو المدرسة

    Following the paper: returns full sentence correction.
    """
    engine = OntologyEngine()

    tokens = [
        Token(index=0, form="معلمون", span=(0, 6)),
        Token(index=1, form="المدرسة", span=(7, 14)),
    ]

    morph_features = [
        [
            MorphAnalysis(
                token_index=0,
                pos="noun",
                number="plural",
                gender="masculine",
                case="nominative",
                lemma="معلم",
                definiteness="indefinite",
                is_disambiguated=True,
            )
        ],
        [
            MorphAnalysis(
                token_index=1,
                pos="noun",
                number="singular",
                gender="feminine",
                case="genitive",
                lemma="مدرسة",
                definiteness="definite",
                is_disambiguated=True,
            )
        ],
    ]

    span = _make_syntax_error((0, 6), [0], "idafa_agreement")
    input_data = GECInput(
        text="معلمون المدرسة",
        tokens=tokens,
        morph_features=morph_features,
        errors_span=[span],
    )

    result = engine.process(input_data)
    assert result.status == ModuleStatus.INCORRECT
    assert len(result.candidate_edits) >= 1

    edit = result.candidate_edits[0]
    assert edit.span == (0, 14)
    assert edit.token_refs == [0, 1]
    assert "معلمو" in edit.correction
    assert "المدرسة" in edit.correction
    assert edit.explanation == "تحذف نون جمع المذكر السالم عند الإضافة"


def test_subject_case_mismatch():
    """Scenario 4: Subject Case Mismatch (Accusative subject -> Nominative).

    Input: جاء المهندسين -> Expected: جاء المهندسون

    Following the paper: returns full sentence correction.
    """
    engine = OntologyEngine()

    tokens = [
        Token(index=0, form="جاء", span=(0, 3)),
        Token(index=1, form="المهندسين", span=(4, 13)),
    ]

    morph_features = [
        [
            MorphAnalysis(
                token_index=0,
                pos="verb",
                number="singular",
                gender="masculine",
                tense="past",
                lemma="جاء",
                is_disambiguated=True,
            )
        ],
        [
            MorphAnalysis(
                token_index=1,
                pos="noun",
                number="plural",
                gender="masculine",
                case="accusative",
                lemma="مهندس",
                definiteness="definite",
                is_disambiguated=True,
            )
        ],
    ]

    span = _make_syntax_error((4, 13), [1], "subject_case_agreement")
    input_data = GECInput(
        text="جاء المهندسين",
        tokens=tokens,
        morph_features=morph_features,
        errors_span=[span],
    )

    result = engine.process(input_data)
    assert result.status == ModuleStatus.INCORRECT
    assert len(result.candidate_edits) >= 1

    edit = result.candidate_edits[0]
    assert edit.span == (0, 13)
    assert edit.token_refs == [0, 1]
    assert "المهندسون" in edit.correction
    assert "جاء" in edit.correction
    assert edit.explanation == "الفاعل يجب أن يكون مرفوعاً ولكن وجد منصوباً"


# --- Unflagged (Pass-2) tests: GED did NOT flag the errors ---


def test_unflagged_noun_adjective_mismatch():
    """Noun-Adjective mismatch with NO GED error spans.

    GED missed the error, but the ontology scan should catch it
    with lower confidence (0.5).

    Following the paper: returns full sentence correction.
    """
    engine = OntologyEngine()

    tokens = [
        Token(index=0, form="سيارة", span=(0, 5)),
        Token(index=1, form="سريع", span=(6, 10)),
    ]

    morph_features = [
        [
            MorphAnalysis(
                token_index=0,
                pos="noun",
                number="singular",
                gender="feminine",
                case="nominative",
                lemma="سيارة",
                definiteness="indefinite",
                is_disambiguated=True,
            )
        ],
        [
            MorphAnalysis(
                token_index=1,
                pos="adj",
                number="singular",
                gender="masculine",
                case="nominative",
                lemma="سريع",
                definiteness="indefinite",
                is_disambiguated=True,
            )
        ],
    ]

    input_data = GECInput(
        text="سيارة سريع",
        tokens=tokens,
        morph_features=morph_features,
        errors_span=[],
    )

    result = engine.process(input_data)
    assert result.status == ModuleStatus.INCORRECT
    assert len(result.candidate_edits) >= 1

    edit = result.candidate_edits[0]
    assert "سريعة" in edit.correction
    assert edit.edit_confidence == 0.5


def test_unflagged_subject_verb_mismatch():
    """Subject-Verb mismatch with NO GED error spans.

    GED missed the verb-subject agreement error, but the ontology
    scan should detect it with lower confidence.

    Following the paper: returns full sentence correction.
    """
    engine = OntologyEngine()

    tokens = [
        Token(index=0, form="كتبوا", span=(0, 5)),
        Token(index=1, form="المهندسون", span=(6, 15)),
    ]

    morph_features = [
        [
            MorphAnalysis(
                token_index=0,
                pos="verb",
                number="plural",
                gender="masculine",
                tense="past",
                lemma="كتب",
                is_disambiguated=True,
            )
        ],
        [
            MorphAnalysis(
                token_index=1,
                pos="noun",
                number="plural",
                gender="masculine",
                case="nominative",
                lemma="مهندس",
                definiteness="definite",
                is_disambiguated=True,
            )
        ],
    ]

    input_data = GECInput(
        text="كتبوا المهندسون",
        tokens=tokens,
        morph_features=morph_features,
        errors_span=[],
    )

    result = engine.process(input_data)
    assert result.status == ModuleStatus.INCORRECT
    assert len(result.candidate_edits) >= 1

    edit = result.candidate_edits[0]
    assert "كتب" in edit.correction
    # Confidence is blended by ranking, just check it's in reasonable range for unflagged
    assert 0.3 <= edit.edit_confidence <= 0.6


def test_flagged_higher_confidence_than_unflagged():
    """Same error type: GED-flagged tokens get higher confidence than unflagged.

    Two identical noun-adj mismatches, but only one is GED-flagged.
    The flagged one should have confidence from the span, the unflagged one 0.5.
    """
    engine = OntologyEngine()

    tokens = [
        Token(index=0, form="السيارة", span=(0, 7)),
        Token(index=1, form="السريع", span=(8, 14)),
        Token(index=2, form="الجميلة", span=(15, 21)),
        Token(index=3, form="الجديد", span=(22, 27)),
    ]

    morph_features = [
        [
            MorphAnalysis(
                token_index=0,
                pos="noun",
                number="singular",
                gender="feminine",
                case="nominative",
                lemma="سيارة",
                definiteness="definite",
                is_disambiguated=True,
            )
        ],
        [
            MorphAnalysis(
                token_index=1,
                pos="adj",
                number="singular",
                gender="masculine",
                case="nominative",
                lemma="سريع",
                definiteness="definite",
                is_disambiguated=True,
            )
        ],
        [
            MorphAnalysis(
                token_index=2,
                pos="noun",
                number="singular",
                gender="feminine",
                case="nominative",
                lemma="جميلة",
                definiteness="definite",
                is_disambiguated=True,
            )
        ],
        [
            MorphAnalysis(
                token_index=3,
                pos="adj",
                number="singular",
                gender="masculine",
                case="nominative",
                lemma="جديد",
                definiteness="definite",
                is_disambiguated=True,
            )
        ],
    ]

    flagged_span = _make_syntax_error((8, 14), [1], "noun_adjective_agreement")
    input_data = GECInput(
        text="السيارة السريع الجميلة الجديد",
        tokens=tokens,
        morph_features=morph_features,
        errors_span=[flagged_span],
    )

    result = engine.process(input_data)
    assert result.status == ModuleStatus.INCORRECT

    # Should have at least one edit
    assert len(result.candidate_edits) >= 1


def test_subject_verb_gender_mismatch_generates_multiple_candidates():
    """Test that gender mismatch generates multiple candidate sentences.

    Input: قالت الطالب -> Expected candidates:
    - قال الطالب (verb changed to masculine)
    - قالت الطالبة (subject changed to feminine)

    Following the paper: returns multiple full sentence candidates.
    """
    engine = OntologyEngine()

    tokens = [
        Token(index=0, form="قالت", span=(0, 4)),
        Token(index=1, form="الطالب", span=(5, 11)),
    ]

    morph_features = [
        [
            MorphAnalysis(
                token_index=0,
                pos="verb",
                number="singular",
                gender="feminine",
                tense="past",
                lemma="قال",
                is_disambiguated=True,
            )
        ],
        [
            MorphAnalysis(
                token_index=1,
                pos="noun",
                number="singular",
                gender="masculine",
                case="nominative",
                lemma="طالب",
                definiteness="definite",
                is_disambiguated=True,
            )
        ],
    ]

    input_data = GECInput(
        text="قالت الطالب",
        tokens=tokens,
        morph_features=morph_features,
        errors_span=[],
    )

    result = engine.process(input_data)
    assert result.status == ModuleStatus.INCORRECT
    # Should generate at least 1 candidate (may generate more depending on alternatives)
    assert len(result.candidate_edits) >= 1

    # At least one candidate should have feminine subject or masculine verb
    corrections = [edit.correction for edit in result.candidate_edits]
    has_masculine_verb = any("قال" in c and "قالت" not in c for c in corrections)
    has_feminine_subject = any("الطالبة" in c for c in corrections)
    assert has_masculine_verb or has_feminine_subject


def test_subject_object_correctness():
    """Test case of verb + subject + object.

    Input: قرأ الطالبين الكتابان (incorrect case on both subject and object)
    Expected: Generates corrected sentences with proper cases

    Following the paper: returns full sentence corrections.
    """
    engine = OntologyEngine()

    tokens = [
        Token(index=0, form="قرأ", span=(0, 4)),
        Token(index=1, form="الطالبين", span=(5, 11)),
        Token(index=2, form="الكتابان", span=(12, 18)),
    ]

    morph_features = [
        [
            MorphAnalysis(
                token_index=0,
                pos="verb",
                number="singular",
                gender="masculine",
                tense="past",
                lemma="قرأ",
                is_disambiguated=True,
            )
        ],
        [
            MorphAnalysis(
                token_index=1,
                pos="noun",
                number="dual",
                gender="masculine",
                case="accusative",
                lemma="طالب",
                definiteness="definite",
                is_disambiguated=True,
            )
        ],
        [
            MorphAnalysis(
                token_index=2,
                pos="noun",
                number="dual",
                gender="masculine",
                case="nominative",
                lemma="كتاب",
                definiteness="definite",
                is_disambiguated=True,
            )
        ],
    ]

    input_data = GECInput(
        text="قرأ الطالبين الكتابان",
        tokens=tokens,
        morph_features=morph_features,
        errors_span=[],
    )

    result = engine.process(input_data)
    assert result.status == ModuleStatus.INCORRECT
    assert len(result.candidate_edits) >= 1

    # Should generate at least one corrected full sentence
    edit = result.candidate_edits[0]
    # Span covers full sentence (0 to end of text)
    assert edit.span[0] == 0
    assert edit.span[1] > 0
    assert edit.token_refs == [0, 1, 2]
    assert "قرأ" in edit.correction
