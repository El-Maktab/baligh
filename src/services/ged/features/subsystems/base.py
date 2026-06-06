"""Base class for GED subsystems.

Authors:
  Amir Anwar
"""

from abc import ABC, abstractmethod

from src.services.ged.schemas import ErrorSpan, MorphAnalysis, Token


class BaseDetector(ABC):
    """Abstract base class for GED subsystems."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the subsystem."""

    @abstractmethod
    def detect(
        self,
        text: str,
        normalized_text: str,
        tokens: list[Token],
        morph_features: list[list[MorphAnalysis]],
    ) -> list[ErrorSpan]:
        """Detect error spans in the input text.

        Args:
            text (str): Original input text.
            normalized_text (str): Normalized input text.
            tokens (list[Token]): List of tokens.
            morph_features (list[list[MorphAnalysis]]): Per-token morphological
                candidates outer list is indexed by token, inner list holds all
                candidates with the disambiguated one always first

        Returns:
            list[ErrorSpan]: List of detected error spans. Each span should include the
            error category and source (subsystem name) for the span, in addition to the
            character offsets.
        """
