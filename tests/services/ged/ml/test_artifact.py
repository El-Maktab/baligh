"""Tests for GED ML artifact integrity checks."""

import hashlib
import json
from pathlib import Path

import pytest
from src.services.ged.detectors.ml.artifact import verify_bundle


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_verify_bundle_rejects_changed_file(tmp_path: Path) -> None:
    """A changed artifact file fails checksum verification."""
    model_path = tmp_path / "model.joblib"
    model_path.write_bytes(b"trusted model placeholder")
    manifest = {
        "artifact_schema_version": 1,
        "files": {
            "model.joblib": {
                "sha256": _digest(model_path),
            }
        },
        "labels": {"model_classes": ["UC"]},
        "model": {"name": "test-model"},
        "artifact_version": "0.0.0",
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    checksums = {
        "manifest.json": _digest(manifest_path),
        "model.joblib": _digest(model_path),
    }
    (tmp_path / "SHA256SUMS").write_text(
        "".join(f"{digest}  {name}\n" for name, digest in checksums.items()),
        encoding="utf-8",
    )

    model_path.write_bytes(b"changed")

    with pytest.raises(ValueError, match="Checksum mismatch"):
        verify_bundle(tmp_path)
