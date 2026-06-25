"""Load and verify downloaded GED model."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
from typing import Any

import joblib
from sklearn_crfsuite import CRF

ARTIFACT_SCHEMA_VERSION = 1
DEFAULT_THRESHOLD = 0.35
MANIFEST_NAME = "manifest.json"
MODEL_NAME = "model.joblib"
CHECKSUMS_NAME = "SHA256SUMS"
LABEL_MAPPING_NAME = "label_mapping.json"
README_NAME = "README.md"
REQUIREMENTS_NAME = "requirements.txt"
SMOKE_TEST_NAME = "smoke_test.json"
THRESHOLD_SWEEP_NAME = "threshold_sweep.json"


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest for a file."""
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_manifest(bundle_dir: Path) -> dict[str, Any]:
    """Read the manifest."""
    manifest_path = bundle_dir / MANIFEST_NAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return manifest


def verify_bundle(bundle_dir: Path) -> dict[str, Any]:
    """Verify checksums and manifest metadata for a downloaded bundle."""
    bundle_dir = bundle_dir.resolve()
    manifest = read_manifest(bundle_dir)
    checksum_path = bundle_dir / CHECKSUMS_NAME
    expected_lines = checksum_path.read_text(encoding="utf-8").splitlines()
    if not expected_lines:
        raise ValueError(f"No checksums found in {checksum_path}.")

    for line in expected_lines:
        expected_digest, relative_name = line.split("  ", maxsplit=1)
        candidate = (bundle_dir / relative_name).resolve()
        if bundle_dir not in candidate.parents:
            raise ValueError(f"Unsafe checksum path: {relative_name!r}.")
        if not candidate.is_file():
            raise FileNotFoundError(candidate)
        actual_digest = sha256_file(candidate)
        if actual_digest != expected_digest:
            raise ValueError(
                f"Checksum mismatch for {relative_name}: "
                f"expected {expected_digest}, got {actual_digest}."
            )

    model_digest = manifest["files"][MODEL_NAME]["sha256"]
    if model_digest != sha256_file(bundle_dir / MODEL_NAME):
        raise ValueError("Model digest does not match manifest.json.")
    return manifest


def load_bundle(bundle_dir: Path, *, verify: bool = True) -> tuple[CRF, dict[str, Any]]:
    """Load a trusted CRF bundle after optional integrity verification."""
    manifest = verify_bundle(bundle_dir) if verify else read_manifest(bundle_dir)
    model: CRF = joblib.load(bundle_dir / MODEL_NAME)
    expected_classes = manifest["labels"]["model_classes"]
    if list(model.classes_) != expected_classes:
        raise ValueError("Loaded model classes do not match manifest.json.")
    return model, manifest


def installed_runtime_versions() -> dict[str, str]:
    """Return the runtime versions needed to load the model bundle."""
    packages = (
        "camel-tools",
        "joblib",
        "numpy",
        "python-crfsuite",
        "scikit-learn",
        "sklearn-crfsuite",
    )
    versions: dict[str, str] = {}
    for package in packages:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            continue
    return versions


def write_bundle(
    bundle_dir: Path,
    *,
    model: CRF,
    manifest: dict[str, Any],
    label_mapping: dict[str, str],
    threshold_sweep: list[dict[str, Any]],
    smoke_test: dict[str, Any],
    readme: str,
) -> None:
    """Write a complete trusted CRF bundle."""
    bundle_dir.mkdir(parents=True, exist_ok=True)

    model_path = bundle_dir / MODEL_NAME
    joblib.dump(model, model_path)

    manifest["files"] = {
        MODEL_NAME: {
            "bytes": model_path.stat().st_size,
            "sha256": sha256_file(model_path),
        }
    }

    files_to_write: dict[str, str] = {
        MANIFEST_NAME: json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        LABEL_MAPPING_NAME: json.dumps(label_mapping, ensure_ascii=False, indent=2)
        + "\n",
        THRESHOLD_SWEEP_NAME: json.dumps(threshold_sweep, ensure_ascii=False, indent=2)
        + "\n",
        SMOKE_TEST_NAME: json.dumps(smoke_test, ensure_ascii=False, indent=2) + "\n",
        README_NAME: readme.strip() + "\n",
        REQUIREMENTS_NAME: "".join(
            f"{package}=={version}\n"
            for package, version in installed_runtime_versions().items()
        ),
    }

    for name, content in files_to_write.items():
        (bundle_dir / name).write_text(content, encoding="utf-8")

    checksum_names = (
        MANIFEST_NAME,
        MODEL_NAME,
        LABEL_MAPPING_NAME,
        THRESHOLD_SWEEP_NAME,
        SMOKE_TEST_NAME,
        README_NAME,
        REQUIREMENTS_NAME,
    )
    checksums = [f"{sha256_file(bundle_dir / name)}  {name}" for name in checksum_names]
    (bundle_dir / CHECKSUMS_NAME).write_text(
        "\n".join(checksums) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    """Verify a downloaded bundle from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument("bundle_dir", type=Path)
    parser.add_argument(
        "--load-model",
        action="store_true",
    )

    args = parser.parse_args()
    if args.load_model:
        _, manifest = load_bundle(args.bundle_dir)
    else:
        manifest = verify_bundle(args.bundle_dir)
    print(
        f"verified {manifest['model']['name']} version {manifest['artifact_version']}"
    )


if __name__ == "__main__":
    main()
