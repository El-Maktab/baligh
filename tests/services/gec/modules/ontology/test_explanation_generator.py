"""Unit tests for the ExplanationGenerator covering all expanded templates."""

from src.services.gec.modules.ontology.explanation_generator import ExplanationGenerator

BASE_URI = "http://arabicontology.org/oas_grammar.owl#"


# ── Subject-Verb (فاعل) ──────────────────────────────────────────────


def test_explanation_subject_verb_case():
    """Test explanation for subject case mismatch."""
    generator = ExplanationGenerator()
    expl = generator.generate_explanation(
        "subject_verb",
        {"case": "nominative"},
        {"case": "accusative"},
    )
    assert expl == "الفاعل يجب أن يكون مرفوعاً ولكن وجد منصوباً"


def test_explanation_subject_verb_number():
    """Test explanation for verb preceding plural subject (number mismatch)."""
    generator = ExplanationGenerator()
    expl = generator.generate_explanation(
        "subject_verb",
        {"number": "singular"},
        {"number": "plural"},
    )
    assert expl == "إذا تقدم الفعل على الفاعل، لزم إفراده"


def test_explanation_subject_verb_case_via_uri():
    """Test explanation via full ontology URI."""
    generator = ExplanationGenerator()
    expl = generator.generate_explanation(
        f"{BASE_URI}فاعل",
        {"case": "nominative"},
        {"case": "genitive"},
    )
    assert "مرفوعاً" in expl
    assert "مجروراً" in expl


# ── Noun-Adjective (نعت) ─────────────────────────────────────────────


def test_explanation_noun_adjective():
    """Test explanation for noun-adjective agreement mismatch."""
    generator = ExplanationGenerator()
    expl = generator.generate_explanation(
        "noun_adjective",
        {"gender": "feminine"},
        {"gender": "masculine"},
    )
    assert expl == "النعت يتبع المنعوت في التذكير والتأنيث"


def test_explanation_noun_adjective_number_via_uri():
    """Test noun-adjective number mismatch via URI."""
    generator = ExplanationGenerator()
    expl = generator.generate_explanation(
        f"{BASE_URI}نعت",
        {"number": "plural"},
        {"number": "singular"},
    )
    assert expl == "النعت يتبع المنعوت في العدد"


def test_explanation_noun_adjective_case_via_uri():
    """Test noun-adjective case mismatch via URI."""
    generator = ExplanationGenerator()
    expl = generator.generate_explanation(
        f"{BASE_URI}نعت",
        {"case": "genitive"},
        {"case": "nominative"},
    )
    assert expl == "النعت يتبع المنعوت في الإعراب"


def test_explanation_noun_adjective_definiteness_via_uri():
    """Test noun-adjective definiteness mismatch via URI."""
    generator = ExplanationGenerator()
    expl = generator.generate_explanation(
        f"{BASE_URI}نعت",
        {"definiteness": "definite"},
        {"definiteness": "indefinite"},
    )
    assert expl == "النعت يتبع المنعوت في التعريف والتنكير"


# ── Idafa (مضاف_اليه) ────────────────────────────────────────────────


def test_explanation_idafa():
    """Test explanation for Idafa sound masculine plural nun deletion."""
    generator = ExplanationGenerator()
    expl = generator.generate_explanation(
        "idafa",
        {"nun_deletion": "true"},
        {"number": "plural", "gender": "masculine"},
    )
    assert expl == "تحذف نون جمع المذكر السالم عند الإضافة"


def test_explanation_idafa_case_via_uri():
    """Test idafa case mismatch via URI."""
    generator = ExplanationGenerator()
    expl = generator.generate_explanation(
        f"{BASE_URI}مضاف_اليه",
        {"case": "genitive"},
        {"case": "nominative"},
    )
    assert expl == "المضاف إليه يكون مجروراً دائماً"


# ── Deputy Subject (نائب_الفاعل) ─────────────────────────────────────


def test_explanation_deputy_subject_case():
    """Test deputy subject case mismatch."""
    generator = ExplanationGenerator()
    expl = generator.generate_explanation(
        f"{BASE_URI}نائب_الفاعل",
        {"case": "nominative"},
        {"case": "accusative"},
    )
    assert "نائب الفاعل" in expl
    assert "مرفوعاً" in expl


def test_explanation_deputy_subject_number():
    """Test deputy subject number mismatch (VSO)."""
    generator = ExplanationGenerator()
    expl = generator.generate_explanation(
        f"{BASE_URI}نائب_الفاعل",
        {"number": "singular"},
        {"number": "plural"},
    )
    assert "نائب الفاعل" in expl


# ── Predicate (خبر_مبتدأ) ────────────────────────────────────────────


