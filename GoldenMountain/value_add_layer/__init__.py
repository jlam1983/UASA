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
from .manager import ValueAddManager, ProcessingResult
from .pipeline.pipeline import ValueAddPipeline

__all__ = [
    # Manager / Factory
    "ValueAddManager",
    "ProcessingResult",
    # Legacy pipeline
    "ValueAddPipeline",
    # Exceptions
    "ValueAddError",
    "EnrichmentError",
    "TransformationError",
    "ValidationErrorBase",
    "AggregationError",
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
]