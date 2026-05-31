"""Factory for creating storage containers."""

from typing import Any

from .base import StorageContainer


class ContainerFactory:
    """Factory to create storage containers by type."""

    _container_classes: dict[str, type[StorageContainer]] = {}

    @classmethod
    def register(cls, name: str, container_class: type[StorageContainer]) -> None:
        """Register a container class by name."""
        cls._container_classes[name.lower()] = container_class

    @classmethod
    def create(cls, name: str, **kwargs) -> StorageContainer:
        """Create a container by name."""
        if name.lower() not in cls._container_classes:
            available = ", ".join(cls._container_classes.keys())
            raise ValueError(f"Unknown container '{name}'. Available: {available}")
        return cls._container_classes[name.lower()](**kwargs)

    @classmethod
    def available(cls) -> list[str]:
        """List available container types."""
        return list(cls._container_classes.keys())


# Auto-register built-in containers
from .sqlite_container import SQLiteContainer
from .postgres_container import PostgreSQLContainer
from .mongo_container import MongoContainer
from .redis_container import RedisContainer

ContainerFactory.register("sqlite", SQLiteContainer)
ContainerFactory.register("postgres", PostgreSQLContainer)
ContainerFactory.register("mongodb", MongoContainer)
ContainerFactory.register("redis", RedisContainer)
