"""Constants for the Ontology of Arabic Syntax."""

##### URI References #####

OWL_BASE_URI = "http://www.w3.org/2002/07/owl#"
RDFS_BASE_URI = "http://www.w3.org/2000/01/rdf-schema#"
RDF_BASE_URI = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
OAS_BASE_URI = "http://arabicontology.org/oas_grammar.owl#"


UNION_OF_URI = OWL_BASE_URI + "unionOf"
SUBCLASS_OF_URI = RDFS_BASE_URI + "subClassOf"
EQUIVALENT_CLASS_URI = OWL_BASE_URI + "equivalentClass"
INTERSECTION_OF_URI = OWL_BASE_URI + "intersectionOf"


OAS_VERB_URI = OAS_BASE_URI + "فعل"
OAS_VERB_TAM_URI = OAS_BASE_URI + "فعل_تام"
OAS_VERB_MOOD_INDICATIVE_URI = OAS_BASE_URI + "فعل_مرفوع"
OAS_VERB_MOOD_SUBJUNCTIVE_URI = OAS_BASE_URI + "فعل_منصوب"
OAS_VERB_MOOD_JUSSIVE_URI = OAS_BASE_URI + "فعل_مجزوم"

OAS_NOUN_URI = OAS_BASE_URI + "اسم"
OAS_NOUN_CASE_NOMINATIVE_URI = OAS_BASE_URI + "اسم_مرفوع"
OAS_NOUN_CASE_ACCUSATIVE_URI = OAS_BASE_URI + "اسم_منصوب"
OAS_NOUN_CASE_GENITIVE_URI = OAS_BASE_URI + "اسم_مجرور"

OAS_NOUN_DEFINITE_URI = OAS_BASE_URI + "اسم_معرفة"
OAS_NOUN_INDEFINITE_URI = OAS_BASE_URI + "اسم_نكرة"


#### Classes ######

NOUN_CASES = (
    "اسم_مرفوع",
    "اسم_منصوب",
    "اسم_مجرور",
    "اسم_معرفة",
    "اسم_نكرة",
)
VERB_MOODS = (
    "فعل_مرفوع",
    "فعل_منصوب",
    "فعل_مجزوم",
)

ONTOLOGY_PROPERTIES = {
    "اعرابه": "case",
    "تعيينه": "definiteness",
    "جنسه": "gender",
    "عدده": "number",
}

ONTOLOGY_CLASSES = {
    "الرفع": "nominative",
    "النصب": "accusative",
    "الجر": "genitive",
    "الجزم": "jussive",
    "معرفة": "definite",
    "نكرة": "indefinite",
    "مذكر": "masculine",
    "مؤنث": "feminine",
    "مفرد": "singular",
    "مثنى": "dual",
    "جمع": "plural",
}

BASE_PRIORITIES = {
    "مفعول": 7,
    "تمييز": 8,
    "بدل": 10,
    "توكيد": 10,
}
