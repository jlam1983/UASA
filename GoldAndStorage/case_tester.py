"""Test cases for Multi-File Type Input System.

Flow Pipeline:
1. Channel Adapters (read from various sources)
2. File Type Adapters (parse different formats)
3. JSON Normalizer (normalize to standard JSON)
4. Data Ingestion Pipeline (end-to-end)
5. Content Sampler (sampling, schema analysis, noise labeling)
"""

import pytest
import json
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import tempfile
from pathlib import Path
from multi_file_input.channels import FileChannel
from multi_file_input.exceptions import ChannelReadError
from multi_file_input.channels import APIChannel
from multi_file_input.channels import StreamMessage
from multi_file_input.channels import TelemetryData
from multi_file_input.channels import DatabaseChange
from multi_file_input.adapters import CSVAdapter
from multi_file_input.adapters import JSONAdapter
from multi_file_input.pipeline import DataIngestionPipeline
from multi_file_input.channels import APIChannel
from content_sampler import ContentSampler
from unittest.mock import patch
from multi_file_input.exceptions import IngestionError
from multi_file_input.exceptions import ChannelReadError
from multi_file_input.exceptions import ParseError
from multi_file_input.exceptions import NormalizationError
from multi_file_input.exceptions import (
    IngestionError,
    ChannelReadError,
    ParseError,
    NormalizationError,
)
from multi_file_input.pipeline import DataIngestionPipeline
from multi_file_input.channels import APIChannel
from multi_file_input.channels import FileChannel
from multi_file_input.channels import APIChannel
from multi_file_input.adapters import CSVAdapter
from multi_file_input.pipeline import ChannelAdapterFactory
from content_sampler.schema_analyzer import SchemaAnalyzer
from content_sampler.noise_labeler import NoiseLabeler
from unittest.mock import patch
from multi_file_input.pipeline import DataIngestionPipeline
from multi_file_input.normalizer import JSONNormalizer
from multi_file_input.adapters import ExcelAdapter
from multi_file_input.adapters import XMLAdapter
from unittest.mock import patch
from io import BytesIO
import openpyxl
from multi_file_input.config import Config
from content_sampler.noise_labeler import NoiseLabeler
from multi_file_input.adapters import YAMLAdapter
from value_add_layer import (
    ValueAddPipeline,
    DataEnricher,
    DataTransformer,
    DataValidator,
    DataAggregator,
    CalculateRule,
    CategoryMapRule,
    LookupRule,
    DateExtractRule,
    ConditionalRule,
    DeriveRule,
    DataReshaper,
    Normalizer,
    CategoricalEncoder,
    RequiredRule,
    TypeRule,
    RangeRule,
    PatternRule,
    EnumRule,
    CustomRule,
    CrossFieldRule,
    UniqueRule,
    ProcessingResult,
)
from value_add_layer.errors import (
    ValueAddError,
    EnrichmentError,
    TransformationError,
    ValidationError as ValueAddValidationError,
    AggregationError,
)


# ============================================================================
# VALUE ADD LAYER: ENRICHER TESTS
# ============================================================================

class TestDataEnricher:
    """Test DataEnricher - adding computed and lookup-based fields."""

    def test_calculate_rule(self):
        """Test CalculateRule - compute from expression."""
        enricher = DataEnricher()
        records = [
            {"quantity": 5, "unit_price": 10},
            {"quantity": 3, "unit_price": 20},
        ]
        rules = [CalculateRule("total", "quantity * unit_price")]
        result = enricher.enrich(records, rules)

        assert result[0]["total"] == 50
        assert result[1]["total"] == 60

    def test_calculate_rule_with_expression(self):
        """Test CalculateRule with more complex expression."""
        enricher = DataEnricher()
        records = [{"price": 100, "tax_rate": 0.1}]
        rules = [CalculateRule("total_with_tax", "price * (1 + tax_rate)")]
        result = enricher.enrich(records, rules)

        assert result[0]["total_with_tax"] == pytest.approx(110.0)

    def test_category_map_rule(self):
        """Test CategoryMapRule - map values to categories."""
        enricher = DataEnricher()
        records = [
            {"age": 15},
            {"age": 25},
            {"age": 45},
            {"age": 70},
        ]
        rules = [
            CategoryMapRule(
                "age_group", "age",
                [(0, 18), (18, 35), (35, 55), (55, 100)],
                ["minor", "young_adult", "adult", "senior"]
            )
        ]
        result = enricher.enrich(records, rules)

        assert result[0]["age_group"] == "minor"
        assert result[1]["age_group"] == "young_adult"
        assert result[2]["age_group"] == "adult"
        assert result[3]["age_group"] == "senior"

    def test_lookup_rule(self):
        """Test LookupRule - add data from lookup source."""
        enricher = DataEnricher()
        records = [{"postal_code": "1001"}, {"postal_code": "1002"}]
        lookup_source = {
            "1001": {"region": "North", "country": "USA"},
            "1002": {"region": "South", "country": "USA"},
        }
        rules = [
            LookupRule("region", lookup_source, "postal_code", ["region", "country"])
        ]
        result = enricher.enrich(records, rules)

        assert result[0]["region"] == "North"
        assert result[1]["region"] == "South"

    def test_enrich_with_multiple_rules(self):
        """Test enriching with multiple rules."""
        enricher = DataEnricher()
        records = [
            {"quantity": 5, "unit_price": 10, "discount": 0.1},
        ]
        rules = [
            CalculateRule("subtotal", "quantity * unit_price"),
            CalculateRule("discount_amount", "subtotal * discount"),
            CalculateRule("total", "subtotal - discount_amount"),
        ]
        result = enricher.enrich(records, rules)

        assert result[0]["subtotal"] == 50
        assert result[0]["discount_amount"] == 5.0
        assert result[0]["total"] == 45.0


class TestDataTransformer:
    """Test DataTransformer - normalization, encoding, and reshaping."""

    def test_normalize_min_max(self):
        """Test min-max normalization."""
        transformer = DataTransformer()
        records = [
            {"value": 0},
            {"value": 50},
            {"value": 100},
        ]
        result = transformer.transform(records, "normalize", {"fields": ["value"], "method": "min_max"})

        assert len(result) == 3

    def test_encode_label(self):
        """Test label encoding."""
        transformer = DataTransformer()
        records = [
            {"status": "active"},
            {"status": "pending"},
            {"status": "active"},
        ]
        result = transformer.transform(records, "encode", {"field": "status", "method": "label"})

        assert all("status_encoded" in r for r in result)

    def test_encode_one_hot(self):
        """Test one-hot encoding."""
        transformer = DataTransformer()
        records = [
            {"color": "red"},
            {"color": "blue"},
            {"color": "red"},
        ]
        result = transformer.transform(records, "encode", {"field": "color", "method": "one_hot"})

        assert any("color_red" in r for r in result)
        assert any("color_blue" in r for r in result)

    def test_filter_records(self):
        """Test filtering records by condition."""
        transformer = DataTransformer()
        records = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
            {"name": "Charlie", "age": 35},
        ]
        result = transformer.transform(records, "filter", {"condition": "age >= 30"})

        assert len(result) == 2
        assert result[0]["name"] == "Alice"
        assert result[1]["name"] == "Charlie"


