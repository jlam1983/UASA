"""Avro file type adapter."""

from __future__ import annotations

from io import BytesIO
from typing import Any

from .base import FileTypeAdapter


class AvroAdapter(FileTypeAdapter):
    """Adapter for Avro files."""

    def __init__(self, schema: dict | None = None):
        self.schema = schema

    def parse(self, source: str | bytes) -> list[dict]:
        import fastavro

        if isinstance(source, bytes):
            source = BytesIO(source)

        with open(source, "rb") as f:
            reader = fastavro.reader(f) if isinstance(source, str) else fastavro.reader(source)
            return [record for record in reader]

    def serialize(self, data: list[dict], destination: str) -> None:
        import fastavro

        with open(destination, "wb") as f:
            fastavro.writer(f, self.schema, data)

    def get_schema(self) -> dict:
        return {"type": "avro", "schema": self.schema}

    def validate(self, data: list[dict]) -> bool:
        if not data:
            return False
        return all(isinstance(record, dict) for record in data)
