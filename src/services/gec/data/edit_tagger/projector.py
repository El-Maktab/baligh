"""Project word-level alignments to subword level."""

from src.core.schemas import Token

from .common import Alignment
from .compressor import Compressor
from .extractor import Extractor


class SubwordProjection:
    """Projects word-level alignments to subword level."""

    # def compute_spans(self, tokens: list[Token]) -> list[tuple[int, int]]:
    #     """Computes the character spans of each subword within the word."""
    #     current_ind = 0
    #     spans = []
    #     for subword in tokens:
    #         clean_subword = subword.replace("##", "")
    #         start = current_ind
    #         end = start + len(clean_subword) - 1
    #         spans.append((start, end))
    #         current_ind = end + 1
    #     return spans

    def get_spans(self, tokens: list[Token]) -> list[tuple[int, int]]:
        """Get character spans for each token."""
        return [token.span for token in tokens]

    def find_corresponding_subword_edit(
        self, char_ind: int, spans: list[tuple[int, int]]
    ) -> int:
        """Finds the index of the subword that contains the given character index."""
        for i, (start, end) in enumerate(spans):
            if start <= char_ind <= end:
                return i
        raise ValueError(f"Character index {char_ind} out of bounds")

    def project(
        self, tokens: list[Token], edits: list[Alignment]
    ) -> list[list[Alignment]]:
        """Projects word-level edits to subword level."""
        spans = self.get_spans(tokens)
        projection: list[list[Alignment]] = [[] for _ in tokens]

        for edit in edits:
            subword_ind = self.find_corresponding_subword_edit(edit.source_start, spans)
            projection[subword_ind].append(edit)
        return projection

    def compress_projection(
        self,
        projections: list[list[Alignment]],
        extractor: Extractor,
        compressor: Compressor,
    ) -> list[str]:
        """Compresses tags per subword for each word."""
        compressed_tags = []
        for projection in projections:
            tags = extractor.extract_tags(projection)
            compressed_tags.append(compressor.compress_tags(tags))
        return compressed_tags
