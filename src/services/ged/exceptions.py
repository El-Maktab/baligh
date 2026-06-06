"""Custom exceptions for GED.

Authors:
  Amir Anwar
"""


class GEDDetectionError(Exception):
    """Raised when a GED detector fails."""

    def __init__(self, detector_name: str, message: str):
        """Inits with the failing detector name."""
        self.detector_name = detector_name
        super().__init__(message)
