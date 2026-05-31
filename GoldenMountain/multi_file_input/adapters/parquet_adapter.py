"""Parquet file type adapter."""

from io import BytesIO
from typing import Any

from .base import FileTypeAdapter


class ParquetAdapter(FileTypeAdapter):
    """Adapter for Parquet files."""

    def __init__(self):
        pass

    def parse(self, source: str | bytes) -> list[dict]:
        import pyarrow.parquet as pq

        if isinstance(source, bytes):
            source = BytesIO(source)

        table = pq.read_table(source)
        df = table.to_pandas()
        return df.to_dict(orient="records")

    def serialize(self, data: list[dict], destination: str) -> None:
        import pyarrow.parquet as pq
        import pandas as pd

        df = pd.DataFrame(data)
        table = pyarrow.Table.from_pandas(df)
        pq.write_table(table, destination)

    def get_schema(self) -> dict:
        return {"type": "parquet"}

    def validate(self, data: list[dict]) -> bool:
        if not data:
            return False
        return all(isinstance(record, dict) for record in data)
