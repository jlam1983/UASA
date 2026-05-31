"""Base sampling strategy interface."""

from abc import ABC, abstractmethod
from typing import Any


class SamplingStrategy(ABC):
    """Base class for sampling strategies."""

    @abstractmethod
    def sample(self, data: list[dict], sample_size: int, **kwargs) -> list[dict]:
        """Sample data according to strategy."""
        pass

    def validate_params(self, **kwargs) -> None:
        """Validate strategy parameters."""
        pass