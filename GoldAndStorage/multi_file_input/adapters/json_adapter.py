"""JSON file type adapter."""

import json
from typing import Any

from .base import FileTypeAdapter


class JSONAdapter(FileTypeAdapter):
    """Adapter for JSON files."""

    def __init__(self, encoding: str = "utf-8", lines: bool = False):
        self.encoding = encoding
        self.lines = lines

    def parse(self, source: str | bytes | list | dict) -> list[dict]:
        # Handle already-parsed data (e.g., from API channels)
        if isinstance(source, list):
            return source
        if isinstance(source, dict):
            return [source]

        if isinstance(source, str):
            source = source.encode(self.encoding)

        text = source.decode(self.encoding)

        if self.lines:
            return [
                json.loads(line)
                for line in text.strip().splitlines()
                if line.strip()
            ]
        else:
            data = json.loads(text)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                for key in ["data", "records", "items", "results", "rows"]:
                    if key in data and isinstance(data[key], list):
                        return data[key]
                return [data]
            return []

    def serialize(self, data: list[dict], destination: str) -> None:
        with open(destination, "w", encoding=self.encoding) as f:
            if self.lines:
                for record in data:
                    f.write(json.dumps(record) + "\n")
            else:
                json.dump({"records": data}, f, indent=2, ensure_ascii=False)

    def get_schema(self) -> dict:
        return {"type": "json", "lines": self.lines, "encoding": self.encoding}

    def validate(self, data: list[dict]) -> bool:
        if not data:
            return False
        return all(isinstance(record, dict) for record in data)