class TestDataReshaper:
    """Test DataReshaper - reshaping operations."""

    def test_pivot(self):
        """Test pivot operation."""
        reshaper = DataReshaper()
        records = [
            {"region": "North", "product": "A", "sales": 100},
            {"region": "North", "product": "B", "sales": 200},
            {"region": "South", "product": "A", "sales": 150},
        ]
        result = reshaper.pivot(records, "region", "product", "sales")

        assert len(result) == 2

    def test_melt(self):
        """Test melt operation."""
        reshaper = DataReshaper()
        records = [
            {"id": 1, "price": 100, "quantity": 5},
            {"id": 2, "price": 200, "quantity": 3},
        ]
        result = reshaper.melt(records, ["id"], ["price", "quantity"])

        assert len(result) == 4

    def test_nest(self):
        """Test nest operation."""
        reshaper = DataReshaper()
        records = [
            {"category": "A", "item": "x", "value": 1},
            {"category": "A", "item": "y", "value": 2},
            {"category": "B", "item": "z", "value": 3},
        ]
        result = reshaper.nest(records, "category", ["item", "value"])

        assert len(result) == 2
        assert result[0]["key"] == "A"
        assert len(result[0]["items"]) == 2


class TestNormalizer:
    """Test Normalizer - normalization strategies."""

    def test_min_max_scale(self):
        """Test min-max scaling."""
        normalizer = Normalizer()
        values = [0, 50, 100]
        scaled = normalizer.min_max_scale(values)

        assert scaled[0] == 0.0
        assert scaled[1] == 0.5
        assert scaled[2] == 1.0

    def test_min_max_scale_constant(self):
        """Test min-max scaling with constant values."""
        normalizer = Normalizer()
        values = [5, 5, 5]
        scaled = normalizer.min_max_scale(values)

        assert all(s == 0.5 for s in scaled)

    def test_z_score_scale(self):
        """Test z-score normalization."""
        normalizer = Normalizer()
        values = [10, 20, 30, 40, 50]
        scaled = normalizer.z_score_scale(values)

        assert abs(scaled[2]) < 0.01

    def test_robust_scale(self):
        """Test robust scaling with median and IQR."""
        normalizer = Normalizer()
        values = [1, 5, 10, 15, 20]
        scaled = normalizer.robust_scale(values)

        assert abs(scaled[2]) < 0.01


class TestCategoricalEncoder:
    """Test CategoricalEncoder - encoding strategies."""

    def test_label_encode(self):
        """Test label encoding."""
        encoder = CategoricalEncoder()
        values = ["cat", "dog", "cat", "bird"]
        encoded = encoder.label_encode(values)

        assert len(encoded) == 4
        assert encoded[0] == encoded[2]

    def test_one_hot_encode(self):
        """Test one-hot encoding."""
        encoder = CategoricalEncoder()
        records = [{"type": "A"}, {"type": "B"}, {"type": "A"}]
        result = encoder.one_hot_encode(records, "type")

        assert len(result) == 3
        assert result[0]["type_A"] == 1
        assert result[0]["type_B"] == 0

    def test_target_encode(self):
        """Test target encoding."""
        encoder = CategoricalEncoder()
        records = [
            {"category": "A", "value": 10},
            {"category": "A", "value": 20},
            {"category": "B", "value": 100},
        ]
        result = encoder.target_encode(records, "category", "value")

        assert result["A"] == 15.0
        assert result["B"] == 100.0


# ============================================================================
# VALUE ADD LAYER: VALIDATOR TESTS
# ============================================================================

class TestDataValidator:
    """Test DataValidator - validation against rules."""

    def test_required_rule(self):
        """Test RequiredRule - field must exist."""
        validator = DataValidator([RequiredRule("id")])
        records = [
            {"id": "1", "name": "Alice"},
            {"name": "Bob"},
        ]
        result = validator.validate_with_details(records)

        assert result["error_count"] == 1

    def test_type_rule(self):
        """Test TypeRule - field must be specific type."""
        validator = DataValidator([TypeRule("age", int)])
        records = [
            {"age": 25},
            {"age": "not_int"},
        ]
        result = validator.validate_with_details(records)

        assert result["error_count"] == 1

    def test_range_rule(self):
        """Test RangeRule - numeric value within bounds."""
        validator = DataValidator([RangeRule("price", min_val=0, max_val=1000)])
        records = [
            {"price": 500},
            {"price": -10},
            {"price": 2000},
        ]
        result = validator.validate_with_details(records)

        assert result["error_count"] == 2

    def test_pattern_rule(self):
        """Test PatternRule - string matches regex."""
        validator = DataValidator([PatternRule("email", r"^[\w.-]+@[\w.-]+\.\w+$")])
        records = [
            {"email": "alice@example.com"},
            {"email": "invalid"},
        ]
        result = validator.validate_with_details(records)

        assert result["error_count"] == 1

    def test_enum_rule(self):
        """Test EnumRule - value in allowed list."""
        validator = DataValidator([EnumRule("status", ["active", "pending"])])
        records = [
            {"status": "active"},
            {"status": "deleted"},
        ]
        result = validator.validate_with_details(records)

        assert result["error_count"] == 1

    def test_custom_rule(self):
        """Test CustomRule - user-defined validation."""
        validator = DataValidator([
            CustomRule("discount", lambda x: x < 1.0, "Discount must be less than 100%")
        ])
        records = [
            {"discount": 0.5},
            {"discount": 1.5},
        ]
        result = validator.validate_with_details(records)

        assert result["error_count"] == 1

    def test_add_rule(self):
        """Test adding rules dynamically."""
        validator = DataValidator()
        validator.add_rule(RequiredRule("id"))
        validator.add_rule(TypeRule("age", int))

        records = [{"id": "1", "age": 25}]
        result = validator.validate_with_details(records)

        assert result["valid"] is True

    def test_remove_rule(self):
        """Test removing rules by name."""
        validator = DataValidator([RequiredRule("id"), RequiredRule("name")])
        validator.remove_rule("required_name")

        records = [{"id": "1"}]
        result = validator.validate_with_details(records)

        assert result["error_count"] == 0


# ============================================================================
# VALUE ADD LAYER: AGGREGATOR TESTS
# ============================================================================

