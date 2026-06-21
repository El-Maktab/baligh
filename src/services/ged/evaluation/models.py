"""Public models for GED evaluation.

Author:
  Amir Anwar
"""

from pathlib import Path

from pydantic import BaseModel, Field

DEFAULT_DATASETS = ("qalb14", "qalb15_l1", "qalb15_l2", "zaebuc")


class EvaluationPolicy(BaseModel):
    """Eval fusion and filtering policies."""

    ignored_score_categories: tuple[str, ...] = ("SE",)
    excluded_rule_subtypes: tuple[str, ...] = ("spacing",)
    excluded_fusion_rule_categories: tuple[str, ...] = ("SY", "SE")
    allowed_fusion_rule_subtypes: tuple[str, ...] = ()


class EvaluationConfig(BaseModel):
    """Eval run config."""

    datasets: tuple[str, ...] = DEFAULT_DATASETS
    output_path: Path = Path("artifacts/ged/evaluation/report.json")
    limit: int | None = Field(default=None, ge=1)
    policy: EvaluationPolicy = Field(default_factory=EvaluationPolicy)


class DatasetStats(BaseModel):
    """Datasets stats."""

    sentences: int
    tokens: int
    errors: int
    unknown_errors: int
    preprocessing_fallback_tokens: int


class BinaryMetrics(BaseModel):
    """Binary GED metrics."""

    tp: int
    fp: int
    fn: int
    tn: int
    precision: float
    recall: float
    f1: float
    false_positives_per_1000: float


class CategoryMetrics(BaseModel):
    """Metrics for one GED category."""

    tp: int
    fp: int
    fn: int
    precision: float
    recall: float
    f1: float
    support: int


class MetricReport(BaseModel):
    """Metrics."""

    binary: BinaryMetrics
    categories: dict[str, CategoryMetrics]
    category_micro: CategoryMetrics
    category_macro: CategoryMetrics


class DatasetReport(BaseModel):
    """Results for one dataset."""

    sha256: str
    stats: DatasetStats
    systems: dict[str, MetricReport]
    preprocessing_strata: dict[str, dict[str, MetricReport]]


class EvaluationReport(BaseModel):
    """Machine readable, made to be analysed, result of a GED evaluation run."""

    schema_version: int = 2
    model_artifact_version: str
    detector_names: tuple[str, ...]
    datasets: dict[str, DatasetReport]
    aggregate: dict[str, MetricReport]
    aggregate_preprocessing_strata: dict[str, dict[str, MetricReport]]
    metric_definitions: dict[str, str]
    config: dict[str, object]
