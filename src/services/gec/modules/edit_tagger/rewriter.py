"""Text rewriting utilities for error correction."""

from src.services.gec.modules.edit_tagger.common import Alignment
from src.services.gec.schemas import EditOperation


class Rewriter:
    """Applies word-level edit tags to raw text."""

    def apply_edits(self, text: str, word_labels: list[str]) -> str:
        """Apply predicted word-level edit tags to the input text.

        Args:
            text: Original sentence.
            word_labels: List of tag strings, one per word (e.g., "K", "R_[cat]",
                "D", "I_[extra]").
        Returns:
            The corrected text string.
        """
        words = text.split()
        if len(words) != len(word_labels):
            raise ValueError(
                f"Word count ({len(words)}) does not match label count ({len(word_labels)})"
            )

        result = []
        for word, label in zip(words, word_labels):
            if label.startswith("K"):
                # Keep the original word
                result.append(word)
            elif label.startswith("R_["):
                # Replace with the provided token (strip the R_[ and ] parts)
                replacement = label[3:-1]
                result.append(replacement if replacement else word)
            elif label.startswith("D"):
                # Delete: skip the word
                continue
            elif label.startswith("I_["):
                # Insert before the current word
                insertion = label[3:-1]
                result.append(insertion)
                result.append(word)
            else:
                # Fallback: keep the word
                result.append(word)
        return " ".join(result)