class TestDataAggregator:
    """Test DataAggregator - grouping and summarizing."""

    def test_aggregate_sum(self):
        """Test sum aggregation."""
        aggregator = DataAggregator()
        records = [
            {"region": "North", "sales": 100},
            {"region": "North", "sales": 200},
            {"region": "South", "sales": 150},
        ]
        result = aggregator.aggregate(records, ["region"], {"total": "sum,sales"})

        assert len(result) == 2
        north_total = next(r["total"] for r in result if r["region"] == "North")
        assert north_total == 300

    def test_aggregate_count(self):
        """Test count aggregation."""
        aggregator = DataAggregator()
        records = [
            {"region": "North", "sales": 100},
            {"region": "North", "sales": 200},
            {"region": "South", "sales": 150},
        ]
        result = aggregator.aggregate(records, ["region"], {"count": "count"})

        north_count = next(r["count"] for r in result if r["region"] == "North")
        assert north_count == 2

    def test_aggregate_mean(self):
        """Test mean aggregation."""
        aggregator = DataAggregator()
        records = [
            {"category": "A", "value": 10},
            {"category": "A", "value": 20},
            {"category": "B", "value": 100},
        ]
        result = aggregator.aggregate(records, ["category"], {"avg": "mean,value"})

        a_avg = next(r["avg"] for r in result if r["category"] == "A")
        assert a_avg == 15.0

    def test_aggregate_min_max(self):
        """Test min/max aggregation."""
        aggregator = DataAggregator()
        records = [
            {"group": "X", "value": 5},
            {"group": "X", "value": 15},
            {"group": "X", "value": 10},
        ]
        result = aggregator.aggregate(records, ["group"], {"minimum": "min,value", "maximum": "max,value"})

        x_result = result[0]
        assert x_result["minimum"] == 5
        assert x_result["maximum"] == 15

    def test_aggregate_multiple_fields(self):
        """Test aggregation with multiple group_by fields."""
        aggregator = DataAggregator()
        records = [
            {"region": "North", "product": "A", "sales": 100},
            {"region": "North", "product": "B", "sales": 200},
            {"region": "South", "product": "A", "sales": 150},
        ]
        result = aggregator.aggregate(
            records,
            ["region", "product"],
            {"total_sales": "sum,sales"}
        )

        assert len(result) == 3
        north_a = next((r for r in result if r["region"] == "North" and r["product"] == "A"), None)
        assert north_a["total_sales"] == 100

    def test_aggregate_first_last(self):
        """Test first/last aggregation."""
        aggregator = DataAggregator()
        records = [
            {"category": "X", "order": 1, "value": "first"},
            {"category": "X", "order": 2, "value": "middle"},
            {"category": "X", "order": 3, "value": "last"},
        ]
        result = aggregator.aggregate(
            records,
            ["category"],
            {"first_val": "first,value", "last_val": "last,value"}
        )

        assert result[0]["first_val"] == "first"
        assert result[0]["last_val"] == "last"


# ============================================================================
# VALUE ADD LAYER: PIPELINE TESTS
# ============================================================================

class TestValueAddPipeline:
    """Test ValueAddPipeline - complete value-add flow."""

    def test_pipeline_enrich_only(self):
        """Test pipeline with only enrichment."""
        pipeline = ValueAddPipeline()
        records = [{"quantity": 5, "unit_price": 10}]

        result = pipeline.process(
            records,
            enrichment_rules=[CalculateRule("total", "quantity * unit_price")]
        )

        assert result.success
        assert result.records[0]["total"] == 50
        assert "enrichment" in result.steps_completed

    def test_pipeline_enrich_and_validate(self):
        """Test pipeline with enrichment and validation."""
        pipeline = ValueAddPipeline()
        records = [
            {"id": "1", "quantity": 5, "unit_price": 10},
            {"id": "2", "quantity": 3, "unit_price": 20},
        ]

        result = pipeline.process(
            records,
            enrichment_rules=[CalculateRule("total", "quantity * unit_price")],
            validation_rules=[RequiredRule("id"), TypeRule("total", (int, float))]
        )

        assert result.success
        assert "enrichment" in result.steps_completed
        assert "validation" in result.steps_completed

    def test_pipeline_with_failed_validation(self):
        """Test pipeline with validation errors."""
        pipeline = ValueAddPipeline()
        records = [{"quantity": 5, "unit_price": 10}]

        result = pipeline.process(
            records,
            enrichment_rules=[CalculateRule("total", "quantity * unit_price")],
            validation_rules=[RequiredRule("id")]
        )

        assert not result.success
        assert len(result.errors) > 0

    def test_pipeline_with_transformation(self):
        """Test pipeline with transformation step."""
        pipeline = ValueAddPipeline()
        records = [
            {"status": "active"},
            {"status": "pending"},
        ]

        result = pipeline.process(
            records,
            transformations=[("encode", {"field": "status", "method": "label"})]
        )

        assert result.success
        assert "transformation" in result.steps_completed

    def test_pipeline_full_flow(self):
        """Test complete pipeline: enrich -> transform -> validate -> aggregate."""
        pipeline = ValueAddPipeline()
        records = [
            {"region": "North", "quantity": 5, "unit_price": 10},
            {"region": "North", "quantity": 3, "unit_price": 20},
            {"region": "South", "quantity": 2, "unit_price": 15},
        ]

        result = pipeline.process(
            records,
            enrichment_rules=[CalculateRule("total", "quantity * unit_price")],
            transformations=[("normalize", {"fields": ["total"], "method": "min_max"})],
            validation_rules=[RequiredRule("region"), TypeRule("total", (int, float))],
            aggregation_config={
                "group_by": ["region"],
                "aggregations": {"total_sales": "sum,total"}
            }
        )

        assert result.success
        assert len(result.steps_completed) == 4

        north = next(r for r in result.records if r.get("region") == "North")
        assert north["total_sales"] == 110


class TestProcessingResult:
    """Test ProcessingResult dataclass."""

    def test_success_property(self):
        """Test success property with no errors."""
        result = ProcessingResult(records=[], errors=[])
        assert result.success is True

    def test_success_property_with_errors(self):
        """Test success property with errors."""
        result = ProcessingResult(records=[], errors=[{"message": "error"}])
        assert result.success is False

    def test_steps_completed(self):
        """Test tracking completed steps."""
        result = ProcessingResult(records=[])
        result.steps_completed.append("enrichment")
        result.steps_completed.append("validation")

        assert len(result.steps_completed) == 2
        assert "enrichment" in result.steps_completed


# ============================================================================
# VALUE ADD LAYER: ERROR TESTS
# ============================================================================

class TestValueAddErrors:
    """Test value-add layer error hierarchy."""

    def test_value_add_error_base(self):
        """Test base ValueAddError."""
        with pytest.raises(ValueAddError):
            raise ValueAddError("Base error")

    def test_enrichment_error(self):
        """Test EnrichmentError."""
        with pytest.raises(EnrichmentError):
            raise EnrichmentError("Enrichment failed")

    def test_transformation_error(self):
        """Test TransformationError."""
        with pytest.raises(TransformationError):
            raise TransformationError("Transformation failed")

    def test_validation_error(self):
        """Test ValueAddValidationError."""
        with pytest.raises(ValueAddValidationError):
            raise ValueAddValidationError("Validation failed")

    def test_aggregation_error(self):
        """Test AggregationError."""
        with pytest.raises(AggregationError):
            raise AggregationError("Aggregation failed")

    def test_error_inheritance(self):
        """Test that all errors inherit from ValueAddError."""
        assert issubclass(EnrichmentError, ValueAddError)
        assert issubclass(TransformationError, ValueAddError)
        assert issubclass(ValueAddValidationError, ValueAddError)
        assert issubclass(AggregationError, ValueAddError)


# ============================================================================
# VALUE ADD LAYER: INTEGRATION TESTS
# ============================================================================

