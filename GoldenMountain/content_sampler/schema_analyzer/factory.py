"""Data classification factory - routes JSON data through classification to appropriate handler."""

from .classifier import SchemaClassifier
from .handlers import (
    BaseHandler,
    CertainHandler,
    MixedHandler,
    AmbiguousHandler,
)


class DataClassificationFactory:
    """
    Central factory for data classification.
    Routes JSON data through detection → processing → output.

    Input: JSON
    Output: JSON (always)

    Usage:
        factory = DataClassificationFactory()
        result = factory.process(input_json)
    """

    def __init__(self):
        self.classifier = SchemaClassifier()
        self.handlers = {
            "certain": CertainHandler(),
            "mixed": MixedHandler(),
            "ambiguous": AmbiguousHandler()
        }

    def process(self, json_data: dict) -> dict:
        """
        Main entry point for data classification.

        Args:
            json_data: Input JSON data (dict with 'records' key or list of dicts)

        Returns:
            dict: JSON result with status, category, and data
                - Certain: {"status": "success", "category": "certain", "data": ...}
                - Mixed: {"status": "success", "category": "mixed", "data": ...}
                - Ambiguous: {"status": "rejected", "category": "ambiguous", "reason": "...", "data": None}
        """
        category = self.classifier.detect(json_data)

        handler = self.handlers.get(category)
        if handler:
            return handler.handle(json_data)

        # Fallback to ambiguous handler if something goes wrong
        return self.handlers["ambiguous"].handle(json_data)

    def classify(self, json_data: dict) -> dict:
        """
        Classify data without processing (returns classification info only).

        Args:
            json_data: Input JSON data

        Returns:
            dict: Classification report
        """
        category = self.classifier.detect(json_data)
        records = self._extract_records(json_data)

        # Count schema variants
        schema_variants = []
        if records:
            from collections import Counter
            field_sets = [frozenset(r.keys()) for r in records if isinstance(r, dict)]
            variant_counts = Counter(field_sets)
            schema_variants = [
                {"fields": list(fs), "count": count}
                for fs, count in variant_counts.most_common()
            ]

        return {
            "category": category,
            "confidence": self._calculate_confidence(category, schema_variants),
            "details": {
                "total_records_analyzed": len(records) if records else 0,
                "schema_variants": len(schema_variants),
                "variant_schemas": schema_variants
            }
        }

    def _extract_records(self, json_data: dict) -> list:
        if isinstance(json_data, dict) and "records" in json_data:
            return json_data["records"]
        elif isinstance(json_data, list):
            return json_data
        return []

    def _calculate_confidence(self, category: str, schema_variants: list) -> float:
        """Calculate confidence score for classification."""
        if category == "certain":
            return 1.0
        elif category == "ambiguous":
            return 0.3

        # Mixed: confidence based on how similar the schemas are
        if not schema_variants:
            return 0.5

        # Higher confidence if dominant schema has more records
        if schema_variants:
            dominant_ratio = schema_variants[0]["count"] / sum(v["count"] for v in schema_variants)
            return min(0.9, max(0.5, dominant_ratio))

        return 0.5