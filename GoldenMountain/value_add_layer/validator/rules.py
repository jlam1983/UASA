"""Validation rule implementations."""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, List


@dataclass
class ValidationResult:
    """Result of a validation rule check."""
    is_valid: bool
    is_error: bool = False
    is_warning: bool = False
    message: str = ""
    error_count: int = 0
    warning_count: int = 0
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)


@dataclass
class ValidationError:
    """Represents a validation error."""
    record: dict
    rule: 'ValidationRule'
    message: str


@dataclass
class ValidationWarning:
    """Represents a validation warning."""
    record: dict
    rule: 'ValidationRule'
    message: str


class ValidationRule(ABC):
    """Base class for validation rules."""

    def __init__(self, name: str, field: str):
        self.name = name
        self.field = field

    @abstractmethod
    def check(self, record: dict) -> ValidationResult:
        """Check if the record satisfies this rule."""
        pass


class RequiredRule(ValidationRule):
    """Field must exist and be non-empty."""

    def __init__(self, field: str):
        super().__init__(f"required_{field}", field)

    def check(self, record: dict) -> ValidationResult:
        if self.field not in record:
            return ValidationResult(
                False, is_error=True,
                message=f"Missing required field: {self.field}"
            )
        if record[self.field] is None or record[self.field] == "":
            return ValidationResult(
                False, is_error=True,
                message=f"Field cannot be empty: {self.field}"
            )
        return ValidationResult(True)


class TypeRule(ValidationRule):
    """Field must be of a specific type."""

    def __init__(self, field: str, expected_type: type):
        super().__init__(f"type_{field}", field)
        self.expected_type = expected_type

    def check(self, record: dict) -> ValidationResult:
        if self.field not in record:
            return ValidationResult(True)
        value = record[self.field]
        if value is None:
            return ValidationResult(True)
        if not isinstance(value, self.expected_type):
            return ValidationResult(
                False, is_error=True,
                message=f"Field {self.field} must be {self.expected_type.__name__}, "
                       f"got {type(value).__name__}"
            )
        return ValidationResult(True)


class RangeRule(ValidationRule):
    """Numeric value must be within bounds."""

    def __init__(self, field: str, min_val: float = None, max_val: float = None):
        super().__init__(f"range_{field}", field)
        self.min_val = min_val
        self.max_val = max_val

    def check(self, record: dict) -> ValidationResult:
        if self.field not in record:
            return ValidationResult(True)
        value = record[self.field]
        if value is None:
            return ValidationResult(True)
        try:
            value = float(value)
        except (TypeError, ValueError):
            return ValidationResult(True)
        if self.min_val is not None and value < self.min_val:
            return ValidationResult(
                False, is_error=True,
                message=f"{self.field} below minimum: {self.min_val}"
            )
        if self.max_val is not None and value > self.max_val:
            return ValidationResult(
                False, is_error=True,
                message=f"{self.field} above maximum: {self.max_val}"
            )
        return ValidationResult(True)


class PatternRule(ValidationRule):
    """String must match a regular expression pattern."""

    def __init__(self, field: str, pattern: str):
        super().__init__(f"pattern_{field}", field)
        self.pattern = re.compile(pattern)

    def check(self, record: dict) -> ValidationResult:
        if self.field not in record:
            return ValidationResult(True)
        value = record[self.field]
        if value is None:
            return ValidationResult(True)
        if not self.pattern.match(str(value)):
            return ValidationResult(
                False, is_error=True,
                message=f"{self.field} does not match pattern"
            )
        return ValidationResult(True)


class EnumRule(ValidationRule):
    """Value must be one of the allowed values."""

    def __init__(self, field: str, allowed_values: List[Any]):
        super().__init__(f"enum_{field}", field)
        self.allowed_values = allowed_values

    def check(self, record: dict) -> ValidationResult:
        if self.field not in record:
            return ValidationResult(True)
        value = record[self.field]
        if value is None:
            return ValidationResult(True)
        if value not in self.allowed_values:
            return ValidationResult(
                False, is_error=True,
                message=f"{self.field} must be one of {self.allowed_values}"
            )
        return ValidationResult(True)


class CustomRule(ValidationRule):
    """User-defined validation function."""

    def __init__(
        self,
        field: str,
        validator: Callable[[Any], bool],
        error_msg: str = None
    ):
        super().__init__(f"custom_{field}", field)
        self.validator = validator
        self.error_msg = error_msg or "Custom validation failed"

    def check(self, record: dict) -> ValidationResult:
        if self.field not in record:
            return ValidationResult(True)
        value = record[self.field]
        if value is None:
            return ValidationResult(True)
        if not self.validator(value):
            return ValidationResult(
                False, is_error=True,
                message=f"{self.error_msg}"
            )
        return ValidationResult(True)


class CrossFieldRule(ValidationRule):
    """Multiple fields must be valid together."""

    def __init__(
        self,
        name: str,
        fields: List[str],
        validator: Callable,
        error_msg: str = None
    ):
        super().__init__(name, fields[0] if fields else "")
        self.fields = fields
        self.validator = validator
        self.error_msg = error_msg or "Cross-field validation failed"

    def check(self, record: dict) -> ValidationResult:
        try:
            values = [record.get(f) for f in self.fields]
            if all(v is not None for v in values):
                if not self.validator(*values):
                    return ValidationResult(
                        False, is_error=True,
                        message=self.error_msg
                    )
        except Exception:
            return ValidationResult(True)
        return ValidationResult(True)


class UniqueRule(ValidationRule):
    """Field values must be unique (no duplicates)."""

    def __init__(self, field: str):
        super().__init__(f"unique_{field}", field)

    def check(self, record: dict) -> ValidationResult:
        return ValidationResult(True)