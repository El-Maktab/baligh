"""Edit segregation utilities."""

from dataclasses import dataclass

from src.services.gec.modules.edit_tagger.common import Alignment
from src.services.gec.modules.edit_tagger.punctuation import (
    is_punctuation,
    PUNCTUATION_SET,
)


@dataclass
class SegregatedEdits:
    """Container for segregated edits."""

    source_text: str
    target_text: str
    punctuation_edits: list[Alignment]
    non_punctuation_edits: list[Alignment]


class EditSegregator:
    """Segregates alignments into punctuation and non-punctuation edits."""

    def segregate(
        self,
        source_tokens: list[str],
        target_tokens: list[str],
        edits: list[Alignment],
    ) -> SegregatedEdits:
        """
        Split alignments into punctuation and non-punctuation edits.

        Args:
            source_tokens: tokenized source sentence
            target_tokens: tokenized target sentence
            edits: alignment list

        Returns:
            SegregatedEdits
        """

        punctuation_edits = []
        non_punctuation_edits = []

        for edit in edits:
            if self._is_punctuation_edit(
                source_tokens,
                target_tokens,
                edit,
            ):
                punctuation_edits.append(edit)
            else:
                non_punctuation_edits.append(edit)

        return SegregatedEdits(
            source_text=" ".join(source_tokens),
            target_text=" ".join(target_tokens),
            punctuation_edits=punctuation_edits,
            non_punctuation_edits=non_punctuation_edits,
        )

    def _is_punctuation_edit(
        self,
        source_tokens: list[str],
        target_tokens: list[str],
        edit: Alignment,
    ) -> bool:
        """
        Determine whether an alignment represents only punctuation.
        """

        src_span = source_tokens[
            edit.source_start : edit.source_end + 1
        ]

        tgt_span = target_tokens[
            edit.target_start : edit.target_end + 1
        ]

        span_tokens = src_span + tgt_span

        if not span_tokens:
            return False

        return all(
            token in PUNCTUATION_SET
            or is_punctuation(token)
            for token in span_tokens
        )

    def remove_punctuation_edits(
        self,
        source_tokens: list[str],
        target_tokens: list[str],
        edits: list[Alignment],
    ) -> list[Alignment]:
        """
        Return only non-punctuation edits.
        """

        return [
            edit
            for edit in edits
            if not self._is_punctuation_edit(
                source_tokens,
                target_tokens,
                edit,
            )
        ]

    def keep_only_punctuation_edits(
        self,
        source_tokens: list[str],
        target_tokens: list[str],
        edits: list[Alignment],
    ) -> list[Alignment]:
        """
        Return only punctuation edits.
        """

        return [
            edit
            for edit in edits
            if self._is_punctuation_edit(
                source_tokens,
                target_tokens,
                edit,
            )
        ]