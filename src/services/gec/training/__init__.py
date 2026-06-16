"""Training components for the GEC edit tagger model."""

__all__ = [
    "GECTaggerModel",
    "GECTrainingDataset",
    "build_trainer",
    "compute_metrics",
]


def __getattr__(name):
    if name in __all__:
        if name == "GECTaggerModel":
            from src.services.gec.training.model import GECTaggerModel

            return GECTaggerModel
        if name == "GECTrainingDataset":
            from src.services.gec.training.datasets import GECTrainingDataset

            return GECTrainingDataset
        if name == "build_trainer":
            from src.services.gec.training.trainer import build_trainer

            return build_trainer
        if name == "compute_metrics":
            from src.services.gec.training.metrics import compute_metrics

            return compute_metrics
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
