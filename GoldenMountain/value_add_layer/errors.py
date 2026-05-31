"""Error classes for Value Add Layer."""


class ValueAddError(Exception):
    """Base exception for value-add layer errors."""
    pass


class EnrichmentError(ValueAddError):
    """Failed during enrichment."""
    pass


class TransformationError(ValueAddError):
    """Failed during transformation."""
    pass


class ValidationError(ValueAddError):
    """Data validation failed."""
    pass


class AggregationError(ValueAddError):
    """Failed during aggregation."""
    pass