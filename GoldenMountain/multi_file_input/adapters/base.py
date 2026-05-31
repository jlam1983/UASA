"""Base interface for file type adapters.

Each adapter has exactly 2 methods:
- parse(source) -> list[dict] (input to records)
- serialize(data, dest) -> None (records to output)

And 1 helper:
- normalize(data) -> dict (records to standard JSON with metadata)
"""

from abc import ABC, abstractmethod
from typing import Any


class FileTypeAdapter(ABC):
    """Base interface for all file type adapters."""

    @abstractmethod
    def parse(self, source: str | bytes) -> list[dict]:
        """Parse source and return list of records.

        Args:
            source: File content as string or bytes

        Returns:
            List of record dicts
        """
        pass

    @abstractmethod
    def serialize(self, data: list[dict], destination: str) -> None:
        """Serialize records to destination.

        Args:
            data: List of record dicts
            destination: Output file path
        """
        pass

    @abstractmethod
    def get_schema(self) -> dict:
        """Return schema of parsed data."""
        pass

    @abstractmethod
    def validate(self, data: list[dict]) -> bool:
        """Validate data structure.

        Args:
            data: List of record dicts

        Returns:
            True if valid, False otherwise
        """
        pass

    def normalize(self, data: list[dict], source_type: str = "unknown") -> dict:
        """Convert parsed data to standard JSON format.

        Args:
            data: List of record dicts
            source_type: Source file type (csv, json, xml, etc.)

        Returns:
            Normalized JSON with metadata and records
        """
        from ..normalizer import JSONNormalizer
        normalizer = JSONNormalizer()
        return normalizer.normalize(data, source_type, "file")
