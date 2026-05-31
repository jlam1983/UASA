"""CSV file type adapter."""

from __future__ import annotations

import csv
from io import StringIO
from typing import Any

from .base import FileTypeAdapter


class CSVAdapter(FileTypeAdapter):
    """Adapter for CSV files."""

    def __init__(
        self,
        delimiter: str = ",",
        encoding: str = "utf-8",
        has_header: bool = True,
        skip_rows: int = 0,
        columns: list[str] | None = None,
 quotechar: str = '"',
        lineterminator: str = "\n",
    ):
        self.delimiter = delimiter
        self.encoding = encoding
        self.has_header = has_header
        self.skip_rows = skip_rows
        self.columns = columns
        self.quotechar = quotechar
        self.lineterminator = lineterminator

    def parse(self, source: str | bytes) -> list[dict]:
        if isinstance(source, str):
            source = source.encode(self.encoding)

        text = source.decode(self.encoding)
        reader = csv.reader(
            StringIO(text),
            delimiter=self.delimiter,
            quotechar=self.quotechar,
            lineterminator=self.lineterminator,
        )

        rows = list(reader)
        if not rows:
            return []

        header = (
            rows[self.skip_rows]
            if self.has_header
            else [f"col_{i}" for i in range(len(rows[0]))]
        )
        data_rows = rows[self.skip_rows + (1 if self.has_header else 0) :]

        return [dict(zip(header, row)) for row in data_rows]

    def serialize(self, data: list[dict], destination: str) -> None:
        if not data:
            return

        with open(destination, "w", newline="", encoding=self.encoding) as f:
            writer = csv.DictWriter(
                f,
                fieldnames=data[0].keys(),
                delimiter=self.delimiter,
                quotechar=self.quotechar,
                lineterminator=self.lineterminator,
            )
            writer.writeheader()
            writer.writerows(data)

    def get_schema(self) -> dict:
        return {
            "type": "csv",
            "delimiter": self.delimiter,
            "encoding": self.encoding,
            "has_header": self.has_header,
        }

    def validate(self, data: list[dict]) -> bool:
        if not data:
            return False
        return all(isinstance(record, dict) for record in data)
