"""Unit tests for the MorphologicalGenerator."""

from src.services.gec.modules.dictionary.arramooz_client import ArramoozClient
from src.services.gec.modules.dictionary.morph_generator import (
    MorphologicalGenerator,
    strip_trailing_vowels,
)


def test_strip_trailing_vowels():
    """Test utility to strip short vowels and tanwin from vocalized forms."""
    assert strip_trailing_vowels("مُهَنْدِسٌ") == "مُهَنْدِس"
    assert strip_trailing_vowels("مُهَنْدِسُ") == "مُهَنْدِس"
    assert strip_trailing_vowels("مُهَنْدِسَ") == "مُهَنْدِس"


def test_morph_generator_noun_singular():
    """Test generating singular masculine and feminine noun forms."""
    client = ArramoozClient()
    generator = MorphologicalGenerator(client)

    # Singular Masculine Nominative Indefinite
    res = generator.generate_form(
        "هندس",
        "noun",
        {
            "number": "singular",
            "gender": "masculine",
            "case": "nominative",
            "definiteness": "indefinite",
            "lemma": "مهندس",
        },
    )
    assert len(res) > 0
    assert "مُهَنْدِسٌ" in res

    # Singular Feminine Accusative Definite
    res_fem = generator.generate_form(
        "هندس",
        "noun",
        {
            "number": "singular",
            "gender": "feminine",
            "case": "accusative",
            "definiteness": "definite",
            "lemma": "مهندس",
        },
    )
    print(res_fem)
    assert len(res_fem) > 0
    assert "المُهَنْدِسَةَ" in res_fem


def test_morph_generator_noun_plural_sound():
    """Test generating sound masculine and feminine plurals."""
    client = ArramoozClient()
    generator = MorphologicalGenerator(client)

    # Sound Masculine Plural Nominative (Definite)
    res = generator.generate_form(
        "هندس",
        "noun",
        {
            "number": "plural",
            "gender": "masculine",
            "case": "nominative",
            "definiteness": "definite",
            "lemma": "مهندس",
        },
    )
    assert "المُهَنْدِسُونَ" in res

    # Sound Masculine Plural Accusative Annexed (Idafa mudaf)
    res_annex = generator.generate_form(
        "علم",
        "noun",
        {
            "number": "plural",
            "gender": "masculine",
            "case": "accusative",
            "annex": True,
            "lemma": "معلم",
        },
    )
    assert len(res_annex) > 0
    assert "مُعَلِّمِي" in res_annex and "مَعَالِمًا" in res_annex


def test_morph_generator_noun_plural_broken():
    """Test generating broken plurals from the database."""
    client = ArramoozClient()
    generator = MorphologicalGenerator(client)

    # Broken Plural for root "علم" (عالم -> علماء)
    res = generator.generate_form(
        "علم",
        "noun",
        {
            "number": "plural",
            "gender": "masculine",
            "case": "nominative",
            "definiteness": "indefinite",
            "lemma": "عالم",
        },
    )
    assert len(res) > 0
    assert "عُلَمَاءٌ" in res


def test_morph_generator_verb_inflection():
    """Test verb inflections for number and gender."""
    client = ArramoozClient()
    generator = MorphologicalGenerator(client)

    # Conjugate past plural "كتبوا" to singular masculine
    res = generator.generate_form(
        "كتب",
        "verb",
        {
            "number": "singular",
            "gender": "masculine",
            "tense": "past",
        },
    )
    assert len(res) > 0
    assert "كَتَبَ" in res

    # Conjugate past plural "كتبوا" to singular feminine
    res_fem = generator.generate_form(
        "كتب",
        "verb",
        {
            "number": "singular",
            "gender": "feminine",
            "tense": "past",
        },
    )
    assert len(res_fem) > 0
    assert "كَتَبَت" in res_fem
