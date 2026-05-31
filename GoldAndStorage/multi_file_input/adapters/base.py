"""Base interface for file type adapters."""

from abc import ABC, abstractmethod
from typing import Any


class FileTypeAdapter(ABC):
    """Base interface for all file type adapters."""

    @abstractmethod
    def parse(self, source: str | bytes) -> list[dict]:
        """Parse source and return list of records."""
        pass

    @abstractmethod
    def serialize(self, data: list[dict], destination: str) -> None:
        """Serialize records to destination."""
        pass

    @abstractmethod
    def get_schema(self) -> dict:
        """Return schema of parsed data."""
        pass

    @abstractmethod
    def validate(self, data: list[dict]) -> bool:
        """Validate data structure."""
        pass