def test_explanation_predicate_case():
    """Test predicate case mismatch."""
    generator = ExplanationGenerator()
    expl = generator.generate_explanation(
        f"{BASE_URI}خبر_مبتدأ",
        {"case": "nominative"},
        {"case": "accusative"},
    )
    assert "الخبر" in expl


def test_explanation_predicate_gender():
    """Test predicate gender mismatch."""
    generator = ExplanationGenerator()
    expl = generator.generate_explanation(
        f"{BASE_URI}خبر_مبتدأ",
        {"gender": "feminine"},
        {"gender": "masculine"},
    )
    assert "الخبر يتبع المبتدأ في التذكير والتأنيث" == expl


# ── Objects (مفعولات) ────────────────────────────────────────────────


def test_explanation_mafool_bih():
    """Test direct object case mismatch."""
    generator = ExplanationGenerator()
    expl = generator.generate_explanation(
        f"{BASE_URI}مفعول_به",
        {"case": "accusative"},
        {"case": "nominative"},
    )
    assert "المفعول به" in expl


def test_explanation_mafool_fih():
    """Test adverbial object case mismatch."""
    generator = ExplanationGenerator()
    expl = generator.generate_explanation(
        f"{BASE_URI}مفعول_فيه",
        {"case": "accusative"},
        {"case": "nominative"},
    )
    assert "المفعول فيه" in expl


def test_explanation_mafool_mutlaq():
    """Test absolute object case mismatch."""
    generator = ExplanationGenerator()
    expl = generator.generate_explanation(
        f"{BASE_URI}مفعول_مطلق",
        {"case": "accusative"},
        {"case": "nominative"},
    )
    assert "المفعول المطلق" in expl


# ── Hal / Tamyeez ────────────────────────────────────────────────────


def test_explanation_hal_case():
    """Test hal case mismatch."""
    generator = ExplanationGenerator()
    expl = generator.generate_explanation(
        f"{BASE_URI}حال",
        {"case": "accusative"},
        {"case": "nominative"},
    )
    assert "الحال" in expl


def test_explanation_tamyeez_definiteness():
    """Test tamyeez definiteness mismatch."""
    generator = ExplanationGenerator()
    expl = generator.generate_explanation(
        f"{BASE_URI}تمييز_ذات",
        {"definiteness": "indefinite"},
        {"definiteness": "definite"},
    )
    assert "التمييز" in expl and "نكرة" in expl


# ── Particle-Governed ────────────────────────────────────────────────


def test_explanation_ism_kana():
    """Test ism kana case mismatch."""
    generator = ExplanationGenerator()
    expl = generator.generate_explanation(
        f"{BASE_URI}اسم_أخوات_كان",
        {"case": "nominative"},
        {"case": "accusative"},
    )
    assert "كان" in expl


def test_explanation_ism_inna():
    """Test ism inna case mismatch."""
    generator = ExplanationGenerator()
    expl = generator.generate_explanation(
        f"{BASE_URI}اسم_أخوات_ان",
        {"case": "accusative"},
        {"case": "nominative"},
    )
    assert "إن" in expl


def test_explanation_majroor():
    """Test genitive with preposition."""
    generator = ExplanationGenerator()
    expl = generator.generate_explanation(
        f"{BASE_URI}مجرور_بحرف",
        {"case": "genitive"},
        {"case": "nominative"},
    )
    assert "المجرور" in expl or "مجرور" in expl.lower()


# ── Jussive ──────────────────────────────────────────────────────────


def test_explanation_majzoom():
    """Test jussive mood explanation."""
    generator = ExplanationGenerator()
    expl = generator.generate_explanation(
        f"{BASE_URI}مجزوم",
        {"case": "jussive"},
        {"case": "nominative"},
    )
    assert "يُجزم" in expl or "الجزم" in expl.lower() or "جزم" in expl


# ── Vocative ─────────────────────────────────────────────────────────


def test_explanation_munada():
    """Test vocative case mismatch."""
    generator = ExplanationGenerator()
    expl = generator.generate_explanation(
        f"{BASE_URI}منادى",
        {"case": "accusative"},
        {"case": "nominative"},
    )
    assert "المنادى" in expl


# ── Badal ─────────────────────────────────────────────────────────


def test_explanation_badal():
    """Test badal (apposition) case mismatch."""
    generator = ExplanationGenerator()
    expl = generator.generate_explanation(
        f"{BASE_URI}بدل_من_اسم",
        {"case": "genitive"},
        {"case": "nominative"},
    )
    assert "البدل" in expl


# ── Generic Fallback ─────────────────────────────────────────────────


def test_explanation_unknown_relation_fallback():
    """Unknown relations should produce a generic Arabic fallback."""
    generator = ExplanationGenerator()
    expl = generator.generate_explanation(
        "http://arabicontology.org/oas_grammar.owl#unknown_relation",
        {"case": "nominative"},
        {"case": "accusative"},
    )
    assert len(expl) > 0  # Should return some fallback text
