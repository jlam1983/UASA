"""Excel file type adapter."""

from __future__ import annotations

from io import BytesIO
from typing import Any

from .base import FileTypeAdapter


class ExcelAdapter(FileTypeAdapter):
    """Adapter for Excel files (.xlsx, .xls)."""

    def __init__(
        self,
        sheet: int | str = 0,
        has_header: bool = True,
        skip_rows: int = 0,
        columns: list[str] | None = None,
    ):
        self.sheet = sheet
        self.has_header = has_header
        self.skip_rows = skip_rows
        self.columns = columns

    def parse(self, source: str | bytes) -> list[dict]:
        import openpyxl

        wb = openpyxl.load_workbook(
            BytesIO(source) if isinstance(source, bytes) else source
        )
        ws = (
            wb[self.sheet]
            if isinstance(self.sheet, str)
            else wb.worksheets[self.sheet]
        )

        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return []

        header = (
            rows[self.skip_rows]
            if self.has_header
            else [f"col_{i}" for i in range(len(rows[0]))]
        )
        data_rows = rows[self.skip_rows + (1 if self.has_header else 0) :]

        return [dict(zip(header, row)) for row in data_rows]

    def get_sheets(self, source: str | bytes) -> list[str]:
        import openpyxl

        wb = openpyxl.load_workbook(
            BytesIO(source) if isinstance(source, bytes) else source
        )
        return wb.sheetnames

    def serialize(self, data: list[dict], destination: str) -> None:
        import openpyxl
        from openpyxl.workbook import Workbook

        wb = Workbook()
        ws = wb.active

        if data:
            ws.append(list(data[0].keys()))
            for record in data:
                ws.append(list(record.values()))

        wb.save(destination)

    def get_schema(self) -> dict:
        return {
            "type": "excel",
            "sheet": self.sheet,
            "has_header": self.has_header,
        }

    def validate(self, data: list[dict]) -> bool:
        if not data:
            return False
        return all(isinstance(record, dict) for record in data)
