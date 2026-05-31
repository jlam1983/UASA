"""Enrichment rule implementations."""

from abc import ABC, abstractmethod
from typing import Any


class EnrichmentRule(ABC):
    """Base class for enrichment rules."""

    def __init__(self, target_field: str):
        self.target_field = target_field

    @abstractmethod
    def compute(self, record: dict) -> Any:
        """Compute the enrichment value."""
        pass


class CalculateRule(EnrichmentRule):
    """Compute a value from an expression using record fields."""

    def __init__(self, target_field: str, expression: str):
        super().__init__(target_field)
        self.expression = expression

    def compute(self, record: dict) -> Any:
        # Convert string numeric values to actual numbers for expression evaluation
        eval_locals = {}
        for k, v in record.items():
            if isinstance(v, str):
                try:
                    # Try integer first, then float
                    if '.' in v:
                        eval_locals[k] = float(v)
                    else:
                        eval_locals[k] = int(v)
                except ValueError:
                    eval_locals[k] = v
            else:
                eval_locals[k] = v
        return eval(self.expression, {"__builtins__": {}}, eval_locals)


class LookupRule(EnrichmentRule):
    """Add data from an external lookup source."""

    def __init__(
        self,
        target_field: str,
        source: dict,
        key_field: str,
        value_fields: list[str] = None
    ):
        super().__init__(target_field)
        self.source = source
        self.key_field = key_field
        self.value_fields = value_fields or [target_field]

    def compute(self, record: dict) -> Any:
        key = record.get(self.key_field)
        if key in self.source:
            return self.source[key].get(self.target_field)
        return None


class DateExtractRule(EnrichmentRule):
    """Extract a component from a date/datetime field."""

    def __init__(self, target_field: str, source_field: str, part: str):
        super().__init__(target_field)
        self.source_field = source_field
        self.part = part

    def compute(self, record: dict) -> Any:
        import pandas as pd
        date_val = record.get(self.source_field)
        if date_val:
            dt = pd.to_datetime(date_val)
            return getattr(dt, self.part, None)
        return None


class CategoryMapRule(EnrichmentRule):
    """Map a numeric value to a category label based on ranges."""

    def __init__(
        self,
        target_field: str,
        source_field: str,
        ranges: list[tuple],
        labels: list[str]
    ):
        super().__init__(target_field)
        self.source_field = source_field
        self.ranges = ranges
        self.labels = labels

    def compute(self, record: dict) -> Any:
        value = record.get(self.source_field)
        if value is None:
            return None
        for i, (low, high) in enumerate(self.ranges):
            if low <= value <= high:
                return self.labels[i]
        if value >= self.ranges[-1][1]:
            return self.labels[-1]
        return None


class ConditionalRule(EnrichmentRule):
    """Apply value based on a condition."""

    def __init__(
        self,
        target_field: str,
        condition: str,
        true_value: Any,
        false_value: Any = None
    ):
        super().__init__(target_field)
        self.condition = condition
        self.true_value = true_value
        self.false_value = false_value

    def compute(self, record: dict) -> Any:
        try:
            result = eval(self.condition, {"__builtins__": {}}, record)
            return self.true_value if result else self.false_value
        except Exception:
            return self.false_value


class DeriveRule(EnrichmentRule):
    """Derive a value using a custom function."""

    def __init__(self, target_field: str, func: callable):
        super().__init__(target_field)
        self.func = func

    def compute(self, record: dict) -> Any:
        return self.func(record)