"""NWS (Next-Word Suggestion) Service.

References:
- docs/contracts/nws-contract.md

Authors:
    - Akram Hany
"""

from src.services.nws.schemas import NWSInput, NWSOutput, NWSSource, Suggestion

__all__ = [
    "NWSInput",
    "NWSOutput",
    "NWSSource",
    "Suggestion",
]
