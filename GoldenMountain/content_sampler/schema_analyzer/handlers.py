"""Handlers for different data classification categories."""

from abc import ABC, abstractmethod
from typing import Any


class BaseHandler(ABC):
    """Base handler interface — all handlers must implement this."""

    @abstractmethod
    def handle(self, json_data: dict) -> dict:
        """
        Process JSON data and return result as JSON.

        Args:
            json_data: Input JSON data

        Returns:
            JSON dict with status, category, and data/error info
        """
        raise NotImplementedError


class CertainHandler(BaseHandler):
    """
    Handler for certain data.
    - No transformation needed, pass through unchanged
    """

    def handle(self, json_data: dict) -> dict:
        """Certain data — no processing needed, pass through."""
        return {
            "status": "success",
            "category": "certain",
            "data": json_data
        }


class MixedHandler(BaseHandler):
    """
    Handler for mixed data.
    - Normalize schema differences
    - Transform to a unified schema
    - Merge optional fields
    """

    def __init__(self):
        self.normalizers = [
            SchemaNormalizer(),
            TypeConverter(),
            FieldMerger(),
            FormatStandardizer()
        ]

    def handle(self, json_data: dict) -> dict:
        """Mixed data — normalize and transform."""
        result = json_data

        for normalizer in self.normalizers:
            result = normalizer.normalize(result)

        return {
            "status": "success",
            "category": "mixed",
            "data": result
        }


class AmbiguousHandler(BaseHandler):
    """
    Handler for ambiguous data.
    - Reject and return error JSON
    """

    def handle(self, json_data: dict) -> dict:
        """Ambiguous data — reject with error JSON."""
        return {
            "status": "rejected",
            "category": "ambiguous",
            "reason": "Data structure is incompatible",
            "data": None
        }


# Normalizer implementations for Mixed data handling

class SchemaNormalizer:
    """Normalize schema by ensuring consistent field structure."""

    def normalize(self, json_data: dict) -> dict:
        """Ensure all records have consistent schema."""
        records = self._extract_records(json_data)
        if not records:
            return json_data

        # Find the dominant schema (most common field combination)
        field_sets = [tuple(sorted(set(r.keys()))) for r in records]
        from collections import Counter
        most_common = Counter(field_sets).most_common(1)[0][0]
        dominant_fields = set(most_common)

        # Normalize all records to have the dominant fields
        normalized_records = []
        for record in records:
            normalized = {}
            for field in dominant_fields:
                normalized[field] = record.get(field)
            normalized_records.append(normalized)

        return {"records": normalized_records}

    def _extract_records(self, json_data: dict) -> list:
        if isinstance(json_data, dict) and "records" in json_data:
            return json_data["records"]
        elif isinstance(json_data, list):
            return json_data
        return []


class TypeConverter:
    """Convert field types to a consistent format."""

    def normalize(self, json_data: dict) -> dict:
        """Convert type inconsistencies in records."""
        records = self._extract_records(json_data)
        if not records:
            return json_data

        # Detect type issues and convert
        for record in records:
            for key, value in record.items():
                if value is None:
                    continue
                # Convert string numbers to actual numbers
                if isinstance(value, str) and value.isdigit():
                    record[key] = int(value)
                elif isinstance(value, str) and self._is_float(value):
                    record[key] = float(value)

        return json_data

    def _extract_records(self, json_data: dict) -> list:
        if isinstance(json_data, dict) and "records" in json_data:
            return json_data["records"]
        elif isinstance(json_data, list):
            return json_data
        return []

    def _is_float(self, s: str) -> bool:
        try:
            float(s)
            return "." in s
        except ValueError:
            return False


class FieldMerger:
    """Merge optional fields that appear in some records but not others."""

    def normalize(self, json_data: dict) -> dict:
        """Merge schema variants into unified structure."""
        records = self._extract_records(json_data)
        if not records:
            return json_data

        # All records already normalized to dominant schema by SchemaNormalizer
        # This step could be enhanced to handle field merging logic
        return json_data

    def _extract_records(self, json_data: dict) -> list:
        if isinstance(json_data, dict) and "records" in json_data:
            return json_data["records"]
        elif isinstance(json_data, list):
            return json_data
        return []


class FormatStandardizer:
    """Standardize format inconsistencies like date formats."""

    def normalize(self, json_data: dict) -> dict:
        """Standardize format inconsistencies."""
        # Placeholder for format standardization logic
        # Could handle date format normalization, etc.
        return json_data

    def _extract_records(self, json_data: dict) -> list:
        if isinstance(json_data, dict) and "records" in json_data:
            return json_data["records"]
        elif isinstance(json_data, list):
            return json_data
        return []