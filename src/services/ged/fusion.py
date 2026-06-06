"""Fusion model handles conflict resolution and merging of GED.

Authors:
  Amir Anwar
"""

from src.services.ged.schemas import ErrorSpan


def resolve_overlaps(errors: list[ErrorSpan]) -> list[ErrorSpan]:
    """Resolve overlapping errors.

    NOTE: this is a stub implementation, Will be replaced

    Args:
        errors: List of errors

    Returns:
        A list of errors with overlaps resolved.
    """
    if not errors:
        return []

    fused_errors = []

    fused_errors = errors.copy()

    return fused_errors
