"""Extract edit tags from word alignments."""

from src.services.gec.schemas import EditOperation

from ..common import Alignment


class Extractor:
    """Extracts edit tags from word alignments."""

    def extract_tags(self, alignment: list[Alignment]) -> list[str]:
        """Compresses a word alignment into an edit tag string."""
        tags = list[str]()
        for a in alignment:
            if a.operation == EditOperation.KEEP:
                tags.append("K")
            elif a.operation == EditOperation.REPLACE:
                label = a.label
                if label is None:
                    raise ValueError("Label cannot be None for REPLACE operation")
                tags.append(f"R_[{label}]")

            elif a.operation == EditOperation.INSERT:
                label = a.label
                if label is None:
                    raise ValueError("Label cannot be None for INSERT operation")
                tags.append(f"I_[{label}]")

            elif a.operation == EditOperation.DELETE:
                tags.append("D")
            elif a.operation == EditOperation.MERGE:
                tags.append("M")
            elif a.operation == EditOperation.SPLIT:
                tags.append("S")
            else:
                raise ValueError(f"Unknown operation: {a.operation}")
        return tags
