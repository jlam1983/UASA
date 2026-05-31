"""Manager for handling multiple storage containers."""

from typing import Any

from .base import StorageContainer
from .factory import ContainerFactory


class ContainerManager:
    """Manage multiple storage containers with a default."""

    def __init__(self, default: str = "sqlite", **config):
        self._containers: dict[str, StorageContainer] = {}
        self._default = default
        self._config = config

    def add(self, name: str | None = None, container_type: str | None = None, **kwargs) -> StorageContainer:
        """Add and connect a container. Uses default if type not specified."""
        name = name or self._default
        container_type = container_type or self._default
        cfg = {**self._config.get(container_type, {}), **kwargs}
        container = ContainerFactory.create(container_type, **cfg)
        self._containers[name] = container
        return container

    def get(self, name: str | None = None) -> StorageContainer:
        """Get a container by name or return default."""
        if name is None:
            name = self._default
        if name not in self._containers:
            raise KeyError(f"Container '{name}' not found. Call add() first.")
        return self._containers[name]

    def remove(self, name: str) -> None:
        """Remove and close a container."""
        if name in self._containers:
            self._containers[name].close()
            del self._containers[name]

    def close_all(self) -> None:
        """Close all containers."""
        for container in self._containers.values():
            container.close()
        self._containers.clear()

    def list_containers(self) -> list[str]:
        """List all container names."""
        return list(self._containers.keys())

    # Proxy common operations to default container
    def store(self, table: str, data: list[dict]) -> None:
        self.get().store(table, data)

    def load(self, table: str, query: dict | None = None) -> list[dict]:
        return self.get().load(table, query)

    def update(self, table: str, query: dict, data: dict) -> int:
        return self.get().update(table, query, data)

    def delete(self, table: str, query: dict) -> int:
        return self.get().delete(table, query)

    def exists(self, table: str) -> bool:
        return self.get().exists(table)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close_all()
