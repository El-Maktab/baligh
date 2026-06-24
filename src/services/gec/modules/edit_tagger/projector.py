"""Project word-level alignments to subword level."""

from src.services.gec.utils.string_utils import Tokenizer

from .common import Alignment, ProjectedExample
from .compressor import Compressor
from .extractor import Extractor


class SubwordProjector:
    """Projects word-level edits to subword level."""

    def __init__(self):
        self.tokenizer = Tokenizer()

    def _tokenize_words(self, words: list[str]) -> list[list[str]]:
        """Tokenize each word into Arabert subwords."""
        if(len(words) == 0): return []
        return [self.tokenizer.tokenize(word) if word != ' ' else [" "] for word in words]

    def compute_spans(self, tokens: list[str]) -> list[tuple[int, int]]:
        """Computes the character spans of each subword within the word."""
        current_ind = 0
        spans = []
        for token in tokens:
            clean_subword = token.replace("##", "")
            start = current_ind
            end = start + len(clean_subword) - 1
            spans.append((start, end))
            current_ind = end + 1
        return spans
    
    def find_corresponding_subword_edit(
        self,
        edit_char_ind: int,
        spans: list[tuple[int, int]],
    ) -> int:
        """Find the subword containing a character index."""
        for i, (start, end) in enumerate(spans):
            if start <= edit_char_ind <= end:
                return i
        return -1

    def project(
        self,
        segments: list[list[str]],
        edits_list: list[list[Alignment]],
    ) -> list[list[Alignment]]:
        """
        Project word-level edits to subword-level edits.

        Args:
            segments:
                List of words, where each word is represented
                by its subword tokens.

            edits_list:
                List of word alignments, one list per word.

        Returns:
            One projection list per subword token.
        """
        projection: list[list[Alignment]] = []
        
        for word_tokens, word_edits in zip(segments, edits_list):
            token_projection = [[] for _ in word_tokens]
            spans = self.compute_spans(word_tokens)
            for edit in word_edits:
                token_ind = self.find_corresponding_subword_edit(
                    edit.source_start,
                    spans,
                )

                if token_ind != -1:
                    token_projection[token_ind].append(edit)
            projection.extend(token_projection)


        return projection

    def compress_projection(
        self,
        subwords: list[str],
        projections: list[list[Alignment]],
        extractor: Extractor,
        compressor: Compressor,
    ) -> ProjectedExample:
        """Compress tags per subword."""
        compressed_tags = []
        compressed_tags_star = []

        for projection in projections:
            tags = extractor.extract_tags(projection)
            count_compressed, star_compressed = compressor.compress_tags(tags)
            compressed_tags.append(count_compressed)
            compressed_tags_star.append(star_compressed)

        return self.flatten(ProjectedExample(
            subwords=subwords,
            labels=compressed_tags,
            labels_star=compressed_tags_star,
        ))

    def flatten(self, projected_examples: ProjectedExample) -> ProjectedExample:
        projection_list = projected_examples.subwords
        items = [item for sublist in projection_list for item in sublist]
        return ProjectedExample(
            subwords=items,
            labels=projected_examples.labels,
            labels_star=projected_examples.labels_star,
        )