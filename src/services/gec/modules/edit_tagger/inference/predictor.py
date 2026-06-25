from pathlib import Path

from loguru import logger
from transformers import AutoModelForTokenClassification
from src.services.gec.modules.edit_tagger.inference.inference import GECInferencePipeline
from src.services.gec.modules.edit_tagger.preprocessing.rewriter import Rewriter
from src.services.gec.utils.string_utils import Tokenizer

class LabelVocab:
    def __init__(self, id2label):
        self.id2label = id2label

class Predictor:
    def __init__(self, id2label, best_model_path= "./gec_models/edit_tagger_v1/checkpoint-3642"):
        self.id2label = id2label
        self.model_path = Path(best_model_path)
        self.rewriter = Rewriter()
        
    def _get_model(self):
        if not self.model_path.exists():
            logger.warning("Model not found.")
        else:
            inference_model = AutoModelForTokenClassification.from_pretrained(self.model_path)
            tokenizer = Tokenizer()
            label_vocab = LabelVocab(self.id2label)

            self.pipeline = GECInferencePipeline(
                model=inference_model,
                tokenizer=tokenizer,
                label_vocab=label_vocab,
            )

    def correct(self, text: str) -> str:
        res = self.pipeline.predict(text)
        return self.rewriter.apply_tag(res[0], res[1])