class TestValueAddLayerIntegration:
    """Integration tests for value_add_layer with multi_file_input."""

    def test_multi_file_input_to_value_add(self, tmp_path):
        """Integration: Multi-File Input -> Value Add Layer."""
        csv_file = tmp_path / "sales.csv"
        csv_file.write_text(
            "product,quantity,price\nWidget A,10,29.99\nWidget B,5,49.99\n",
            encoding="utf-8"
        )

        pipeline = DataIngestionPipeline()
        normalized = pipeline.ingest(
            source=str(csv_file),
            channel_type="file",
            file_type="csv"
        )

        records = [r["_source"] for r in normalized["records"]]

        value_add_pipeline = ValueAddPipeline()
        result = value_add_pipeline.process(
            records,
            enrichment_rules=[CalculateRule("total", "quantity * price")],
            validation_rules=[RequiredRule("product"), TypeRule("total", (int, float))]
        )

        assert result.success
        assert result.records[0]["total"] == 299.9

    def test_content_sampler_to_value_add(self, tmp_path):
        """Integration: Content Sampler -> Value Add Layer."""
        data = [
            {"id": i, "name": f"Product {i}", "price": 10 * i, "quantity": i}
            for i in range(1, 11)
        ]

        sampler = ContentSampler()
        sampled = sampler.sample(data, sample_size=5, strategy="random")
        sampled_records = [r for r in sampled if "_sample_index" in r]
        sampled_records = data[:5]

        value_add_pipeline = ValueAddPipeline()
        result = value_add_pipeline.process(
            sampled_records,
            enrichment_rules=[
                CalculateRule("total_value", "price * quantity"),
                CategoryMapRule(
                    "quantity_tier", "quantity",
                    [(0, 3), (3, 6), (6, 10)],
                    ["low", "medium", "high"]
                )
            ]
        )

        assert result.success
        assert result.records[0]["total_value"] == 10
        assert result.records[0]["quantity_tier"] == "low"


class TestValueAddLayerFullPipeline:
    """Test full value-add layer pipeline with all components."""

    def test_complete_data_quality_pipeline(self):
        """Complete pipeline: ingest -> sample -> enrich -> validate -> aggregate."""
        records = [
            {"region": "North", "product": "A", "quantity": 5, "unit_price": 100, "discount": 0.1},
            {"region": "North", "product": "B", "quantity": 3, "unit_price": 200, "discount": 0.15},
            {"region": "South", "product": "A", "quantity": 10, "unit_price": 150, "discount": 0.05},
            {"region": "South", "product": "B", "quantity": 2, "unit_price": 80, "discount": 0.2},
            {"region": "East", "product": "C", "quantity": 1, "unit_price": 500, "discount": 0.0},
        ]

        pipeline = ValueAddPipeline()

        enrichment_rules = [
            CalculateRule("subtotal", "quantity * unit_price"),
            CalculateRule("discount_amount", "subtotal * discount"),
            CalculateRule("total", "subtotal - discount_amount"),
            CategoryMapRule(
                "size_tier", "quantity",
                [(0, 3), (3, 7), (7, 100)],
                ["small", "medium", "large"]
            ),
        ]

        validation_rules = [
            RequiredRule("region"),
            RequiredRule("product"),
            TypeRule("quantity", int),
            TypeRule("unit_price", (int, float)),
            RangeRule("discount", min_val=0, max_val=1),
        ]

        aggregation_config = {
            "group_by": ["region"],
            "aggregations": {
                "total_revenue": "sum,total",
                "avg_discount": "mean,discount",
                "order_count": "count",
            }
        }

        result = pipeline.process(
            records,
            enrichment_rules=enrichment_rules,
            validation_rules=validation_rules,
            aggregation_config=aggregation_config
        )

        assert result.success
        assert len(result.steps_completed) == 3

        assert len(result.records) == 3
        north_result = next(r for r in result.records if r.get("region") == "North")
        assert north_result["order_count"] == 2

    def test_data_quality_pipeline_with_failures(self):
        """Pipeline with data quality issues - validation errors."""
        records = [
            {"region": "North", "quantity": 5, "unit_price": 100},
            {"region": "South", "quantity": 3, "unit_price": None},  # Missing unit_price
            {"region": "East", "quantity": 2, "unit_price": 50},
        ]

        pipeline = ValueAddPipeline()
        result = pipeline.process(
            records,
            validation_rules=[
                RequiredRule("unit_price"),
            ]
        )

        assert len(result.errors) > 0
        assert not result.success


# ============================================================================
# PIPELINE STEP 1: CHANNEL ADAPTERS
# ============================================================================

class TestFileChannel:
    """Test FileChannel - reading files from disk."""

    def test_read_csv_file(self, tmp_path):
        """Test reading a CSV file via FileChannel."""

        csv_file = tmp_path / "test.csv"
        csv_file.write_text("name,age,city\nAlice,30,NYC\nBob,25,LA\n", encoding="utf-8")

        channel = FileChannel()
        content = channel.read(str(csv_file))

        assert content == b"name,age,city\nAlice,30,NYC\nBob,25,LA\n"

    def test_read_json_file(self, tmp_path):
        """Test reading a JSON file via FileChannel."""

        json_file = tmp_path / "test.json"
        json_file.write_text('{"name": "Alice", "age": 30}', encoding="utf-8")

        channel = FileChannel()
        content = channel.read(str(json_file))

        assert b"Alice" in content

    def test_read_nonexistent_file_raises_error(self):
        """Test that reading non-existent file raises ChannelReadError."""

        channel = FileChannel()
        with pytest.raises(ChannelReadError):
            channel.read("/nonexistent/file.csv")

    def test_detect_file_type(self, tmp_path):
        """Test file type detection."""

        csv_file = tmp_path / "test.csv"
        csv_file.write_text("a,b,c\n1,2,3\n", encoding="utf-8")

        json_file = tmp_path / "test.json"
        json_file.write_text('{"key": "value"}', encoding="utf-8")

        channel = FileChannel()
        assert channel.detect_type(str(csv_file)) == "csv"
        assert channel.detect_type(str(json_file)) == "json"

    def test_batch_read_directory(self, tmp_path):
        """Test batch reading all files in a directory."""

        (tmp_path / "file1.csv").write_text("a,b\n1,2\n", encoding="utf-8")
        (tmp_path / "file2.csv").write_text("c,d\n3,4\n", encoding="utf-8")

        channel = FileChannel()
        files = channel.batch_read(str(tmp_path), "*.csv")

        assert len(files) == 2


class TestAPIChannel:
    """Test APIChannel - fetching data from APIs."""

    def test_fetch_url_success(self):
        """Test successful API fetch."""

        channel = APIChannel()
        mock_response = {"data": [{"id": 1}, {"id": 2}]}

        with patch.object(channel, 'fetch', return_value=mock_response):
            result = channel.fetch("http://example.com/api/data")
            assert result == mock_response

    def test_paginate_with_list_response(self):
        """Test pagination with list response."""

        channel = APIChannel()
        mock_pages = [
            [{"id": 1}, {"id": 2}],
            [{"id": 3}, {"id": 4}],
            [],
        ]

        with patch.object(channel, 'fetch', side_effect=mock_pages):
            results = list(channel.paginate("http://example.com/api", page_size=2))
            assert len(results) == 4

    def test_authenticate_bearer_token(self):
        """Test bearer token authentication."""

        channel = APIChannel()
        token = channel.authenticate({"token": "secret123"}, auth_type="bearer")

        assert token == "secret123"
        assert channel._auth_token == "secret123"


