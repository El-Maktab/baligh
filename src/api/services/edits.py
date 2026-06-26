# src/api/services/gec.py
"""Thin wrapper around the GEC pipeline.

It receives a ``PreprocessingOutput`` (with error spans) and runs the three
GEC sub‑modules (TAG, ONTOLOGY, DICTIONARY). The repository already contains
these modules under ``src.services.gec.modules`` - each module exposes an
``engine.run`` function that returns a ``ModuleResult``. This wrapper aggregates
the results into a ``GECOutput`` model defined in ``src.services.gec.schemas``.
"""

from src.services.gec.modules.dictionary.engine import DictionaryEngine
from src.services.gec.modules.ontology.engine import OntologyEngine

# from src.services.gec.modules.edit_tagger import engine as tagger_engine
from src.services.gec.schemas import GECInput, GECOutput, ModuleResult


def run(preproc_output) -> GECOutput:
    """Run the three GEC modules and return a GECOutput."""
    # Build a very simple GECInput – the actual schema may contain more fields.
    gec_input = GECInput(
        text=preproc_output.text,
        tokens=preproc_output.tokens,
        morph_features=preproc_output.morph_features,
        errors_span=getattr(preproc_output, "errors_span", []),
    )
    ontology_engine = OntologyEngine()
    dictionary_engine = DictionaryEngine()
    # tag_result: ModuleResult = tagger_engine.run(gec_input)
    ontology_result: ModuleResult = ontology_engine.process(gec_input)
    dictionary_result: ModuleResult = dictionary_engine.process(gec_input)
    return GECOutput([ontology_result, dictionary_result])
