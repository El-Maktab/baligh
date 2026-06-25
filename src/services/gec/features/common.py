from src.services.gec.modules.edit_tagger.preprocessing.aligner import Aligner
from src.services.gec.modules.edit_tagger.preprocessing.compressor import Compressor
from src.services.gec.modules.edit_tagger.preprocessing.extractor import Extractor
from src.services.gec.modules.edit_tagger.preprocessing.projector import SubwordProjector
from src.services.gec.modules.edit_tagger.preprocessing.rewriter import Rewriter
from src.services.gec.features.feature_builder import FeatureBuilder
from src.services.gec.features.parser import ParallelCorpusParser

def build_feature_builder() -> FeatureBuilder:
    parser = ParallelCorpusParser()
    aligner = Aligner()
    rewriter = Rewriter()
    extractor = Extractor()
    compressor = Compressor()
    projector = SubwordProjector()

    return FeatureBuilder(
        parser=parser,
        aligner=aligner,
        rewriter=rewriter,
        extractor=extractor,
        compressor=compressor,
        projector=projector,
    )