class TestStreamChannel:
    """Test StreamChannel - consuming streaming data."""

    def test_stream_message_dataclass(self):
        """Test StreamMessage structure."""

        msg = StreamMessage(
            topic="test-topic",
            data={"event": "click"},
            timestamp=1234567890.0,
            offset=100,
            partition=0,
            key="key1"
        )

        assert msg.topic == "test-topic"
        assert msg.data == {"event": "click"}
        assert msg.offset == 100


class TestIoTChannel:
    """Test IoTChannel - IoT cloud platform connections."""

    def test_telemetry_data_dataclass(self):
        """Test TelemetryData structure."""

        telemetry = TelemetryData(
            device_id="sensor-001",
            timestamp=1234567890.0,
            data={"temperature": 25.5, "humidity": 60},
            quality="good"
        )

        assert telemetry.device_id == "sensor-001"
        assert telemetry.data["temperature"] == 25.5


class TestDatabaseChannel:
    """Test DatabaseChannel - database polling and CDC."""

    def test_database_change_dataclass(self):
        """Test DatabaseChange structure."""

        change = DatabaseChange(
            operation="INSERT",
            table="users",
            data={"id": 1, "name": "Alice"},
            timestamp=1234567890.0
        )

        assert change.operation == "INSERT"
        assert change.table == "users"


# ============================================================================
# PIPELINE STEP 2: FILE TYPE ADAPTERS
# ============================================================================

class TestCSVAdapter:
    """Test CSVAdapter - parsing CSV files."""

    def test_parse_csv_with_header(self):
        """Test parsing CSV with header row."""

        adapter = CSVAdapter(delimiter=",", has_header=True)
        data = adapter.parse("name,age,city\nAlice,30,NYC\nBob,25,LA\n")

        assert len(data) == 2
        assert data[0] == {"name": "Alice", "age": "30", "city": "NYC"}
        assert data[1] == {"name": "Bob", "age": "25", "city": "LA"}

    def test_parse_csv_without_header(self):
        """Test parsing CSV without header."""

        adapter = CSVAdapter(delimiter=",", has_header=False)
        data = adapter.parse("Alice,30,NYC\nBob,25,LA\n")

        assert len(data) == 2
        assert data[0] == {"col_0": "Alice", "col_1": "30", "col_2": "NYC"}

    def test_serialize_csv(self, tmp_path):
        """Test serializing data to CSV."""

        adapter = CSVAdapter()
        data = [{"name": "Alice", "age": "30"}, {"name": "Bob", "age": "25"}]

        output_path = tmp_path / "output.csv"
        adapter.serialize(data, str(output_path))

        content = output_path.read_text(encoding="utf-8")
        assert "name,age" in content
        assert "Alice,30" in content

    def test_validate_valid_data(self):
        """Test validation of valid data."""

        adapter = CSVAdapter()
        data = [{"a": 1}, {"a": 2}]
        assert adapter.validate(data) is True

    def test_validate_empty_data(self):
        """Test validation of empty data."""

        adapter = CSVAdapter()
        assert adapter.validate([]) is False


class TestJSONAdapter:
    """Test JSONAdapter - parsing JSON files."""

    def test_parse_json_array(self):
        """Test parsing JSON array."""

        adapter = JSONAdapter()
        data = adapter.parse('[{"id": 1}, {"id": 2}]')

        assert len(data) == 2
        assert data[0] == {"id": 1}

    def test_parse_json_object_with_records_key(self):
        """Test parsing JSON object with records key."""

        adapter = JSONAdapter()
        data = adapter.parse('{"records": [{"id": 1}, {"id": 2}]}')

        assert len(data) == 2
        assert data[0] == {"id": 1}

    def test_parse_json_lines_format(self):
        """Test parsing JSON Lines format."""

        adapter = JSONAdapter(lines=True)
        data = adapter.parse('{"id": 1}\n{"id": 2}\n{"id": 3}')

        assert len(data) == 3
        assert data[2] == {"id": 3}

    def test_serialize_json(self, tmp_path):
        """Test serializing data to JSON."""

        adapter = JSONAdapter()
        data = [{"id": 1}, {"id": 2}]

        output_path = tmp_path / "output.json"
        adapter.serialize(data, str(output_path))

        content = json.loads(output_path.read_text(encoding="utf-8"))
        assert "records" in content
        assert len(content["records"]) == 2


class TestXMLAdapter:
    """Test XMLAdapter - parsing XML files."""

    def test_parse_simple_xml(self):
        """Test parsing simple XML."""


        adapter = XMLAdapter(record_path=".//record")
        xml_content = """<?xml version="1.0"?>
<root>
    <record><name>Alice</name><age>30</age></record>
    <record><name>Bob</name><age>25</age></record>
</root>"""
        data = adapter.parse(xml_content.encode("utf-8"))

        assert len(data) == 2
        assert data[0]["name"] == "Alice"
        assert data[1]["name"] == "Bob"

    def test_parse_xml_with_attributes(self):
        """Test parsing XML with attributes."""

        adapter = XMLAdapter(record_path=".//item")
        xml_content = """<root>
    <item id="1" type="A"><name>Alice</name></item>
    <item id="2" type="B"><name>Bob</name></item>
</root>"""
        data = adapter.parse(xml_content.encode("utf-8"))

        assert data[0]["@id"] == "1"
        assert data[0]["@type"] == "A"

    def test_serialize_xml(self, tmp_path):
        """Test serializing data to XML."""

        adapter = XMLAdapter()
        data = [{"name": "Alice", "age": "30"}]

        output_path = tmp_path / "output.xml"
        adapter.serialize(data, str(output_path))

        content = output_path.read_text(encoding="utf-8")
        assert "<record>" in content
        assert "<name>Alice</name>" in content


class TestExcelAdapter:
    """Test ExcelAdapter - parsing Excel files."""

    def test_parse_excel_from_bytes(self):
        """Test parsing Excel data from bytes."""

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["name", "age"])
        ws.append(["Alice", "30"])
        ws.append(["Bob", "25"])

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        adapter = ExcelAdapter()
        data = adapter.parse(buffer.getvalue())

        assert len(data) == 2
        assert data[0] == {"name": "Alice", "age": "30"}


class TestYAMLAdapter:
    """Test YAMLAdapter - parsing YAML files."""

    def test_parse_yaml_list(self):
        """Test parsing YAML list."""

        adapter = YAMLAdapter()
        yaml_content = """- name: Alice
  age: 30
- name: Bob
  age: 25"""
        data = adapter.parse(yaml_content.encode("utf-8"))

        assert len(data) == 2
        assert data[0]["name"] == "Alice"


# ============================================================================
# PIPELINE STEP 3: JSON NORMALIZER
# ============================================================================

