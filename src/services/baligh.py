"""Baligh API module."""

from pathlib import Path

from src.services.gec.schemas import GECInput
from src.services.gec.serving.controller import GECController
from src.services.gec.serving.dictionary_module import DictionaryService
from src.services.gec.serving.ontology_module import OntologyService
from src.services.gec.serving.tagger_module import EditTaggerService
from src.services.ged.detectors.lexicon.detector import LexiconDetector
from src.services.ged.detectors.ml.detector import MLDetector
from src.services.ged.detectors.rule_based.detector import RuleBasedDetector
from src.services.ged.orchestrator import GEDService
from src.services.ged.schemas import GEDInput, GEDOutput
from src.services.nws.features.cache.idioms import IdiomsCache
from src.services.nws.features.cache.manager import CacheManager
from src.services.nws.features.cache.phrases import PhrasesCache
from src.services.nws.features.cache.user_lru import UserLRUCache
from src.services.nws.features.nwp.hybrid.model import HybridArabicPredictor
from src.services.nws.features.nwp.lstm.model import LSTMNWPModel
from src.services.nws.features.nwp.word_ngram.model import WordNGramLM
from src.services.nws.features.nwp.word_ngram.serializer import load_ngram_model
from src.services.nws.features.wac.char_ngram.model import CharNGramLM
from src.services.nws.features.wac.char_ngram.serializer import load_model
from src.services.nws.orchestrator import NWSOrchestrator
from src.services.nws.schemas import NWSInput, NWSOutput
from src.services.preprocessing.orchestrator import preprocess
from src.services.preprocessing.schemas import PreprocessingInput, PreprocessingOutput
from src.services.ranker.ranker import RankerService
from src.services.ranker.schemas import RankerInput, RankerOutput


class Baligh:
    """Main Baligh class for Arabic text correction."""

    def __init__(self):
        """Initialize Baligh with all service controllers."""
        ontology = OntologyService()
        dictionary = DictionaryService()
        tagger = EditTaggerService()
        self.gec = GECController(ontology, dictionary, tagger)

        rule_detector = RuleBasedDetector()
        lexicon_detector = LexiconDetector()
        ml_detector = MLDetector()
        detectors = [rule_detector, lexicon_detector, ml_detector]
        self.ged = GEDService(detectors)

        curr_dir = Path(__file__).resolve()
        dir = curr_dir / "nws" / "data"
        ngram_data = load_ngram_model(dir / "word_ngram_lm_lstm.msgpack.gz")
        kn_model = WordNGramLM(ngram_data)
        neural_model = LSTMNWPModel(
            model_path=str(dir / "best_model.pt"),
            sp_model_path=str(dir / "arabic_bpe.model"),
        )
        hybrid = HybridArabicPredictor(neural_model, kn_model)

        char_model = CharNGramLM(load_model(dir / "char_ngram_lm_lstm.msgpack.gz"))

        cache_manager = CacheManager(
            tier1=IdiomsCache(dir / "idioms.yaml"),
            tier2=PhrasesCache(dir / "phrases.yaml"),
            tier3=UserLRUCache(maxsize=1000),
        )

        self.nws = NWSOrchestrator(
            cache_manager=cache_manager,
            nwp_model=hybrid,
            wac_model=char_model,
        )

        self.ranker = RankerService()

    def run(self, input_text: str, cursor_offset: int, current_fragment):
        """Run the full Baligh pipeline on input text."""
        preprocessing_input = PreprocessingInput(
            text=input_text, cursor_offset=cursor_offset
        )
        preprocessing_output: PreprocessingOutput = preprocess(preprocessing_input)

        ged_input = GEDInput(
            text=preprocessing_output.text,
            normalized_text=preprocessing_output.normalized_text,
            tokens=preprocessing_output.tokens,
            morph_features=preprocessing_output.morph_features,
        )
        ged_output: GEDOutput = self.ged.process(ged_input)

        gec_input = GECInput(
            text=preprocessing_output.text,
            tokens=preprocessing_output.tokens,
            morph_features=preprocessing_output.morph_features,
            errors_span=ged_output.errors,
        )
        gec_output = self.gec.run(gec_input)

        ranker_input = RankerInput(
            text=preprocessing_output.text,
            tokens=preprocessing_output.tokens,
            errors_span=ged_output.errors,
            errors_corrections=gec_output,
        )
        ranker_output: RankerOutput = self.ranker.rank(ranker_input)

        return ranker_output, ged_output

    def run_nws(self, preprocessed: PreprocessingOutput, curr_frag) -> NWSOutput:
        """Run the NWS"""
        nws_input = NWSInput(
            tokens=preprocessed.tokens,
            morph_features=preprocessed.morph_features,
            current_fragment=curr_frag,
            mode=preprocessed.mode,
        )
        return self.nws.predict(nws_input)
