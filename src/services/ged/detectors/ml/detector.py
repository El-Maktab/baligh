"""ML GED detector.

Authors:
    Amir Anwar
"""

from pathlib import Path
from typing import Any

from sklearn_crfsuite import CRF

from src.core.schemas import MorphAnalysis, Token
from src.runtime_config import load_runtime_config
from src.services.ged.detectors.base import BaseDetector
from src.services.ged.detectors.ml.artifact import load_bundle
from src.services.ged.detectors.ml.features import (
    FEATURE_SET_VERSION,
    sentence_features,
)
from src.services.ged.detectors.ml.labels import NO_ERROR, UNKNOWN
from src.services.ged.schemas import (
    ErrorCategory,
    ErrorSource,
    ErrorSpan,
    ProvenanceTier,
)


class MLDetector(BaseDetector):
    """Detect token errors with the ML sequence labeler.

    Checks that the runtime feature extractor matches the loaded model bundle.
    """

    def __init__(
        self,
        bundle_dir: Path | None = None,
        *,
        model: CRF | None = None,
        manifest: dict[str, Any] | None = None,
    ) -> None:
        """Load the model."""
        if (model is None) != (manifest is None):
            raise ValueError("Model and manifest must be provided together.")

        if model is None:
            configured_dir = (
                bundle_dir or load_runtime_config().ged.ml.resolved_bundle_dir
            )
            model, manifest = load_bundle(configured_dir)

        assert manifest is not None
        if manifest["features"]["version"] != FEATURE_SET_VERSION:
            raise ValueError("Model and runtime feature versions do not match.")

        self.model = model
        self.threshold = float(manifest["inference"]["error_threshold"])
        self.error_labels = tuple(
            label for label in model.classes_ if label != NO_ERROR
        )

    @property
    def name(self) -> str:
        """Subsystem name."""
        return ErrorSource.SEQUENCE_LABELER.value

    def detect(
        self,
        text: str,  # noqa: ARG002
        normalized_text: str,  # noqa: ARG002
        tokens: list[Token],
        morph_features: list[list[MorphAnalysis]],
    ) -> list[ErrorSpan]:
        """Predict labels and convert accepted errors to source spans."""
        if not tokens:
            return []

        features = sentence_features(tokens, morph_features)
        marginals = self.model.predict_marginals([features])[0]
        if len(marginals) != len(tokens):
            raise ValueError("Model returned a different number of token predictions.")

        predictions = [self._predict(row) for row in marginals]
        return self._to_spans(tokens, predictions)

    def _predict(self, marginals: dict[str, float]) -> tuple[str, float]:
        """Choose the strongest non-UC label when it clears the threshold."""
        label = max(self.error_labels, key=lambda item: marginals.get(item, 0.0))
        confidence = marginals.get(label, 0.0)
        return (label, confidence) if confidence >= self.threshold else (NO_ERROR, 0.0)

    def _to_spans(
        self,
        tokens: list[Token],
        predictions: list[tuple[str, float]],
    ) -> list[ErrorSpan]:
        """Build spans, joining only adjacent merge labels."""
        spans: list[ErrorSpan] = []
        index = 0
        while index < len(tokens):
            label, confidence = predictions[index]
            if label in {NO_ERROR, UNKNOWN}:
                index += 1
                continue

            end = index + 1
            if label == ErrorCategory.MERGE:
                while end < len(tokens) and predictions[end][0] == label:
                    confidence = min(confidence, predictions[end][1])
                    end += 1

            spans.append(self._build_span(tokens[index:end], label, confidence))
            index = end
        return spans

    @staticmethod
    def _build_span(tokens: list[Token], label: str, confidence: float) -> ErrorSpan:
        """Build a statistical ErrorSpan from one prediction group."""
        return ErrorSpan(
            span=(tokens[0].span[0], tokens[-1].span[1]),
            token_refs=[token.index for token in tokens],
            category=ErrorCategory(label),
            subtype=f"ml_{ErrorCategory(label).name.lower()}",
            confidence=confidence,
            sources=[ErrorSource.SEQUENCE_LABELER],
            provenance_tier=ProvenanceTier.TIER_3_STATISTICAL,
            explanation_eligible=False,
            explanation_text=None,
        )
