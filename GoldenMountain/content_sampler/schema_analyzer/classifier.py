"""Schema classifier for detecting data category (certain/mixed/ambiguous)."""

from typing import Literal


class SchemaClassifier:
    """
    Classifies JSON data into certain/mixed/ambiguous categories.

    - certain: uniform schema across all records
    - mixed: similar but not identical schemas (reconcilable)
    - ambiguous: incompatible structure (reject)
    """

    def detect(self, json_data: dict) -> Literal["certain", "mixed", "ambiguous"]:
        """
        Detect the category of the input JSON data.

        Args:
            json_data: Input JSON data (dict with 'records' key or list of dicts)

        Returns:
            "certain", "mixed", or "ambiguous"
        """
        records = self._extract_records(json_data)

        if not records:
            return "ambiguous"

        if not self._is_list_of_dicts(records):
            return "ambiguous"

        # Analyze schema variants
        schema_variants = self._analyze_schema_variants(records)

        if len(schema_variants) == 1:
            return "certain"
        elif self._is_reconcilable(schema_variants):
            return "mixed"
        else:
            return "ambiguous"

    def _extract_records(self, json_data: dict) -> list:
        """Extract records from JSON data."""
        if isinstance(json_data, dict):
            if "records" in json_data:
                return json_data["records"]
            return [json_data]
        elif isinstance(json_data, list):
            return json_data
        return []

    def _is_list_of_dicts(self, records: list) -> bool:
        """Check if records is a list of dictionaries."""
        if not isinstance(records, list):
            return False
        return all(isinstance(r, dict) for r in records)

    def _analyze_schema_variants(self, records: list[dict]) -> list[set]:
        """Analyze schema variants across records. Returns list of field name sets."""
        return [set(record.keys()) for record in records]

    def _is_reconcilable(self, schema_variants: list[set]) -> bool:
        """
        Check if schema variants are reconcilable (mixed) or incompatible (ambiguous).

        Reconcilable means:
        - All schemas share some common fields
        - Differences are in optional/extra fields, not completely different structures
        """
        if not schema_variants:
            return False

        # Find intersection (common fields) and union (all fields)
        common_fields = schema_variants[0]
        all_fields = schema_variants[0]

        for variant in schema_variants[1:]:
            common_fields = common_fields.intersection(variant)
            all_fields = all_fields.union(variant)

        # Must have at least some common fields
        if not common_fields:
            return False

        # If all records share the exact same schema, it would be "certain" (caught earlier)
        # For mixed: schemas differ but share significant common ground
        # Calculate how much variation there is
        total_fields = len(all_fields)
        common_count = len(common_fields)

        # If common fields are less than half, likely ambiguous
        if total_fields > 0 and common_count / total_fields < 0.3:
            return False

        return True