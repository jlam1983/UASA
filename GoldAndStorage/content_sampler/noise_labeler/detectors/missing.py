"""Missing value detector."""

from typing import Any


class MissingValueDetector:
    """Detects missing values in data."""

    def detect(self, value: Any) -> bool:
        """Check if value is missing."""
        if value is None:
            return True
        if value == "":
            return True
        if isinstance(value, list) and len(value) == 0:
            return True
        if isinstance(value, str) and value.strip() == "":
            return True
        return False

    def detect_field(self, records: list[dict], field: str) -> list[dict]:
        """Detect missing values in a specific field across records."""
        noisy_records = []
        for i, record in enumerate(records):
            value = record.get(field)
            if self.detect(value):
                noisy_records.append({
                    "record_index": i,
                    "field": field,
                    "value": value,
                    "noise_type": "missing_value"
                })
        return noisy_records
