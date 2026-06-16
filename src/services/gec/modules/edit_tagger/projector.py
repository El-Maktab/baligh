"""Project word-level alignments to subword level."""

from src.services.gec.utils.string_utils import Tokenizer

from .common import Alignment, ProjectedExample
from .compressor import Compressor
from .extractor import Extractor


# class SubwordProjector:
#     """Projects word-level alignments to subword level."""

#     def __init__(self):
#         self.tokenizer = Tokenizer()

#     def compute_spans(self, tokens: list[str]) -> list[tuple[int, int]]:
#         """Computes the character spans of each subword within the word."""
#         current_ind = 0
#         spans = []
#         for token in tokens:
#             clean_subword = token.replace("##", "")
#             start = current_ind
#             end = start + len(clean_subword) - 1
#             spans.append((start, end))
#             current_ind = end + 1
#         return spans

#     def compute_global_spans(
#         self, word_span: tuple[int, int], token_span: tuple[int, int]
#     ) -> tuple[int, int]:
#         """Convert a local token span to a global character span."""
#         start = word_span[0] + token_span[0]
#         end = start + (token_span[1] - token_span[0])
#         return (start, end)

#     def get_spans(self, segments: list[Token]) -> list[tuple[int, int]]:
#         """Get character spans for each token."""
#         return [token.span for token in segments]

#     def find_corresponding_subword_edit(
#         self, edit_char_ind: int, spans: list[tuple[int, int]]
#     ) -> int:
#         """Finds the index of the subword that contains the given character index."""
#         for i, (start, end) in enumerate(spans):
#             if start <= edit_char_ind <= end:
#                 return i
#         return -1

#     def _tokenize_words(self, words: list[str]) -> list[list[str]]:
#         """Tokenize each word into Arabert subwords."""
#         return [self.tokenizer.tokenize(word) for word in words]

#     def _compute_global_subword_spans(
#         self, words_spans: list[tuple[int, int]], tokens_list: list[list[str]]
#     ) -> list[list[tuple[int, int]]]:
#         """Compute global character spans for every subword of every word."""
#         global_spans: list[list[tuple[int, int]]] = []
#         for word_ind, subwords in enumerate(tokens_list):
#             local_spans = self.compute_spans(subwords)
#             word_global = [
#                 self.compute_global_spans(words_spans[word_ind], ls)
#                 for ls in local_spans
#             ]
#             global_spans.append(word_global)
#         return global_spans

#     def project(
#         self, segments: list[Token], edits_list: list[Alignment]
#     ) -> list[list[Alignment]]:
#         """Projects word-level edits to subword level."""
#         words: list[str] = [segment.form for segment in segments]
#         words_spans: list[tuple[int, int]] = self.get_spans(segments)
#         tokens_list: list[list[str]] = self._tokenize_words(words)
#         global_tokens_spans = self._compute_global_subword_spans(
#             words_spans, tokens_list
#         )

#         flat_spans: list[tuple[int, int]] = []
#         for word_spans in global_tokens_spans:
#             flat_spans.extend(word_spans)

#         projection: list[list[Alignment]] = [[] for _ in flat_spans]
#         for edit in edits_list:
#             subword_ind = self.find_corresponding_subword_edit(
#                 edit.source_start, flat_spans
#             )
#             if subword_ind != -1:
#                 projection[subword_ind].append(edit)
#         return projection

#     def compress_projection(
#         self,
#         subwords: list[str],
#         projections: list[list[Alignment]],
#         extractor: Extractor,
#         compressor: Compressor,
#     ) -> ProjectedExample:
#         """Compresses tags per subword for each word."""
#         compressed_tags = []
#         for projection in projections:
#             tags = extractor.extract_tags(projection)
#             compressed_tags.append(compressor.compress_tags(tags))
#         return ProjectedExample(subwords=subwords, labels=compressed_tags)

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

        for projection in projections:
            tags = extractor.extract_tags(projection)
            compressed_tags.append(
                compressor.compress_tags(tags)
            )

        return self.flatten(ProjectedExample(
            subwords=subwords,
            labels=compressed_tags,
        ))

    def flatten(self, projected_examples: ProjectedExample) -> ProjectedExample:
        projection_list = projected_examples.subwords
        items = [item for sublist in projection_list for item in sublist]
        return ProjectedExample(subwords=items, labels=projected_examples.labels)