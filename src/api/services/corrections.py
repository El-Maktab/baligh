"""Thin wrapper around the GEC & GED services.

This module is used by the API to run the GEC and GED stages of Baligh.
"""

from src.api.services.baligh_singleton import get_baligh
from src.services.ged.schemas import GEDOutput
from src.services.ranker.schemas import RankerOutput


def run(text: str) -> tuple[RankerOutput, GEDOutput]:
    """Run the GEC and GED stages of Baligh on the input text."""
    return get_baligh().run(text)
