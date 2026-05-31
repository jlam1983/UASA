"""DataValidator - Validates records against schema and business rules."""

from typing import List, Optional

from .rules import (
    ValidationRule,
    ValidationResult,
    ValidationError,
    ValidationWarning,
)


class DataValidator:
    """Validates data against defined rules."""

    def __init__(self, rules: Optional[List[ValidationRule]] = None):
        self.rules = rules or []

    def validate(self, records: List[dict]) -> ValidationResult:
        """Validate all records against the rules."""
        errors: List[ValidationError] = []
        warnings: List[ValidationWarning] = []

        for i, record in enumerate(records):
            for rule in self.rules:
                result = rule.check(record)
                if result.is_error:
                    errors.append(ValidationError(record, rule, result.message))
                elif result.is_warning:
                    warnings.append(ValidationWarning(record, rule, result.message))

        return ValidationResult(
            is_valid=len(errors) == 0,
            is_error=False,
            is_warning=False,
            message="",
            error_count=len(errors),
            warning_count=len(warnings),
            errors=errors,
            warnings=warnings
        )

    def add_rule(self, rule: ValidationRule) -> None:
        """Add a validation rule."""
        self.rules.append(rule)

    def remove_rule(self, rule_name: str) -> None:
        """Remove a validation rule by name."""
        self.rules = [r for r in self.rules if r.name != rule_name]

    def validate_with_details(self, records: List[dict]) -> dict:
        """Validate records and return detailed results."""
        errors = []
        warnings = []

        for record in records:
            for rule in self.rules:
                result = rule.check(record)
                if result.is_error:
                    errors.append({
                        "field": rule.field,
                        "message": result.message,
                        "record": record
                    })
                elif result.is_warning:
                    warnings.append({
                        "field": rule.field,
                        "message": result.message,
                        "record": record
                    })

        return {
            "valid": len(errors) == 0,
            "error_count": len(errors),
            "warning_count": len(warnings),
            "errors": errors,
            "warnings": warnings
        }