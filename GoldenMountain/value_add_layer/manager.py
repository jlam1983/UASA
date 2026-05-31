"""ValueAddManager - Factory/Manager for value-add operations with JSON I/O."""

from datetime import datetime
from typing import Any, Dict, List, Optional

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
from .transformer.transformer import DataTransformer
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
from .errors import ValueAddError


class ProcessingResult:
    """Container for processing results."""

    def __init__(self):
        self.metadata: Dict[str, Any] = {}
        self.records: List[dict] = []
        self.steps_completed: List[str] = []
        self.validation: Optional[ValidationResult] = None

    def to_json(self) -> dict:
        """Convert result to JSON-serializable dict."""
        result = {
            "metadata": {
                "source": "value_add_layer",
                "processed_at": datetime.utcnow().isoformat() + "Z",
                "steps_completed": self.steps_completed,
                "record_count": len(self.records),
            },
            "records": self.records,
        }
        if self.validation is not None:
            result["validation"] = {
                "valid": self.validation.is_valid,
                "error_count": self.validation.error_count,
                "warning_count": self.validation.warning_count,
                "errors": [
                    {"field": e.rule.field, "message": e.message}
                    for e in self.validation.errors
                ],
                "warnings": [
                    {"field": w.rule.field, "message": w.message}
                    for w in self.validation.warnings
                ],
            }
        return result


class ValueAddManager:
    """Factory/Manager for value-add operations.

    Provides a unified entry point for enrichment, transformation,
    validation, and aggregation using JSON input/output.
    """

    def __init__(self, config: Optional[dict] = None):
        self.enricher = DataEnricher()
        self.transformer = DataTransformer()
        self.validator = DataValidator()
        self.aggregator = DataAggregator()
        self.normalizer = Normalizer()
        self.encoder = CategoricalEncoder()

    def process(self, input_json: dict) -> dict:
        """Process input JSON through the value-add pipeline.

        Args:
            input_json: {
                "records": [...],
                "config": {
                    "enrichment": [...],
                    "transformation": [...],
                    "validation": [...],
                    "aggregation": {...}
                }
            }

        Returns:
            output_json: {
                "metadata": {...},
                "records": [...],
                "validation": {...}
            }
        """
        records = input_json.get("records", [])
        config = input_json.get("config", {})

        result = ProcessingResult()
        result.metadata["source"] = "value_add_layer"
        result.metadata["processed_at"] = datetime.utcnow().isoformat() + "Z"

        # Step 1: Enrichment
        if "enrichment" in config:
            enrichment_config = config["enrichment"]
            rules = self._build_enrichment_rules(enrichment_config)
            if rules:
                records = self.enricher.enrich(records, rules)
                result.steps_completed.append("enrichment")

        # Step 2: Transformation
        if "transformation" in config:
            for transform_config in config["transformation"]:
                strategy = transform_config.get("type", "normalize")
                records = self.transformer.transform(records, strategy, transform_config)
            result.steps_completed.append("transformation")

        # Step 3: Validation
        if "validation" in config:
            validation_config = config["validation"]
            rules = self._build_validation_rules(validation_config)
            self.validator.rules = rules
            validation_result = self.validator.validate(records)
            result.validation = validation_result
            result.steps_completed.append("validation")

        # Step 4: Aggregation
        if "aggregation" in config:
            agg_config = config["aggregation"]
            records = self.aggregator.aggregate(
                records,
                agg_config["group_by"],
                agg_config["aggregations"]
            )
            result.steps_completed.append("aggregation")

        result.metadata["record_count"] = len(records)
        result.metadata["steps_completed"] = result.steps_completed
        result.records = records

        return result.to_json()

    def _build_enrichment_rules(self, config: List[dict]) -> List[EnrichmentRule]:
        """Build enrichment rules from config list."""
        rules = []
        for rule_config in config:
            rule_type = rule_config.get("type")
            if rule_type == "calculate":
                rules.append(CalculateRule(
                    rule_config["target"],
                    rule_config["expression"]
                ))
            elif rule_type == "lookup":
                rules.append(LookupRule(
                    rule_config["target"],
                    rule_config["source"],
                    rule_config["key_field"],
                    rule_config.get("value_fields")
                ))
            elif rule_type == "date_extract":
                rules.append(DateExtractRule(
                    rule_config["target"],
                    rule_config["source"],
                    rule_config["part"]
                ))
            elif rule_type == "category_map":
                rules.append(CategoryMapRule(
                    rule_config["target"],
                    rule_config["source"],
                    rule_config["ranges"],
                    rule_config["labels"]
                ))
            elif rule_type == "conditional":
                rules.append(ConditionalRule(
                    rule_config["target"],
                    rule_config["condition"],
                    rule_config["true_value"],
                    rule_config.get("false_value")
                ))
            elif rule_type == "derive":
                rules.append(DeriveRule(
                    rule_config["target"],
                    rule_config["func"]
                ))
        return rules

    def _build_validation_rules(self, config: List[dict]) -> List[ValidationRule]:
        """Build validation rules from config list."""
        rules = []
        for rule_config in config:
            rule_type = rule_config.get("type")
            field = rule_config.get("field")
            if rule_type == "required":
                rules.append(RequiredRule(field))
            elif rule_type == "type":
                rules.append(TypeRule(field, rule_config.get("expected_type")))
            elif rule_type == "range":
                rules.append(RangeRule(field, rule_config.get("min"), rule_config.get("max")))
            elif rule_type == "pattern":
                rules.append(PatternRule(field, rule_config.get("pattern")))
            elif rule_type == "enum":
                rules.append(EnumRule(field, rule_config.get("allowed_values")))
            elif rule_type == "unique":
                rules.append(UniqueRule(field))
            elif rule_type == "custom":
                rules.append(CustomRule(
                    field,
                    rule_config.get("validator"),
                    rule_config.get("error_msg")
                ))
            elif rule_type == "cross_field":
                rules.append(CrossFieldRule(
                    field,
                    rule_config.get("field2"),
                    rule_config.get("validator")
                ))
        return rules

    # Common utility functions grouped together

    def normalize_fields(self, records: List[dict], fields: List[str], method: str = "min_max") -> List[dict]:
        """Normalize specified numeric fields in records."""
        return self.normalizer.normalize(records, fields, method)

    def encode_categorical(self, records: List[dict], field: str, method: str = "label") -> List[dict]:
        """Encode a categorical field."""
        return self.encoder.encode(records, field, method)

    def aggregate_simple(
        self,
        records: List[dict],
        group_by: str,
        agg_func: str,
        agg_field: str
    ) -> List[dict]:
        """Simple aggregation with single function and field."""
        return self.aggregator.aggregate(
            records,
            [group_by],
            {"result": f"{agg_func},{agg_field}"}
        )

    def validate_single(self, record: dict, rules: List[ValidationRule]) -> ValidationResult:
        """Validate a single record."""
        self.validator.rules = rules
        return self.validator.validate([record])