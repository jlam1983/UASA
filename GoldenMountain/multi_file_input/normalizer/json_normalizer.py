"""JSON normalizer.

Outputs single JSON format with data_category detection:
- flatten: single-table structure (CSV, simple JSON, Excel sheet)
- complex: multi-level/hierarchical data (nested JSON, XML, multi-sheet)
"""

from __future__ import annotations

import re
import hashlib
import json
from datetime import datetime
from typing import Any

from ..exceptions import NormalizationError


class JSONNormalizer:
    """Normalizes all data formats to standard JSON structure."""

    def __init__(self, include_raw: bool = False, generate_ids: bool = True):
        self.include_raw = include_raw
        self.generate_ids = generate_ids

    def normalize(
        self,
        data: list[dict],
        source_type: str,
        source_channel: str,
        source_path: str | None = None,
    ) -> dict:
        """Convert parsed data to normalized JSON.

        Args:
            data: List of parsed record dicts
            source_type: Type of source (csv, json, xml, etc.)
            source_channel: Channel used (file, api, stream, database, iot)
            source_path: Source path or URL

        Returns:
            Normalized JSON with metadata and records
        """
        if not data:
            return {
                "metadata": {
                    "source_type": source_type,
                    "source_channel": source_channel,
                    "source_path": source_path,
                    "record_count": 0,
                    "columns": [],
                    "parsed_at": datetime.utcnow().isoformat() + "Z",
                    "schema_hash": "",
                    "data_category": "flatten",
                },
                "records": [],
            }

        columns = list(data[0].keys()) if isinstance(data[0], dict) else []
        data_category = self._detect_category(data)

        normalized = {
            "metadata": {
                "source_type": source_type,
                "source_channel": source_channel,
                "source_path": source_path,
                "record_count": len(data),
                "columns": columns,
                "parsed_at": datetime.utcnow().isoformat() + "Z",
                "schema_hash": self._hash_columns(columns),
                "data_category": data_category,
            },
            "records": [],
        }

        for i, record in enumerate(data):
            if not isinstance(record, dict):
                record = {"_value": record}

            normalized_record = {
                "_id": self._generate_id(source_path, i) if self.generate_ids else str(i),
                "_source": self._normalize_keys(record),
            }

            if self.include_raw:
                normalized_record["_raw"] = record

            normalized["records"].append(normalized_record)

        return normalized

    def _detect_category(self, data: list[dict]) -> str:
        """Detect if data is flatten or complex.

        Flatten: single-table structure, no nested dicts/lists of dicts
        Complex: hierarchical data with nested structures that need flattening

        Args:
            data: List of records

        Returns:
            "flatten" or "complex"
        """
        if not data:
            return "flatten"

        first = data[0]
        for value in first.values():
            if isinstance(value, list) and value and isinstance(value[0], dict):
                return "complex"
            if isinstance(value, dict):
                return "complex"
        return "flatten"

    def _normalize_keys(self, record: dict) -> dict:
        """Normalize dictionary keys (snake_case, remove special chars)."""
        result = {}
        for key, value in record.items():
            # Convert camelCase to snake_case
            normalized_key = re.sub(r'([A-Z]+)', r'_\1', key)
            normalized_key = normalized_key.lower()
            normalized_key = re.sub(r"[\W]+", "_", normalized_key)
            normalized_key = re.sub(r"_+", "_", normalized_key).strip("_")

            if isinstance(value, dict):
                result[normalized_key] = self._normalize_keys(value)
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                result[normalized_key] = [self._normalize_keys(v) for v in value]
            else:
                result[normalized_key] = value
        return result

    def _generate_id(self, source: str | None, index: int) -> str:
        """Generate unique record ID."""
        prefix = hashlib.md5(str(source or "").encode()).hexdigest()[:8]
        return f"{prefix}_{index}"

    def _hash_columns(self, columns: list[str]) -> str:
        """Generate schema hash for change detection."""
        col_str = ",".join(sorted(columns))
        return hashlib.md5(col_str.encode()).hexdigest()[:12]

    def denormalize(self, normalized: dict) -> list[dict]:
        """Convert normalized JSON back to list of dicts."""
        return [record["_source"] for record in normalized.get("records", [])]

    def merge(self, normalized_list: list[dict]) -> dict:
        """Merge multiple normalized datasets."""
        all_records = []
        all_columns = set()
        merged_metadata = {
            "source_type": "merged",
            "source_channel": "multiple",
            "record_count": 0,
            "columns": [],
            "parsed_at": datetime.utcnow().isoformat() + "Z",
            "data_category": "flatten",
        }

        for norm in normalized_list:
            all_records.extend(norm.get("records", []))
            all_columns.update(norm.get("metadata", {}).get("columns", []))

        merged_metadata["record_count"] = len(all_records)
        merged_metadata["columns"] = sorted(all_columns)
        merged_metadata["schema_hash"] = self._hash_columns(merged_metadata["columns"])

        return {
            "metadata": merged_metadata,
            "records": all_records,
        }
