"""GED evaluation module based on Multiple datasets."""

from src.services.ged.evaluation.models import (
    EvaluationConfig,
    EvaluationPolicy,
    EvaluationReport,
)
from src.services.ged.evaluation.runner import evaluate

__all__ = ["EvaluationConfig", "EvaluationPolicy", "EvaluationReport", "evaluate"]