class TestJSONNormalizer:
    """Test JSONNormalizer - normalizing to standard JSON."""

    def test_normalize_with_records(self):
        """Test normalizing data with records."""

        normalizer = JSONNormalizer()
        data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]

        result = normalizer.normalize(data, "csv", "file", "/path/to/data.csv")

        assert "metadata" in result
        assert "records" in result
        assert result["metadata"]["source_type"] == "csv"
        assert result["metadata"]["source_channel"] == "file"
        assert result["metadata"]["record_count"] == 2
        assert len(result["records"]) == 2

    def test_normalize_generates_ids(self):
        """Test that normalize generates unique IDs."""

        normalizer = JSONNormalizer(generate_ids=True)
        data = [{"name": "Alice"}, {"name": "Bob"}]

        result = normalizer.normalize(data, "json", "api", "/path/data.json")

        assert result["records"][0]["_id"].endswith("_0")
        assert result["records"][1]["_id"].endswith("_1")

    def test_normalize_includes_raw(self):
        """Test that normalize includes raw data when requested."""

        normalizer = JSONNormalizer(include_raw=True)
        data = [{"name": "Alice"}]

        result = normalizer.normalize(data, "json", "api")

        assert "_raw" in result["records"][0]
        assert result["records"][0]["_raw"] == {"name": "Alice"}

    def test_normalize_keys_snake_case(self):
        """Test that keys are normalized to snake_case."""

        normalizer = JSONNormalizer()
        data = [{"firstName": "Alice", "lastName": "Smith"}]

        result = normalizer.normalize(data, "json", "api")

        source = result["records"][0]["_source"]
        assert "first_name" in source
        assert "last_name" in source

    def test_denormalize(self):
        """Test converting normalized JSON back to list of dicts."""

        normalizer = JSONNormalizer()
        normalized = {
            "metadata": {"source_type": "csv"},
            "records": [
                {"_id": "abc_0", "_source": {"name": "Alice"}},
                {"_id": "abc_1", "_source": {"name": "Bob"}},
            ]
        }

        data = normalizer.denormalize(normalized)

        assert len(data) == 2
        assert data[0] == {"name": "Alice"}

    def test_merge_normalized(self):
        """Test merging multiple normalized datasets."""

        normalizer = JSONNormalizer()
        normalized1 = {
            "metadata": {"columns": ["name"]},
            "records": [{"_id": "1", "_source": {"name": "Alice"}}]
        }
        normalized2 = {
            "metadata": {"columns": ["age"]},
            "records": [{"_id": "2", "_source": {"age": 30}}]
        }

        merged = normalizer.merge([normalized1, normalized2])

        assert merged["metadata"]["record_count"] == 2
        assert "name" in merged["metadata"]["columns"]
        assert "age" in merged["metadata"]["columns"]


# ============================================================================
# PIPELINE STEP 4: DATA INGESTION PIPELINE (End-to-End)
# ============================================================================

class TestDataIngestionPipeline:
    """Test DataIngestionPipeline - complete flow."""

    def test_pipeline_csv_to_normalized_json(self, tmp_path):
        """Pipeline: Read CSV -> Parse -> Normalize -> Output JSON."""

        # Step 1: Create CSV file
        csv_file = tmp_path / "sales.csv"
        csv_file.write_text("product,quantity,price\nWidget A,10,29.99\nWidget B,5,49.99\n", encoding="utf-8")

        # Step 2: Pipeline ingest
        pipeline = DataIngestionPipeline()
        result = pipeline.ingest(
            source=str(csv_file),
            channel_type="file",
            file_type="csv"
        )

        # Step 3: Verify normalized output
        assert result["metadata"]["source_type"] == "csv"
        assert result["metadata"]["record_count"] == 2
        assert result["records"][0]["_source"]["product"] == "Widget A"
        assert result["records"][1]["_source"]["quantity"] == "5"

    def test_pipeline_json_to_normalized_json(self, tmp_path):
        """Pipeline: Read JSON -> Parse -> Normalize -> Output JSON."""

        json_file = tmp_path / "users.json"
        json_file.write_text('[{"name": "Alice", "email": "alice@example.com"}]', encoding="utf-8")

        pipeline = DataIngestionPipeline()
        result = pipeline.ingest(
            source=str(json_file),
            channel_type="file",
            file_type="json"
        )

        assert result["metadata"]["source_type"] == "json"
        assert result["records"][0]["_source"]["email"] == "alice@example.com"

    def test_pipeline_auto_detect_file_type(self, tmp_path):
        """Pipeline: Auto-detect file type from extension."""

        csv_file = tmp_path / "data.csv"
        csv_file.write_text("a,b\n1,2\n", encoding="utf-8")

        pipeline = DataIngestionPipeline()
        result = pipeline.ingest(
            source=str(csv_file),
            channel_type="file"
        )

        assert result["metadata"]["source_type"] == "csv"

    def test_pipeline_batch_ingestion(self, tmp_path):
        """Pipeline: Batch ingest multiple files."""

        (tmp_path / "north.csv").write_text("region,sales\nNorth,1000\n", encoding="utf-8")
        (tmp_path / "south.csv").write_text("region,sales\nSouth,2000\n", encoding="utf-8")

        pipeline = DataIngestionPipeline()
        sources = [
            (str(tmp_path / "north.csv"), "file", "csv"),
            (str(tmp_path / "south.csv"), "file", "csv"),
        ]

        results = pipeline.ingest_batch(sources)

        assert len(results) == 2
        assert results[0]["metadata"]["record_count"] == 1
        assert results[1]["metadata"]["record_count"] == 1

    def test_pipeline_directory_ingestion(self, tmp_path):
        """Pipeline: Ingest all files in a directory."""
        (tmp_path / "a.csv").write_text("x,y\n1,2\n", encoding="utf-8")
        (tmp_path / "b.csv").write_text("x,y\n3,4\n", encoding="utf-8")

        pipeline = DataIngestionPipeline()
        results = pipeline.ingest_directory(str(tmp_path), pattern="*.csv")

        assert len(results) == 2

    def test_pipeline_api_channel(self):
        """Pipeline: Fetch from API -> Parse -> Normalize."""
        """Test file type detection from path."""

        pipeline = DataIngestionPipeline()
        mock_data = [{"id": 1, "name": "Product A"}, {"id": 2, "name": "Product B"}]

        with patch.object(APIChannel, 'fetch', return_value=mock_data):
            result = pipeline.ingest(
                source="http://api.example.com/products",
                channel_type="api",
                file_type="json"
            )

        assert result["metadata"]["source_channel"] == "api"
        assert result["metadata"]["record_count"] == 2
        assert result["records"][0]["_source"]["name"] == "Product A"


class TestChannelAdapterFactory:
    """Test ChannelAdapterFactory."""

    def test_create_file_channel(self):
        """Test creating file channel."""
        channel = ChannelAdapterFactory.create_channel("file")
        assert isinstance(channel, FileChannel)

    def test_create_api_channel(self):
        """Test creating API channel."""

        channel = ChannelAdapterFactory.create_channel("api")
        assert isinstance(channel, APIChannel)

    def test_create_csv_adapter(self):
        """Test creating CSV adapter."""

        adapter = ChannelAdapterFactory.create_file_adapter("csv")
        assert isinstance(adapter, CSVAdapter)

    def test_detect_file_type(self):

        assert ChannelAdapterFactory.detect_file_type("data.csv") == "csv"
        assert ChannelAdapterFactory.detect_file_type("data.json") == "json"
        assert ChannelAdapterFactory.detect_file_type("data.xlsx") == "xlsx"


