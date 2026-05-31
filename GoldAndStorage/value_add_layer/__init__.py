"""Value Add Layer - Data enrichment, transformation, validation, and aggregation."""

from .errors import (
    ValueAddError,
    EnrichmentError,
    TransformationError,
    ValidationError as ValidationErrorBase,
    AggregationError,
)
from .enricher.enricher import DataEnricher
from .enricher.rules import (
    EnrichmentRule,
    CalculateRule,
    LookupRule,
    DateExtractRule,
    CategoryMapRule,
    ConditionalRule,
    DeriveRule,
)
from .transformer.transformer import DataTransformer, DataReshaper
from .transformer.normalizer import Normalizer
from .transformer.encoder import CategoricalEncoder
from .validator.validator import DataValidator
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
from .aggregator.aggregator import DataAggregator
from .pipeline.pipeline import ValueAddPipeline, ProcessingResult

__all__ = [
    "ValueAddError",
    "EnrichmentError",
    "TransformationError",
    "ValidationErrorBase",
    "AggregationError",
    "DataEnricher",
    "EnrichmentRule",
    "CalculateRule",
    "LookupRule",
    "DateExtractRule",
    "CategoryMapRule",
    "ConditionalRule",
    "DeriveRule",
    "DataTransformer",
    "DataReshaper",
    "Normalizer",
    "CategoricalEncoder",
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
    "DataAggregator",
    "ValueAddPipeline",
    "ProcessingResult",
]