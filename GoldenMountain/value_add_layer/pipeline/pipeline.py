"""ValueAddPipeline - Orchestrates enrichment, transformation, validation, and aggregation."""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any

from ..enricher.enricher import DataEnricher
from ..enricher.rules import EnrichmentRule
from ..transformer.transformer import DataTransformer
from ..validator.validator import DataValidator
from ..validator.rules import ValidationRule, ValidationResult
from ..aggregator.aggregator import DataAggregator


@dataclass
class ProcessingResult:
    """Result of a value-add pipeline execution."""
    records: List[dict]
    steps_completed: List[str] = field(default_factory=list)
    validation: Optional[ValidationResult] = None
    errors: List[dict] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """Check if processing was successful (no errors)."""
        return len(self.errors) == 0


class ValueAddPipeline:
    """Complete value-add processing pipeline."""

    def __init__(self):
        self.enricher = DataEnricher()
        self.transformer = DataTransformer()
        self.validator = DataValidator()
        self.aggregator = DataAggregator()

    def process(
        self,
        records: List[dict],
        enrichment_rules: Optional[List[EnrichmentRule]] = None,
        transformations: Optional[List[Tuple[str, dict]]] = None,
        validation_rules: Optional[List[ValidationRule]] = None,
        aggregation_config: Optional[Dict] = None
    ) -> ProcessingResult:
        """
        Run records through the full value-add pipeline.

        Args:
            records: Input records
            enrichment_rules: List of enrichment rules to apply
            transformations: List of (transform_type, config) tuples
            validation_rules: List of validation rules
            aggregation_config: Dict with "group_by" and "aggregations"

        Returns:
            ProcessingResult with processed records and metadata
        """
        result = ProcessingResult(records=records)

        # Step 1: Enrich
        if enrichment_rules:
            result.records = self.enricher.enrich(result.records, enrichment_rules)
            result.steps_completed.append("enrichment")

        # Step 2: Transform
        if transformations:
            for transform_type, config in transformations:
                result.records = self.transformer.transform(result.records, transform_type, config)
            result.steps_completed.append("transformation")

        # Step 3: Validate
        if validation_rules:
            self.validator.rules = validation_rules
            validation_result = self.validator.validate_with_details(result.records)
            result.validation = ValidationResult(
                is_valid=validation_result["valid"],
                is_error=False,
                is_warning=False,
                message=""
            )
            if not validation_result["valid"]:
                result.errors.extend(validation_result["errors"])
            result.steps_completed.append("validation")

        # Step 4: Aggregate (if configured)
        if aggregation_config:
            result.records = self.aggregator.aggregate(
                result.records,
                aggregation_config["group_by"],
                aggregation_config["aggregations"]
            )
            result.steps_completed.append("aggregation")

        return result

    def enrich(
        self,
        records: List[dict],
        rules: List[EnrichmentRule]
    ) -> List[dict]:
        """Apply enrichment rules to records."""
        return self.enricher.enrich(records, rules)

    def transform(
        self,
        records: List[dict],
        strategy: str,
        config: Optional[dict] = None
    ) -> List[dict]:
        """Apply a transformation strategy to records."""
        return self.transformer.transform(records, strategy, config)

    def validate(
        self,
        records: List[dict],
        rules: List[ValidationRule]
    ) -> dict:
        """Validate records against rules."""
        self.validator.rules = rules
        return self.validator.validate_with_details(records)

    def aggregate(
        self,
        records: List[dict],
        group_by: List[str],
        aggregations: Dict[str, str]
    ) -> List[dict]:
        """Aggregate records by grouping fields."""
        return self.aggregator.aggregate(records, group_by, aggregations)