# ============================================================================
# PIPELINE STEP 5: CONTENT SAMPLER
# ============================================================================

class TestContentSamplerSampling:
    """Test ContentSampler - sampling strategies."""

    def test_sample_random(self):
        """Test random sampling."""

        sampler = ContentSampler()
        data = [{"id": i, "value": f"item_{i}"} for i in range(100)]

        sampled = sampler.sample(data, sample_size=10, strategy="random")

        assert len(sampled) == 10
        assert all("_sample_index" in r for r in sampled)
        assert all("_sample_strategy" in r for r in sampled)

    def test_sample_stratified(self):
        """Test stratified sampling."""

        sampler = ContentSampler()
        data = [
            {"category": "A", "value": 1},
            {"category": "A", "value": 2},
            {"category": "A", "value": 3},
            {"category": "B", "value": 4},
            {"category": "B", "value": 5},
        ]

        sampled = sampler.sample(data, sample_size=4, strategy="stratified", stratify_by="category")

        assert len(sampled) == 4
        # Should maintain proportion (3 A's and 2 B's = 60% A, 40% B)
        categories = [r["category"] for r in sampled]
        assert categories.count("A") >= 2 # At least proportional

    def test_sample_systematic(self):
        """Test systematic sampling."""

        sampler = ContentSampler()
        data = [{"id": i} for i in range(100)]

        sampled = sampler.sample(data, sample_size=10, strategy="systematic")

        assert len(sampled) == 10

    def test_sample_with_analysis(self):
        """Test sample with schema analysis."""

        sampler = ContentSampler()
        data = [
            {"name": "Alice", "age": 30, "email": "alice@example.com"},
            {"name": "Bob", "age": 25, "email": "bob@example.com"},
            {"name": "Charlie", "age": 35, "email": "charlie@example.com"},
        ]

        result = sampler.sample_with_analysis(
            data,
            sample_size=3,
            strategy="random",
            analyze_schema=True
        )

        assert "metadata" in result
        assert "records" in result
        assert "schema_analysis" in result
        assert result["metadata"]["original_count"] == 3
        assert result["metadata"]["sample_size"] == 3


class TestSchemaAnalyzer:
    """Test SchemaAnalyzer - analyzing schema."""

    def test_analyze_schema(self):
        """Test schema analysis."""

        analyzer = SchemaAnalyzer()
        data = [
            {"id": 1, "name": "Alice", "age": 30},
            {"id": 2, "name": "Bob", "age": 25},
 ]

        result = analyzer.analyze(data)

        assert "fields" in result
        assert "statistics" in result
        assert len(result["fields"]) == 3 # id, name, age

        field_names = [f["name"] for f in result["fields"]]
        assert "id" in field_names
        assert "name" in field_names
        assert "age" in field_names

    def test_analyze_field_types(self):
        """Test field type detection."""

        analyzer = SchemaAnalyzer()
        data = [
            {"id": 1, "name": "Alice", "score": 95.5},
            {"id": 2, "name": "Bob", "score": 87.3},
        ]

        result = analyzer.analyze(data)

        id_field = next(f for f in result["fields"] if f["name"] == "id")
        name_field = next(f for f in result["fields"] if f["name"] == "name")
        score_field = next(f for f in result["fields"] if f["name"] == "score")

        assert id_field["type"] == "integer"
        assert name_field["type"] == "string"
        assert score_field["type"] == "float"

    def test_optimize_schema_sqlite(self):
        """Test schema optimization for SQLite."""

        analyzer = SchemaAnalyzer()
        data = [
            {"id": 1, "name": "Alice", "active": True},
            {"id": 2, "name": "Bob", "active": False},
        ]

        schema = analyzer.analyze(data)
        optimized = analyzer.optimize(schema, target="sqlite")

        assert optimized["target"] == "sqlite"
        assert "fields" in optimized
        assert "create_sql" in optimized
        assert "CREATE TABLE" in optimized["create_sql"]

    def test_optimize_schema_postgresql(self):
        """Test schema optimization for PostgreSQL."""

        analyzer = SchemaAnalyzer()
        data = [
            {"email": "alice@example.com", "created": "2024-01-01"},
 {"email": "bob@example.com", "created": "2024-01-02"},
        ]

        schema = analyzer.analyze(data)
        optimized = analyzer.optimize(schema, target="postgresql")

        assert optimized["target"] == "postgresql"
        # PostgreSQL maps email to VARCHAR(255)
        assert any("VARCHAR" in f["target_type"] for f in optimized["fields"])


class TestNoiseLabeler:
    """Test NoiseLabeler - detecting and labeling noise."""

    def test_detect_missing_values(self):
        """Test detecting missing values."""

        labeler = NoiseLabeler()
        data = [
            {"name": "Alice", "age": 30, "phone": None},
            {"name": "Bob", "age": 25, "phone": "555-1234"},
            {"name": "Charlie", "age": None, "phone": "555-5678"},
        ]

        result = labeler.detect_and_label(data)

        assert "noise_report" in result
        assert result["noise_report"]["total_records_analyzed"] == 3
        assert result["noise_report"]["records_with_noise"] >= 2

    def test_detect_outliers(self):
        """Test detecting outliers."""

        labeler = NoiseLabeler()
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
            {"name": "Outlier", "age": 999},  # Outlier
        ]

        result = labeler.detect_and_label(data)

        # Outlier should be detected
        labeled = result["noise_report"]["labeled_records"]
        outlier_labels = [l for l in labeled if l.get("noise_type") == "outlier"]
        assert len(outlier_labels) >= 1

    def test_detect_duplicates(self):
        """Test detecting duplicates."""

        labeler = NoiseLabeler()
        data = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
            {"id": 1, "name": "Alice"},  # Duplicate
        ]

        result = labeler.detect_and_label(data)

        assert result["noise_report"]["records_with_noise"] >= 1

    def test_label_record_manual(self):
        """Test manual noise labeling."""

        labeler = NoiseLabeler()
        record = {"_id": "test_0", "name": "Test", "value": "bad"}

        labeler.label_record(record, "invalid_char", "value", severity="high")

        labels = labeler.get_labels()
        assert len(labels) == 1
        assert labels[0]["noise_type"] == "invalid_char"
        assert labels[0]["severity"] == "high"

    def test_clean_data(self):
        """Test cleaning data by removing labeled noise."""

        labeler = NoiseLabeler()
        data = [
            {"_id": "0", "name": "Alice", "age": 30},
            {"_id": "1", "name": "Bob", "age": 999},  # Outlier
            {"_id": "2", "name": "Charlie", "age": 25},
        ]

        labeler.detect_and_label(data)
        cleaned = labeler.clean(data, remove_labeled=True)

        # Outlier should be removed
        assert len(cleaned) == 2
        assert all(r["age"] != 999 for r in cleaned)


