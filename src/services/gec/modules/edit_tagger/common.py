"""Common data structures and enums for edit tagging."""

from dataclasses import dataclass
from enum import StrEnum

from src.services.gec.schemas import EditOperation


@dataclass
class ProjectedExample:
    subwords: list[str]
    labels: list[str]
    labels_star: list[str] | None = None


@dataclass
class JSONLEditTagExample:
    input_ids: list[int]
    attention_mask: list[int]
    labels: list[int]


class AlignmentType(StrEnum):
    """Type of alignment."""

    WORD = "WORD"
    CHARACTER = "CHARACTER"


@dataclass
class Alignment:
    """Represents an alignment between source and target word spans.

    Stores the alignment between a span of source words and a span of target
    words, along with the edit operation.
    """

    source_start: int
    source_end: int

    target_start: int
    target_end: int

    operation: EditOperation
    label: str | None = None
    alignment_type: AlignmentType = AlignmentType.WORD


@dataclass
class BackPointer:
    """Represents a back pointer in the DP table.

    Stores the operation and previous indices for backtracking through the
    dynamic programming table.
    """

    operation: EditOperation

    prev_i: int
    prev_j: int


@dataclass
class ParallelExample:
    """Parallel example with source and target text."""

    source: str
    target: str
