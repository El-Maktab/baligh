"""Maps internal domain features to Ontology concepts."""

from src.services.gec.features.camel_adapter import InternalMorphFeatures

BASE_URI = "http://arabicontology.org/oas_grammar.owl#"

POS_MAPPING = {
    "noun": f"{BASE_URI}اسم",
    "verb": f"{BASE_URI}فعل",
    "adj": f"{BASE_URI}اسم",  # Adjectives behave as nouns grammatically in Arabic
    "pron": f"{BASE_URI}ضمير",
    "prep": f"{BASE_URI}حرف_جر",
    "conj": f"{BASE_URI}حرف",
    "part": f"{BASE_URI}حرف",
    "num": f"{BASE_URI}اسم",
}

GENDER_MAPPING = {
    "masculine": f"{BASE_URI}مذكر",
    "feminine": f"{BASE_URI}مؤنث",
}

NUMBER_MAPPING = {
    "singular": f"{BASE_URI}مفرد",
    "dual": f"{BASE_URI}مثنى",
    "plural": f"{BASE_URI}جمع",
}

DEFINITENESS_MAPPING = {
    "definite": f"{BASE_URI}معرفة",
    "indefinite": f"{BASE_URI}نكرة",
}

CASE_MAPPING = {
    "nominative": f"{BASE_URI}اسم_مرفوع",
    "accusative": f"{BASE_URI}اسم_منصوب",
    "genitive": f"{BASE_URI}اسم_مجرور",
}


def map_to_ontology_concepts(features: InternalMorphFeatures) -> dict[str, str | None]:
    """Maps normalized internal morphological features to Ontology concept URIs.

    Args:
        features: Standardized InternalMorphFeatures.

    Returns:
        dict: A dictionary of mapped concepts, with keys:
              'pos', 'gender', 'number', 'definiteness', 'case'.
              Values are full URIs or None.
    """
    def_val = (
        DEFINITENESS_MAPPING.get(features.definiteness)
        if features.definiteness
        else None
    )
    return {
        "pos": POS_MAPPING.get(features.pos),
        "gender": GENDER_MAPPING.get(features.gender) if features.gender else None,
        "number": NUMBER_MAPPING.get(features.number) if features.number else None,
        "definiteness": def_val,
        "case": CASE_MAPPING.get(features.case) if features.case else None,
    }