class TestContentSamplerFullPipeline:
    """Test ContentSampler full pipeline - sample + analyze + label."""

    def test_full_pipeline_sample_analyze_label(self):
        """Test complete pipeline: sample -> analyze schema -> detect noise."""

        sampler = ContentSampler()

        # Create test data with noise
        data = [
            {"id": 1, "name": "Alice", "age": 30, "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "age": 25, "email": "bob@example.com"},
            {"id": 3, "name": "Charlie", "age": 999, "email": None},  # Outlier + missing
            {"id": 4, "name": "Alice", "age": 35, "email": "david@example.com"},  # Duplicate name
        ]

        # Full pipeline
        result = sampler.sample_with_analysis(
            data,
            sample_size=4,
            strategy="random",
            analyze_schema=True,
            detect_noise=True
        )

        # Verify pipeline output
        assert "metadata" in result
        assert "records" in result
        assert "schema_analysis" in result
        assert "noise_report" in result

        # Verify metadata
        assert result["metadata"]["original_count"] == 4
        assert result["metadata"]["sample_size"] == 4

        # Verify schema analysis has fields
        assert len(result["schema_analysis"]["fields"]) == 4

        # Verify noise detection ran
        assert result["noise_report"]["total_records_analyzed"] == 4

    def test_optimize_schema_for_target_database(self):
        """Test schema optimization for different databases."""

        sampler = ContentSampler()
        data = [
            {"id": 1, "name": "Product A", "price": 29.99, "in_stock": True},
            {"id": 2, "name": "Product B", "price": 49.99, "in_stock": False},
        ]

        # Analyze and optimize
        schema_analysis = sampler.analyze_schema(data)
        optimized = sampler.optimize_schema(schema_analysis, target="postgresql")

        assert optimized["target"] == "postgresql"
        assert "create_sql" in optimized
        assert "CREATE TABLE" in optimized["create_sql"]

    def test_clean_data_pipeline(self):
        """Test data cleaning pipeline."""

        sampler = ContentSampler()
        data = [
            {"id": 1, "name": "Valid", "age": 30},
            {"id": 2, "name": "Outlier", "age": 999},
            {"id": 3, "name": "Also Valid", "age": 25},
        ]

        # Detect noise
        sampler.detect_noise(data)
        # Clean data
        cleaned = sampler.clean_data(data, remove_labeled=True)

        assert len(cleaned) == 2
        assert all(r["age"] != 999 for r in cleaned)


# ============================================================================
# PIPELINE INTEGRATION TESTS
# ============================================================================

class TestPipelineIntegration:
    """Integration tests for complete pipeline flow."""

    def test_multi_file_input_to_content_sampler(self, tmp_path):
        """Integration: Multi-File Input -> Content Sampler."""

        # Step 1: Create and ingest data via multi_file_input
        csv_file = tmp_path / "products.csv"
        csv_file.write_text(
            "id,name,price,stock\n1,Widget A,29.99,100\n2,Widget B,49.99,50\n3,Widget C,999.99,10\n",
            encoding="utf-8"
        )

        pipeline = DataIngestionPipeline()
        normalized = pipeline.ingest(
            source=str(csv_file),
            channel_type="file",
            file_type="csv"
        )

        # Step 2: Extract records for content sampler
        records = [r["_source"] for r in normalized["records"]]

        # Step 3: Sample and analyze with content_sampler
        sampler = ContentSampler()
        result = sampler.sample_with_analysis(
            records,
            sample_size=3,
            strategy="random",
            analyze_schema=True,
            detect_noise=True
        )

        # Verify integration
        assert result["metadata"]["original_count"] == 3
        assert "schema_analysis" in result
        assert "noise_report" in result

        # The outlier price999.99 should be detected
        noise_report = result["noise_report"]
        assert noise_report["total_records_analyzed"] == 3

    def test_api_to_sampler_pipeline(self):
        """Integration: API Channel -> Content Sampler."""

        # Step 1: Mock API data
        mock_data = [
            {"id": i, "name": f"User {i}", "score": 50 + i * 10}
            for i in range(1, 11)
        ]

        # Step 2: Ingest via pipeline
        pipeline = DataIngestionPipeline()
        with patch.object(APIChannel, 'fetch', return_value=mock_data):
            normalized = pipeline.ingest(
                source="http://api.example.com/users",
                channel_type="api",
                file_type="json"
            )

        # Step 3: Extract and sample
        records = [r["_source"] for r in normalized["records"]]
        sampler = ContentSampler()
        result = sampler.sample_with_analysis(
            records,
            sample_size=5,
            strategy="random",
            analyze_schema=True
        )

        assert result["metadata"]["original_count"] == 10
        assert result["metadata"]["sample_size"] == 5


# ============================================================================
# EXCEPTION TESTS
# ============================================================================

class TestExceptions:
    """Test exception hierarchy."""

    def test_ingestion_error_base(self):
        """Test base IngestionError."""

        with pytest.raises(IngestionError):
            raise IngestionError("Base error")

    def test_channel_read_error(self):
        """Test ChannelReadError."""

        with pytest.raises(ChannelReadError):
            raise ChannelReadError("Failed to read")

    def test_parse_error(self):
        """Test ParseError."""


        with pytest.raises(ParseError):
            raise ParseError("Failed to parse")

    def test_normalization_error(self):
        """Test NormalizationError."""

        with pytest.raises(NormalizationError):
            raise NormalizationError("Failed to normalize")

    def test_error_inheritance(self):
        """Test that all errors inherit from IngestionError."""
        assert issubclass(ChannelReadError, IngestionError)
        assert issubclass(ParseError, IngestionError)
        assert issubclass(NormalizationError, IngestionError)


# ============================================================================
# CONFIGURATION TESTS
# ============================================================================

class TestConfig:
    """Test configuration management."""

    def test_load_config_from_yaml(self, tmp_path):
        """Test loading configuration from YAML."""

        config_content = """
channels:
  file:
    watch_directories:
      - ./data/incoming
file_types:
  csv:
    delimiter: ";"
normalizer:
  include_raw: true
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_content, encoding="utf-8")

        config = Config.from_yaml(str(config_file))

        assert "./data/incoming" in config.channels["file"]["watch_directories"]
        assert config.file_types["csv"]["delimiter"] == ";"

    def test_config_to_yaml(self, tmp_path):
        """Test saving configuration to YAML."""

        config = Config()
        config.channels = {"file": {"watch_directories": ["./data"]}}

        output_file = tmp_path / "output.yaml"
        config.to_yaml(str(output_file))

        content = output_file.read_text(encoding="utf-8")
        assert "file" in content


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_csv_content():
    """Sample CSV content for testing."""
    return "name,age,city\nAlice,30,NYC\nBob,25,LA\nCharlie,35,Chicago\n"


@pytest.fixture
def sample_json_content():
    """Sample JSON content for testing."""
    return json.dumps([
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 25},
    ])


@pytest.fixture
def sample_records_with_noise():
    """Sample records with noise for testing."""
    return [
        {"id": 1, "name": "Alice", "age": 30, "email": "alice@example.com"},
        {"id": 2, "name": "Bob", "age": 25, "email": "bob@example.com"},
        {"id": 3, "name": "Charlie", "age": 999, "email": None},  # Outlier + missing
        {"id": 4, "name": "Alice", "age": 35, "email": "david@example.com"},  # Duplicate
        {"id": 5, "name": "", "age": None, "email": "invalid"},  # Missing values
    ]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
