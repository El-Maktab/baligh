"""Protocol definition for GEC correction modules."""

from typing import Protocol

from src.services.gec.schemas import (
    GECInput,
    ModuleResult,
)


class GECModule(Protocol):
    """Protocol that all GEC correction modules must implement."""

    def run(self, input: GECInput) -> ModuleResult:
        """Run the module on the given input and return results."""
        ...
