# Value Add Layer

## Overview

A modular data transformation layer that enriches, validates, and transforms raw data into value-added assets ready for storage and analysis. All input/output uses **JSON format**.

---

## Architecture

```
Input JSON → ValueAddManager → Output JSON
                    │
                    ▼
        ┌───────────────────────┐
        │   Pipeline Steps      │
        │  Enrich → Transform   │
        │  → Validate → Aggregate│
        └───────────────────────┘
```

---

## Input/Output Format

All operations use standardized JSON input and output:

```json
// Input
{
  "records": [
    {"id": 1, "name": "Alice", "price": 100, "quantity": 2},
    {"id": 2, "name": "Bob", "price": 50, "quantity": 3}
  ]
}

// Output
{
  "metadata": {
    "source": "value_add_layer",
    "steps_completed": ["enrichment", "transformation"],
    "record_count": 2,
    "processed_at": "2024-01-01T00:00:00Z"
  },
  "records": [
    {"id": 1, "name": "Alice", "price": 100, "quantity": 2, "total_value": 200},
    {"id": 2, "name": "Bob", "price": 50, "quantity": 3, "total_value": 150}
  ],
  "validation": {
    "valid": true,
    "error_count": 0,
    "warning_count": 0,
    "errors": [],
    "warnings": []
  }
}
```

---

## ValueAddManager (Factory)

The main entry point that orchestrates all operations.

### ProcessingResult

```python
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
                    {"field": e.field, "message": e.message}
                    for e in self.validation.errors
                ],
                "warnings": [
                    {"field": w.field, "message": w.message}
                    for w in self.validation.warnings
                ],
            }
        return result
```

### ValueAddManager

```python
class ValueAddManager:
    """Factory/Manager for value-add operations."""

    def __init__(self, config: Optional[dict] = None):
        self.enricher = DataEnricher()
        self.transformer = DataTransformer()
        self.validator = DataValidator()
        self.aggregator = DataAggregator()
        self.normalizer = Normalizer()
        self.encoder = CategoricalEncoder()

    def process(self, input_json: dict) -> dict:
        """Process input JSON through the value-add pipeline."""
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

    # Common utility functions

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
```

---

## Usage Example

```python
from value_add_layer import ValueAddManager

manager = ValueAddManager()

# Input JSON
input_data = {
    "records": [
        {"id": 1, "name": "Alice", "age": 25, "price": 100, "quantity": 2},
        {"id": 2, "name": "Bob", "age": 35, "price": 50, "quantity": 3}
    ],
    "config": {
        "enrichment": [
            {"type": "calculate", "target": "total_value", "expression": "price * quantity"},
            {"type": "category_map", "target": "age_group", "source": "age",
             "ranges": [[0, 18], [18, 35], [35, 55], [55, 150]],
             "labels": ["minor", "young_adult", "adult", "senior"]}
        ],
        "transformation": [
            {"type": "normalize", "fields": ["price", "quantity"], "method": "min_max"}
        ],
        "validation": [
            {"type": "required", "field": "id"},
            {"type": "range", "field": "price", "min": 0, "max": 10000}
        ],
        "aggregation": {
            "group_by": ["age_group"],
            "aggregations": {
                "total_sales": "sum,total_value",
                "count": "count",
                "avg_price": "mean,price"
            }
        }
    }
}

# Process
output = manager.process(input_data)

print(output["metadata"]["record_count"], "records processed")
print(output["records"])
```

---

## Components

### 1. DataEnricher

Adds computed fields to records.

```python
class DataEnricher:
    def enrich(self, records: list[dict], rules: list) -> list[dict]:
        for record in records:
            for rule in rules:
                record[rule.target_field] = rule.compute(record)
        return records
```

**Supported Rules:** `calculate`, `lookup`, `derive`, `date_extract`, `category_map`, `conditional`

### 2. DataTransformer

Applies normalization, encoding, and reshaping.

```python
class DataTransformer:
    def transform(self, records: list[dict], strategy: str, config: dict) -> list[dict]:
        strategies = {
            "normalize": self._normalize,
            "encode": self._encode_categorical,
            "reshape": self._reshape,
        }
        return strategies[strategy](records, config)
```

**Supported Transforms:** `normalize`, `standardize`, `encode`, `one_hot`, `reshape`, `pivot`, `melt`

### 3. DataValidator

Validates records against rules.

```python
class DataValidator:
    def validate(self, records: list[dict]) -> ValidationResult:
        errors = []
        warnings = []
        for record in records:
            for rule in self.rules:
                result = rule.check(record)
                if result.is_error:
                    errors.append(ValidationError(record, rule, result.message))
        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)
```

**Supported Rules:** `required`, `type`, `range`, `pattern`, `enum`, `unique`, `custom`

### 4. DataAggregator

Groups and summarizes data.

```python
class DataAggregator:
    def aggregate(self, records: list[dict], group_by: list, aggregations: dict) -> list[dict]:
        # Group records and apply aggregation functions
```

**Supported Functions:** `sum`, `count`, `mean`, `avg`, `min`, `max`, `std`, `first`, `last`, `list`, `median`, `mode`

---

## Project Structure

```
value_add_layer/
├── __init__.py
├── main.py                 # CLI entry point
├── manager.py              # ValueAddManager (factory)
├── errors.py               # Custom exceptions
├── enricher/
│   ├── __init__.py
│   ├── enricher.py         # DataEnricher class
│   └── rules.py            # Enrichment rule implementations
├── transformer/
│   ├── __init__.py
│   ├── transformer.py      # DataTransformer class
│   ├── normalizer.py       # Normalization strategies
│   └── encoder.py          # Categorical encoding
├── validator/
│   ├── __init__.py
│   ├── validator.py        # DataValidator class
│   └── rules.py            # Validation rule implementations
├── aggregator/
│   ├── __init__.py
│   └── aggregator.py        # Aggregation functions
└── pipeline/
    ├── __init__.py
    └── pipeline.py         # Pipeline orchestration
```

---

## Configuration

All configuration is done via the input JSON `config` section. No external YAML required.

```json
{
  "records": [...],
  "config": {
    "enrichment": [...],
    "transformation": [...],
    "validation": [...],
    "aggregation": {...}
  }
}
```