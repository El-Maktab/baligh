from dataclasses import asdict
from pathlib import Path

import json

from src.services.gec.modules.edit_tagger.aligner import Aligner
from src.services.gec.modules.edit_tagger.compressor import Compressor
from src.services.gec.modules.edit_tagger.extractor import Extractor
from src.services.gec.modules.edit_tagger.projector import SubwordProjector
from src.services.gec.modules.edit_tagger.rewriter import Rewriter
from src.services.gec.modules.edit_tagger.common import Alignment, ProjectedExample
from src.services.gec.features.parser import ParallelCorpusParser

class FeatureBuilder:
    """Builds projected training examples from a parallel corpus."""
    CHECKPOINT_SIZE = 5000

    def __init__(
        self,
        parser: ParallelCorpusParser,
        aligner: Aligner,
        rewriter: Rewriter,
        extractor: Extractor,
        compressor: Compressor,
        projector: SubwordProjector,
    ) -> None:
        self.parser = parser
        self.aligner = aligner
        self.rewriter = rewriter
        self.extractor = extractor
        self.compressor = compressor
        self.projector = projector


    def build_pipeline(
        self,
        source_path: str,
        target_path: str,
        checkpoint_path: str | None = None,
    ) -> list[ProjectedExample]:
        """Build projected examples from a parallel corpus."""

        src_path = Path(source_path)
        tgt_path = Path(target_path)

        parallel_examples = self.parser.parse(
            src_path,
            tgt_path,
        )

        processed_results: list[ProjectedExample] = []

        all_results: list[ProjectedExample] = []

        checkpoint_file = (
            Path(checkpoint_path)
            if checkpoint_path
            else None
        )
        curr_checkpoint = 1
        for idx, example in enumerate(parallel_examples, start=1):
            print(idx)
            word_aligns = self.aligner.align_words(
                example.source,
                example.target,
            )

            inter_source = self.rewriter.apply_word_edits(
                example.source,
                word_aligns,
            )

            char_aligns: list[list[Alignment]] = []
            target_words = example.target.split(" ")

            for src, tgt in zip(inter_source, target_words):
                aligned_src_word = self.aligner.align_characters(src,tgt)
                char_aligns.append(aligned_src_word)
            
            tokens: list[list[str]] = self.projector._tokenize_words(inter_source)
            
            projections = self.projector.project(
                tokens,
                char_aligns,
            )

            examp : ProjectedExample = self.projector.compress_projection(
                tokens,
                projections,
                self.extractor,
                self.compressor,
            )
            processed_results.append(examp)
            all_results.append(examp)
            if (
                checkpoint_file is not None
                and len(processed_results) >= self.CHECKPOINT_SIZE
            ):
                with checkpoint_file.open(
                    "a",
                    encoding="utf-8",
                ) as f:
                    for result in processed_results:
                        f.write(json.dumps(asdict(result), ensure_ascii=False))
                        f.write("\n")

                print(
                    f"{curr_checkpoint} Checkpoint saved at example {idx}"
                )
                curr_checkpoint+=1
                processed_results.clear()            
                if (idx > 400): return all_results
        if checkpoint_file is not None and processed_results:
            with checkpoint_file.open(
                "a",
                encoding="utf-8",
            ) as f:
                for result in processed_results:
                    f.write(json.dumps(asdict(result), ensure_ascii=False))
                    f.write("\n")

            print("Final checkpoint saved")
        return all_results
