"""YAML file type adapter."""

from typing import Any

from .base import FileTypeAdapter


class YAMLAdapter(FileTypeAdapter):
    """Adapter for YAML files."""

    def __init__(self, encoding: str = "utf-8"):
        self.encoding = encoding

    def parse(self, source: str | bytes) -> list[dict]:
        import yaml

        if isinstance(source, str):
            source = source.encode(self.encoding)

        data = yaml.safe_load(source)

        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            for key in ["data", "records", "items", "results"]:
                if key in data and isinstance(data[key], list):
                    return data[key]
            return [data]
        return []

    def serialize(self, data: list[dict], destination: str) -> None:
        import yaml

        with open(destination, "w", encoding=self.encoding) as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

    def get_schema(self) -> dict:
        return {"type": "yaml", "encoding": self.encoding}

    def validate(self, data: list[dict]) -> bool:
        if not data:
            return False
        return all(isinstance(record, dict) for record in data)
