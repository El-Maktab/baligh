"""Thin wrapper around the GEC & GED services.

This module is used by the API to run the GEC and GED stages of Baligh.
"""

from functools import lru_cache

from src.services.baligh import Baligh
from src.services.ged.schemas import GEDOutput
from src.services.ranker.schemas import RankerOutput


@lru_cache(maxsize=1)
def _get_baligh() -> Baligh:
    """Build the shared Baligh service once per process."""
    return Baligh()


def run(text: str) -> tuple[RankerOutput, GEDOutput]:
    """Run the GEC and GED stages of Baligh on the input text."""
    return _get_baligh().run(text)
