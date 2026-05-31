"""Schema analyzer."""

from typing import Any
from collections import Counter

from .type_detector import TypeDetector
from .optimizer import SchemaOptimizer


class SchemaAnalyzer:
    """Analyzes schema from data samples."""

    def __init__(self, sample_values_limit: int = 10):
        self.sample_values_limit = sample_values_limit

    def analyze(self, data: list[dict]) -> dict:
        """Analyze schema of data."""
        if not data:
            return {"fields": [], "statistics": {"total_records": 0}}

        fields = self._analyze_fields(data)
        statistics = self._analyze_statistics(data, fields)

        return {
            "fields": fields,
            "statistics": statistics,
        }

    def _analyze_fields(self, data: list[dict]) -> list[dict]:
        """Analyze each field in the data."""
        if not data:
            return []

        field_names = set()
        for record in data:
            field_names.update(record.keys())

        analyzed_fields = []
        for field_name in sorted(field_names):
            values = [record.get(field_name) for record in data]
            type_info = TypeDetector.infer_field_type(values)

            field_analysis = {
                "name": field_name,
                "nullable": type_info.get("nullable", True),
                "unique": self._is_unique(values),
                "cardinality": len(set(str(v) for v in values if v is not None)),
                "cardinality_ratio": self._calculate_cardinality_ratio(values),
            }

            field_analysis.update(type_info)

            # Sample values
            non_null = [v for v in values if v is not None]
            field_analysis["sample_values"] = non_null[:self.sample_values_limit]

            analyzed_fields.append(field_analysis)

        return analyzed_fields

    def _analyze_statistics(self, data: list[dict], fields: list[dict]) -> dict:
        """Calculate overall statistics."""
        total_records = len(data)
        total_fields = len(fields)

        missing_values = {}
        for field in fields:
            if field.get("nullable"):
                null_count = sum(1 for record in data if record.get(field["name"]) is None)
                if null_count > 0:
                    missing_values[field["name"]] = null_count

        duplicate_count = total_records - len({self._record_id(r) for r in data})

        return {
            "total_records": total_records,
            "total_fields": total_fields,
            "missing_values": missing_values,
            "duplicate_records": duplicate_count,
        }

    def _is_unique(self, values: list[Any]) -> bool:
        """Check if values are unique."""
        non_null = [v for v in values if v is not None]
        return len(non_null) == len(set(non_null))

    def _calculate_cardinality_ratio(self, values: list[Any]) -> float:
        """Calculate cardinality ratio."""
        non_null = [v for v in values if v is not None]
        if not non_null:
            return 0.0
        return len(set(non_null)) / len(non_null)

    def _record_id(self, record: dict) -> tuple:
        """Generate a tuple ID for a record for deduplication."""
        return tuple(sorted(record.items()))

    def optimize(self, schema_analysis: dict, target: str = "sqlite") -> dict:
        """Optimize schema for target database."""
        optimizer = SchemaOptimizer(target=target)
        return optimizer.optimize_schema(schema_analysis)

    def suggest_indexes(self, schema_analysis: dict) -> list[dict]:
        """Suggest indexes for the schema."""
        optimizer = SchemaOptimizer()
        return optimizer.suggest_indexes(schema_analysis)
