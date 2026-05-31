"""Test cases for ValueAddManager and value_add_layer components."""

import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from value_add_layer import ValueAddManager, ProcessingResult
from value_add_layer.enricher.rules import (
    CalculateRule, CategoryMapRule, LookupRule, ConditionalRule
)
from value_add_layer.validator.rules import RequiredRule, RangeRule, TypeRule, EnumRule
from value_add_layer.validator.validator import DataValidator
from value_add_layer.aggregator.aggregator import DataAggregator


class TestValueAddManager:
    """Test ValueAddManager JSON I/O processing."""

    def test_process_with_enrichment(self):
        """Test enrichment via JSON config."""
        manager = ValueAddManager()

        input_data = {
            "records": [
                {"id": 1, "price": 100, "quantity": 2},
                {"id": 2, "price": 50, "quantity": 3}
            ],
            "config": {
                "enrichment": [
                    {"type": "calculate", "target": "total", "expression": "price * quantity"}
                ]
            }
        }

        result = manager.process(input_data)

        assert result["metadata"]["source"] == "value_add_layer"
        assert "enrichment" in result["metadata"]["steps_completed"]
        assert result["records"][0]["total"] == 200
        assert result["records"][1]["total"] == 150

    def test_process_with_category_map(self):
        """Test category_map enrichment rule."""
        manager = ValueAddManager()

        input_data = {
            "records": [
                {"id": 1, "age": 25},
                {"id": 2, "age": 55},
                {"id": 3, "age": 75}
            ],
            "config": {
                "enrichment": [
                    {"type": "category_map", "target": "age_group", "source": "age",
                     "ranges": [[0, 18], [19, 35], [36, 55], [56, 150]],
                     "labels": ["minor", "young_adult", "adult", "senior"]}
                ]
            }
        }

        result = manager.process(input_data)

        assert result["records"][0]["age_group"] == "young_adult"
        assert result["records"][1]["age_group"] == "adult"
        assert result["records"][2]["age_group"] == "senior"

    def test_process_with_validation(self):
        """Test validation via JSON config."""
        manager = ValueAddManager()

        input_data = {
            "records": [
                {"id": 1, "price": 100},
                {"id": 2, "price": -10}  # Invalid: negative price
            ],
            "config": {
                "validation": [
                    {"type": "required", "field": "id"},
                    {"type": "range", "field": "price", "min": 0}
                ]
            }
        }

        result = manager.process(input_data)

        assert "validation" in result
        assert result["validation"]["valid"] is False
        assert result["validation"]["error_count"] >= 1

    def test_process_with_aggregation(self):
        """Test aggregation via JSON config."""
        manager = ValueAddManager()

        input_data = {
            "records": [
                {"category": "A", "value": 100},
                {"category": "A", "value": 200},
                {"category": "B", "value": 150}
            ],
            "config": {
                "enrichment": [
                    {"type": "calculate", "target": "total", "expression": "value"}
                ],
                "aggregation": {
                    "group_by": ["category"],
                    "aggregations": {
                        "sum_value": "sum,total",
                        "count": "count"
                    }
                }
            }
        }

        result = manager.process(input_data)

        assert "aggregation" in result["metadata"]["steps_completed"]
        assert len(result["records"]) == 2  # 2 groups

    def test_process_empty_records(self):
        """Test with empty records list."""
        manager = ValueAddManager()

        input_data = {
            "records": [],
            "config": {}
        }

        result = manager.process(input_data)

        assert result["metadata"]["record_count"] == 0
        assert result["records"] == []

    def test_process_no_config(self):
        """Test with no config (passthrough)."""
        manager = ValueAddManager()

        input_data = {
            "records": [{"id": 1, "name": "test"}]
        }

        result = manager.process(input_data)

        assert result["metadata"]["record_count"] == 1
        assert result["records"][0]["name"] == "test"

    def test_output_json_format(self):
        """Test output is valid JSON-serializable."""
        manager = ValueAddManager()

        input_data = {
            "records": [{"id": 1, "price": 100}],
            "config": {}
        }

        result = manager.process(input_data)

        # Should not raise
        json_str = json.dumps(result)
        parsed = json.loads(json_str)

        assert "metadata" in parsed
        assert "records" in parsed
        assert "processed_at" in parsed["metadata"]


class TestProcessingResult:
    """Test ProcessingResult class."""

    def test_to_json_with_validation(self):
        """Test to_json includes validation info."""
        result = ProcessingResult()
        result.records = [{"id": 1}]
        result.steps_completed = ["enrichment"]
        result.validation = None

        json_output = result.to_json()

        assert "metadata" in json_output
        assert "records" in json_output
        assert json_output["metadata"]["record_count"] == 1

    def test_to_json_without_validation(self):
        """Test to_json works without validation."""
        result = ProcessingResult()
        result.records = [{"id": 1}]
        result.steps_completed = []

        json_output = result.to_json()

        assert "validation" not in json_output


