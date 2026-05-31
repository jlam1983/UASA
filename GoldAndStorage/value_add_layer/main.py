"""Value Add Layer - Main entry point.

A modular data transformation layer that enriches, validates, and transforms
raw data into value-added assets ready for storage and analysis.
"""

from .pipeline import ValueAddPipeline, ProcessingResult
from .enricher import DataEnricher
from .enricher.rules import (
    EnrichmentRule,
    CalculateRule,
    LookupRule,
    DateExtractRule,
    CategoryMapRule,
    ConditionalRule,
    DeriveRule,
)
from .transformer import DataTransformer, DataReshaper, Normalizer, CategoricalEncoder
from .validator import DataValidator
from .validator.rules import (
    ValidationRule,
    ValidationResult,
    RequiredRule,
    TypeRule,
    RangeRule,
    PatternRule,
    EnumRule,
    CustomRule,
    CrossFieldRule,
    UniqueRule,
)
from .aggregator import DataAggregator
from .errors import (
    ValueAddError,
    EnrichmentError,
    TransformationError,
    ValidationError,
    AggregationError,
)


def create_pipeline() -> ValueAddPipeline:
    """Create a new ValueAddPipeline instance."""
    return ValueAddPipeline()


def enrich_records(records, rules):
    """Enrich records with given rules."""
    enricher = DataEnricher()
    return enricher.enrich(records, rules)


def transform_records(records, strategy, config=None):
    """Transform records using specified strategy."""
    transformer = DataTransformer()
    return transformer.transform(records, strategy, config)


def validate_records(records, rules):
    """Validate records against given rules."""
    validator = DataValidator(rules)
    return validator.validate_with_details(records)


def aggregate_records(records, group_by, aggregations):
    """Aggregate records by grouping fields."""
    aggregator = DataAggregator()
    return aggregator.aggregate(records, group_by, aggregations)


__all__ = [
    # Pipeline
    "ValueAddPipeline",
    "ProcessingResult",
    # Enricher
    "DataEnricher",
    "EnrichmentRule",
    "CalculateRule",
    "LookupRule",
    "DateExtractRule",
    "CategoryMapRule",
    "ConditionalRule",
    "DeriveRule",
    # Transformer
    "DataTransformer",
    "DataReshaper",
    "Normalizer",
    "CategoricalEncoder",
    # Validator
    "DataValidator",
    "ValidationRule",
    "ValidationResult",
    "RequiredRule",
    "TypeRule",
    "RangeRule",
    "PatternRule",
    "EnumRule",
    "CustomRule",
    "CrossFieldRule",
    "UniqueRule",
    # Aggregator
    "DataAggregator",
    # Errors
    "ValueAddError",
    "EnrichmentError",
    "TransformationError",
    "ValidationError",
    "AggregationError",
    # Helpers
    "create_pipeline",
    "enrich_records",
    "transform_records",
    "validate_records",
    "aggregate_records",
]