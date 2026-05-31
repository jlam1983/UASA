"""Base storage container interface."""

from abc import ABC, abstractmethod
from typing import Any


class StorageContainer(ABC):
    """Abstract base class for all storage containers."""

    @abstractmethod
    def store(self, table: str, data: list[dict]) -> None:
        """Store records in container."""
        pass

    @abstractmethod
    def load(self, table: str, query: dict | None = None) -> list[dict]:
        """Load records with optional query."""
        pass

    @abstractmethod
    def update(self, table: str, query: dict, data: dict) -> int:
        """Update matching records. Returns number updated."""
        pass

    @abstractmethod
    def delete(self, table: str, query: dict) -> int:
        """Delete matching records. Returns number deleted."""
        pass

    @abstractmethod
    def exists(self, table: str) -> bool:
        """Check if table/collection exists."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close container connection."""
        pass