class TestEnrichmentRules:
    """Test enrichment rule classes."""

    def test_calculate_rule(self):
        """Test CalculateRule."""
        rule = CalculateRule("total", "price * quantity")
        record = {"price": 100, "quantity": 2}

        result = rule.compute(record)

        assert result == 200

    def test_category_map_rule(self):
        """Test CategoryMapRule."""
        rule = CategoryMapRule(
            "age_group", "age",
            [[0, 18], [18, 35], [35, 55], [55, 150]],
            ["minor", "young_adult", "adult", "senior"]
        )

        assert rule.compute({"age": 10}) == "minor"
        assert rule.compute({"age": 25}) == "young_adult"
        assert rule.compute({"age": 45}) == "adult"
        assert rule.compute({"age": 70}) == "senior"
        assert rule.compute({"age": None}) is None

    def test_conditional_rule(self):
        """Test ConditionalRule."""
        rule = ConditionalRule("tier", "price > 100", "premium", "standard")

        assert rule.compute({"price": 150}) == "premium"
        assert rule.compute({"price": 50}) == "standard"


class TestValidator:
    """Test DataValidator."""

    def test_required_rule(self):
        """Test RequiredRule."""
        validator = DataValidator([RequiredRule("name")])

        # Valid record
        result = validator.validate([{"name": "test"}])
        assert result.is_valid is True

        # Missing field
        result = validator.validate([{"id": 1}])
        assert result.is_valid is False

    def test_range_rule(self):
        """Test RangeRule."""
        validator = DataValidator([RangeRule("price", min_val=0, max_val=1000)])

        # Valid
        result = validator.validate([{"price": 500}])
        assert result.is_valid is True

        # Below min
        result = validator.validate([{"price": -10}])
        assert result.is_valid is False

        # Above max
        result = validator.validate([{"price": 2000}])
        assert result.is_valid is False

    def test_enum_rule(self):
        """Test EnumRule."""
        validator = DataValidator([EnumRule("status", ["active", "pending"])])

        # Valid
        result = validator.validate([{"status": "active"}])
        assert result.is_valid is True

        # Invalid
        result = validator.validate([{"status": "unknown"}])
        assert result.is_valid is False


class TestAggregator:
    """Test DataAggregator."""

    def test_aggregate_sum(self):
        """Test sum aggregation."""
        aggregator = DataAggregator()

        records = [
            {"category": "A", "value": 100},
            {"category": "A", "value": 200},
            {"category": "B", "value": 150}
        ]

        result = aggregator.aggregate(records, ["category"], {"total": "sum,value"})

        assert len(result) == 2
        # Find category A
        cat_a = next(r for r in result if r["category"] == "A")
        assert cat_a["total"] == 300

    def test_aggregate_count(self):
        """Test count aggregation."""
        aggregator = DataAggregator()

        records = [
            {"category": "A", "value": 100},
            {"category": "A", "value": 200},
            {"category": "B", "value": 150}
        ]

        result = aggregator.aggregate(records, ["category"], {"count": "count"})

        cat_a = next(r for r in result if r["category"] == "A")
        assert cat_a["count"] == 2


class TestManagerUtilities:
    """Test ValueAddManager utility methods."""

    def test_normalize_fields(self):
        """Test normalize_fields utility."""
        manager = ValueAddManager()

        records = [
            {"id": 1, "price": 0},
            {"id": 2, "price": 50},
            {"id": 3, "price": 100}
        ]

        result = manager.normalize_fields(records, ["price"], method="min_max")

        # Check that normalized values are added
        assert any("price_normalized" in r for r in result)

    def test_encode_categorical(self):
        """Test encode_categorical utility."""
        manager = ValueAddManager()

        records = [
            {"id": 1, "status": "active"},
            {"id": 2, "status": "pending"},
            {"id": 3, "status": "active"}
        ]

        result = manager.encode_categorical(records, "status", method="label")

        # Check that encoded field is added
        assert any("status_encoded" in r for r in result)


def run_tests():
    """Run all tests and print results."""
    test_classes = [
        TestValueAddManager,
        TestProcessingResult,
        TestEnrichmentRules,
        TestValidator,
        TestAggregator,
        TestManagerUtilities,
    ]

    total = 0
    passed = 0
    failed = []

    for test_class in test_classes:
        print(f"\n{'='*50}")
        print(f"Running {test_class.__name__}")
        print('='*50)

        instance = test_class()
        for method_name in dir(instance):
            if method_name.startswith("test_"):
                total += 1
                try:
                    getattr(instance, method_name)()
                    print(f"  ✓ {method_name}")
                    passed += 1
                except Exception as e:
                    print(f"  ✗ {method_name}: {e}")
                    failed.append(f"{test_class.__name__}.{method_name}")

    print(f"\n{'='*50}")
    print(f"Results: {passed}/{total} passed")
    print('='*50)

    if failed:
        print("\nFailed tests:")
        for f in failed:
            print(f"  - {f}")

    return passed == total


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)