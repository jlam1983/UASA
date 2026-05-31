"""Format detector for inconsistent formats."""

import re
from typing import Any


class FormatDetector:
    """Detects inconsistent formats in data."""

    DATE_PATTERNS = [
        (r"^\d{4}-\d{2}-\d{2}$", "YYYY-MM-DD"),
        (r"^\d{2}/\d{2}/\d{4}$", "MM/DD/YYYY"),
        (r"^\d{2}-\d{2}-\d{4}$", "DD-MM-YYYY"),
        (r"^\d{2}\.\d{2}\.\d{4}$", "DD.MM.YYYY"),
    ]

    PHONE_PATTERNS = [
        (r"^\d{3}-\d{3}-\d{4}$", "XXX-XXX-XXXX"),
        (r"^\(\d{3}\)\s*\d{3}-\d{4}$", "(XXX) XXX-XXXX"),
        (r"^\+\d{1,3}\s*\d{3}\s*\d{3}\s*\d{4}$", "+X XXX XXX XXXX"),
    ]

    def detect_inconsistent_formats(self, values: list[Any], pattern_type: str = "date") -> dict[int, str]:
        """Detect inconsistent formats in values."""
        formats_found = {}
        patterns = self.DATE_PATTERNS if pattern_type == "date" else self.PHONE_PATTERNS

        for i, value in enumerate(values):
            if value is None or value == "":
                continue

            value_str = str(value)
            for pattern, format_name in patterns:
                if re.match(pattern, value_str):
                    if format_name not in formats_found:
                        formats_found[i] = format_name
                    break
            else:
                # No pattern matched
                formats_found[i] = "unknown"

        return formats_found

    def detect_date_inconsistency(self, values: list[Any]) -> list[dict]:
        """Detect inconsistent date formats."""
        formats = self.detect_inconsistent_formats(values, "date")
        unique_formats = set(formats.values())

        if len(unique_formats) <= 1:
            return []

        inconsistent = []
        for idx, format_name in formats.items():
            if format_name == "unknown":
                inconsistent.append({
                    "record_index": idx,
                    "field": "date",
                    "value": values[idx],
                    "detected_format": "unknown",
                    "noise_type": "format_inconsistent"
                })

        return inconsistent

    def detect_field(self, records: list[dict], field: str) -> list[dict]:
        """Detect format inconsistencies in a field."""
        values = [record.get(field) for record in records]
        return self.detect_date_inconsistency(values)
