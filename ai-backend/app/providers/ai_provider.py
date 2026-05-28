"""
LabMind AI — AI Analysis Provider (Abstract)
Defines the interface for blood smear analysis engines.
"""

from abc import ABC, abstractmethod


class AIProvider(ABC):
    """Abstract interface for blood smear analysis engines."""

    @abstractmethod
    def analyze(self, image_path: str) -> dict:
        """
        Run analysis on the image at the given path.

        Returns a dict with:
        - total_cells: int
        - sickle_count: int
        - normal_count: int
        - sickle_percentage: float
        - cell_details: list[dict]  (per-cell data)
        - annotated_image_path: str  (path to generated annotated image)
        """
        ...

    @abstractmethod
    def get_version(self) -> str:
        """Return the engine version string."""
        ...
