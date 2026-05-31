"""Duplicate detector."""

from typing import Any


class DuplicateDetector:
    """Detects duplicate records."""

    def detect_exact_duplicates(self, records: list[dict]) -> list[int]:
        """Detect exact duplicate records. Returns indices of duplicate records."""
        seen = {}
        duplicate_indices = []

        for i, record in enumerate(records):
            record_key = self._make_key(record)
            if record_key in seen:
                duplicate_indices.append(i)
            else:
                seen[record_key] = i

        return duplicate_indices

    def detect_near_duplicates(self, records: list[dict], key_fields: list[str] = None) -> list[int]:
        """Detect near duplicates based on key fields."""
        seen = {}
        duplicate_indices = []

        for i, record in enumerate(records):
            if key_fields:
                key_values = tuple(record.get(f) for f in key_fields)
            else:
                key_values = self._make_key(record)

            if key_values in seen:
                duplicate_indices.append(i)
            else:
                seen[key_values] = i

        return duplicate_indices

    def _make_key(self, record: dict) -> tuple:
        """Create a hashable key from a record."""
        return tuple(sorted(record.items()))

    def detect_field(self, records: list[dict], field: str) -> list[dict]:
        """Detect duplicate values in a specific field."""
        values = [record.get(field) for record in records]
        seen = {}
        duplicate_indices = []

        for i, value in enumerate(values):
            if value is not None:
                if value in seen:
                    duplicate_indices.append(i)
                else:
                    seen[value] = i

        return [
            {
                "record_index": idx,
                "field": field,
                "value": values[idx],
                "noise_type": "duplicate"
            }
            for idx in duplicate_indices
        ]
