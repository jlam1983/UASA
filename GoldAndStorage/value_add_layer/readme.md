# Value Add Layer

## Overview

A modular data transformation layer that enriches, validates, and transforms raw data into value-added assets ready for storage and analysis. Supports multiple transformation strategies, validation rules, and enrichment operations.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Input Data                                     │
│                    { records: [...], metadata: {...} }                   │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Value Add Pipeline                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │   Enrich     │→ │  Transform   │→ │  Validate    │→ │  Aggregate │  │
│  │              │  │              │  │              │  │            │  │
│  │ • Calculate  │  │ • Normalize   │  │ • Schema     │  │ • Group    │  │
│  │ • Lookup     │  │ • Encode     │  │ • Range      │  │ • Summarize │  │
│  │ • Derive     │  │ • Reshape    │  │ • Pattern    │  │ • Statistic │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘  │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          Enriched Output                                 │
│                  { records: [...], metadata: {...} }                     │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Data Enricher

Adds computed fields, lookup values, and derived data to records.

```python
class DataEnricher:
    """Enriches records with calculated and lookup-based fields"""

    def enrich(
        self,
        records: list[dict],
        rules: list[EnrichmentRule],
        lookup_sources: dict[str, LookupSource] = None
    ) -> list[dict]:
        for record in records:
            for rule in rules:
                record[rule.target_field] = rule.compute(record)
        return records

    def enrich_with_lookups(
        self,
        records: list[dict],
        lookup_config: dict
    ) -> list[dict]:
        # Build lookup index
        index = self._build_lookup_index(
            lookup_config["source"],
            lookup_config["key_field"]
        )
        # Apply enrichments
        for record in records:
            lookup_key = record.get(lookup_config["lookup_key"])
            if lookup_key in index:
                record.update(index[lookup_key])
        return records
```

#### Enrichment Rule Types

| Rule Type | Description | Example |
|-----------|-------------|---------|
| **Calculate** | Compute from existing fields | `total = price * quantity` |
| **Lookup** | Add data from external source | `region_name` from postal code |
| **Derive** | Generate value via function | `full_name` = `first` + `last` |
| **DateExtract** | Pull date components | `year`, `month`, `day_of_week` |
| **CategoryMap** | Map values to categories | `age_group` from `age` range |
| **Conditional** | Apply based on condition | `tier` based on `spending` |

#### Enrichment Rule Implementation

```python
class EnrichmentRule(ABC):
    """Base class for enrichment rules"""

    @abstractmethod
    def compute(self, record: dict) -> any:
        """Compute the enrichment value"""
        pass

class CalculateRule(EnrichmentRule):
    def __init__(self, target_field: str, expression: str):
        self.target_field = target_field
        self.expression = expression

    def compute(self, record: dict) -> any:
        return eval(self.expression, {"__builtins__": {}}, record)

class LookupRule(EnrichmentRule):
    def __init__(
        self,
        target_field: str,
        source: dict,
        key_field: str,
        value_fields: list[str]
    ):
        self.target_field = target_field
        self.source = source
        self.key_field = key_field
        self.value_fields = value_fields

    def compute(self, record: dict) -> any:
        key = record.get(self.key_field)
        if key in self.source:
            return self.source[key].get(self.target_field)
        return None

class DateExtractRule(EnrichmentRule):
    def __init__(self, target_field: str, source_field: str, part: str):
        self.target_field = target_field
        self.source_field = source_field
        self.part = part  # year, month, day, hour, weekday, etc.

    def compute(self, record: dict) -> any:
        date_val = record.get(self.source_field)
        if date_val:
            dt = pd.to_datetime(date_val)
            return getattr(dt, self.part)
        return None

class CategoryMapRule(EnrichmentRule):
    def __init__(
        self,
        target_field: str,
        source_field: str,
        ranges: list[tuple],
        labels: list[str]
    ):
        self.target_field = target_field
        self.source_field = source_field
        self.ranges = ranges  # [(0, 18), (18, 30), (30, 60), (60, 100)]
        self.labels = labels  # ["child", "young_adult", "adult", "senior"]

    def compute(self, record: dict) -> any:
        value = record.get(self.source_field)
        for i, (low, high) in enumerate(self.ranges):
            if low <= value < high:
                return self.labels[i]
        return self.labels[-1] if value >= self.ranges[-1][1] else None
```

#### Usage Example

```python
from enricher import DataEnricher, CalculateRule, LookupRule, CategoryMapRule

enricher = DataEnricher()

# Define enrichment rules
rules = [
    CalculateRule("total_value", "quantity * unit_price"),
    CalculateRule("profit_margin", "(selling_price - cost) / cost * 100"),
    CategoryMapRule("age_group", "age", [(0, 18), (18, 35), (35, 55), (55, 100)],
                    ["minor", "young_adult", "adult", "senior"]),
]

# Load lookup data
region_lookup = {
    "1001": {"region": "North", "country": "USA"},
    "1002": {"region": "South", "country": "USA"},
    ...
}

rules.append(LookupRule("region", region_lookup, "postal_code", ["region", "country"]))

# Enrich records
enriched = enricher.enrich(records, rules)
```

---

### 2. Data Transformer

Applies normalization, encoding, and reshaping transformations.

```python
class DataTransformer:
    """Transforms data using various transformation strategies"""

    def transform(
        self,
        records: list[dict],
        strategy: str,
        config: dict = None
    ) -> list[dict]:
        strategies = {
            "normalize": self._normalize,
            "encode": self._encode_categorical,
            "reshape": self._reshape,
            "pivot": self._pivot,
            "filter": self._filter_records,
            "aggregate": self._aggregate,
        }
        return strategies[strategy](records, config or {})

    def _normalize(self, records: list[dict], config: dict) -> list[dict]:
        """Scale numeric values to 0-1 range"""
        pass

    def _encode_categorical(self, records: list[dict], config: dict) -> list[dict]:
        """Encode categorical values as numbers"""
        pass
```

#### Transformation Types

| Transform | Description | Use Case |
|-----------|-------------|----------|
| **Normalize** | Scale numeric values | ML preprocessing |
| **Standardize** | Mean=0, std=1 | Statistical analysis |
| **Encode** | Categorical to numeric | ML models |
| **OneHot** | Binary columns per category | ML models |
| **Reshape** | Change data structure | Data restructuring |
| **Pivot** | Rotate rows to columns | Cross-tabulation |
| **Melt** | Columns to rows | Unpivot data |
| **Cast** | Change data types | Type consistency |

#### Normalization Strategies

```python
class Normalizer:
    """Normalize numeric values"""

    def min_max_scale(self, values: list[float], min_val=None, max_val=None) -> list[float]:
        min_val = min_val or min(values)
        max_val = max_val or max(values)
        range_val = max_val - min_val
        if range_val == 0:
            return [0.5] * len(values)
        return [(v - min_val) / range_val for v in values]

    def z_score_scale(self, values: list[float]) -> list[float]:
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std = variance ** 0.5
        if std == 0:
            return [0.0] * len(values)
        return [(v - mean) / std for v in values]

    def robust_scale(self, values: list[float]) -> list[float]:
        median = sorted(values)[len(values) // 2]
        q1 = sorted(values)[len(values) // 4]
        q3 = sorted(values)[len(values) // 4 * 3]
        iqr = q3 - q1
        if iqr == 0:
            return [0.0] * len(values)
        return [(v - median) / iqr for v in values]
```

#### Categorical Encoding

```python
class CategoricalEncoder:
    """Encode categorical variables"""

    def label_encode(self, values: list[str]) -> list[int]:
        unique = list(set(values))
        return [unique.index(v) for v in values]

    def one_hot_encode(self, records: list[dict], field: str) -> list[dict]:
        unique_values = sorted(set(r[field] for r in records))
        result = []
        for record in records:
            encoded = dict(record)
            for val in unique_values:
                encoded[f"{field}_{val}"] = 1 if record[field] == val else 0
            result.append(encoded)
        return result

    def target_encode(self, records: list[dict], category_field: str, target_field: str) -> dict:
        """Encode categories by mean target value"""
        category_stats = {}
        for record in records:
            cat = record[category_field]
            target = record[target_field]
            if cat not in category_stats:
                category_stats[cat] = {"sum": 0, "count": 0}
            category_stats[cat]["sum"] += target
            category_stats[cat]["count"] += 1
        return {cat: stats["sum"] / stats["count"] for cat, stats in category_stats.items()}
```

#### Reshape Operations

```python
class DataReshaper:
    """Reshape data structure"""

    def pivot(self, records: list[dict], index: str, columns: str, values: str) -> list[dict]:
        """Pivot table: unique index+columns combinations become rows"""
        pivot_map = {}
        for record in records:
            idx = record[index]
            col = record[columns]
            val = record[values]
            if idx not in pivot_map:
                pivot_map[idx] = {index: idx}
            pivot_map[idx][col] = val
        return list(pivot_map.values())

    def melt(self, records: list[dict], id_vars: list[str], value_vars: list[str]) -> list[dict]:
        """Unpivot: convert columns to rows"""
        result = []
        for record in records:
            base = {k: record[k] for k in id_vars}
            for var in value_vars:
                new_row = dict(base)
                new_row["variable"] = var
                new_row["value"] = record[var]
                result.append(new_row)
        return result

    def nest(self, records: list[dict], group_by: str, nest_fields: list[str]) -> list[dict]:
        """Nest specified fields under a group"""
        grouped = {}
        for record in records:
            key = record[group_by]
            if key not in grouped:
                grouped[key] = []
            grouped[key].append({f: record[f] for f in nest_fields})
        return [{"key": k, "items": v} for k, v in grouped.items()]
```

---

### 3. Data Validator

Validates records against schema and business rules.

```python
class DataValidator:
    """Validates data against defined rules"""

    def __init__(self, rules: list[ValidationRule] = None):
        self.rules = rules or []

    def validate(self, records: list[dict]) -> ValidationResult:
        errors = []
        warnings = []
        for i, record in enumerate(records):
            for rule in self.rules:
                result = rule.check(record)
                if result.is_error:
                    errors.append(ValidationError(record, rule, result.message))
                elif result.is_warning:
                    warnings.append(ValidationWarning(record, rule, result.message))
        return ValidationResult(
            valid=len(errors) == 0,
            error_count=len(errors),
            warning_count=len(warnings),
            errors=errors,
            warnings=warnings
        )

    def add_rule(self, rule: ValidationRule) -> None:
        self.rules.append(rule)

    def remove_rule(self, rule_name: str) -> None:
        self.rules = [r for r in self.rules if r.name != rule_name]
```

#### Validation Rule Types

| Rule | Description | Example |
|------|-------------|---------|
| **Required** | Field must exist and be non-empty | `required("email")` |
| **Type** | Field must be specific type | `type("age", int)` |
| **Range** | Numeric value within bounds | `range("price", min=0, max=10000)` |
| **Pattern** | String matches regex | `pattern("phone", r"^\d{3}-\d{4}$")` |
| **Enum** | Value in allowed list | `enum("status", ["active", "pending"])` |
| **Custom** | User-defined validation | `custom("discount", lambda x: x < 1.0)` |
| **CrossField** | Multiple fields valid together | `cross_field("start", "end", lambda s, e: s < e)` |
| **Unique** | No duplicate values | `unique("email")` |

#### Validation Rule Implementation

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable

@dataclass
class ValidationResult:
    is_valid: bool
    is_error: bool = False
    is_warning: bool = False
    message: str = ""

class ValidationRule(ABC):
    def __init__(self, name: str, field: str):
        self.name = name
        self.field = field

    @abstractmethod
    def check(self, record: dict) -> ValidationResult:
        pass

class RequiredRule(ValidationRule):
    def check(self, record: dict) -> ValidationResult:
        if self.field not in record:
            return ValidationResult(False, is_error=True, message=f"Missing required field: {self.field}")
        if record[self.field] is None or record[self.field] == "":
            return ValidationResult(False, is_error=True, message=f"Field cannot be empty: {self.field}")
        return ValidationResult(True)

class TypeRule(ValidationRule):
    def __init__(self, field: str, expected_type: type):
        super().__init__(f"type_{field}", field)
        self.expected_type = expected_type

    def check(self, record: dict) -> ValidationResult:
        if self.field not in record:
            return ValidationResult(True)  # Not required, skip
        value = record[self.field]
        if value is None:
            return ValidationResult(True)
        if not isinstance(value, self.expected_type):
            return ValidationResult(
                False, is_error=True,
                message=f"Field {self.field} must be {self.expected_type.__name__}, got {type(value).__name__}"
            )
        return ValidationResult(True)

class RangeRule(ValidationRule):
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
        if self.min_val is not None and value < self.min_val:
            return ValidationResult(False, is_error=True, message=f"{self.field} below minimum: {self.min_val}")
        if self.max_val is not None and value > self.max_val:
            return ValidationResult(False, is_error=True, message=f"{self.field} above maximum: {self.max_val}")
        return ValidationResult(True)

class PatternRule(ValidationRule):
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
            return ValidationResult(False, is_error=True, message=f"{self.field} does not match pattern")
        return ValidationResult(True)

class EnumRule(ValidationRule):
    def __init__(self, field: str, allowed_values: list[Any]):
        super().__init__(f"enum_{field}", field)
        self.allowed_values = allowed_values

    def check(self, record: dict) -> ValidationResult:
        if self.field not in record:
            return ValidationResult(True)
        value = record[self.field]
        if value is None:
            return ValidationResult(True)
        if value not in self.allowed_values:
            return ValidationResult(False, is_error=True, message=f"{self.field} must be one of {self.allowed_values}")
        return ValidationResult(True)

class CustomRule(ValidationRule):
    def __init__(self, field: str, validator: Callable[[Any], bool], error_msg: str = None):
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
            return ValidationResult(False, is_error=True, message=f"{self.error_msg}")
        return ValidationResult(True)
```

#### Usage Example

```python
from validator import DataValidator, RequiredRule, TypeRule, RangeRule, PatternRule, EnumRule

validator = DataValidator()

# Define validation rules
validator.add_rule(RequiredRule("id"))
validator.add_rule(TypeRule("age", int))
validator.add_rule(RangeRule("age", min_val=0, max_val=150))
validator.add_rule(TypeRule("price", (int, float)))
validator.add_rule(RangeRule("price", min_val=0))
validator.add_rule(PatternRule("email", r"^[\w.-]+@[\w.-]+\.\w+$"))
validator.add_rule(EnumRule("status", ["active", "pending", "completed", "cancelled"]))

# Validate records
result = validator.validate(records)

if result.valid:
    print("All records are valid")
else:
    print(f"Found {result.error_count} errors:")
    for error in result.errors:
        print(f"  - Record {error.record.get('id', 'unknown')}: {error.message}")

if result.warning_count > 0:
    print(f"Warnings: {result.warning_count}")
```

---

### 4. Data Aggregator

Groups and summarizes data to produce aggregated datasets.

```python
class DataAggregator:
    """Aggregates data using various aggregation functions"""

    def aggregate(
        self,
        records: list[dict],
        group_by: list[str],
        aggregations: dict[str, str | list[str]]
    ) -> list[dict]:
        """
        Aggregate records by grouping fields.

        Args:
            records: Input records
            group_by: Fields to group by
            aggregations: {output_field: aggregation_function}
                          e.g., {"total": "sum", "count": "count", "avg": "mean"}

        Returns:
            Aggregated records
        """
        grouped = self._group_records(records, group_by)
        results = []
        for key, group_records in grouped.items():
            result = dict(zip(group_by, key)) if isinstance(key, tuple) else {group_by[0]: key}
            for field, agg_func in aggregations.items():
                result[field] = self._apply_aggregation(group_records, agg_func)
            results.append(result)
        return results

    def _group_records(self, records: list[dict], group_by: list[str]) -> dict:
        grouped = {}
        for record in records:
            key = tuple(record.get(f) for f in group_by)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(record)
        return grouped

    def _apply_aggregation(self, records: list[dict], agg_func: str) -> any:
        func_map = {
            "sum": lambda r, f: sum(r.get(f, 0) for r in records),
            "count": lambda r, f: len(records),
            "mean": lambda r, f: sum(r.get(f, 0) for r in records) / len(records),
            "min": lambda r, f: min((r.get(f) for r in records if r.get(f) is not None), default=None),
            "max": lambda r, f: max((r.get(f) for r in records if r.get(f) is not None), default=None),
            "avg": lambda r, f: sum(r.get(f, 0) for r in records) / len(records),
            "std": lambda r, f: self._stddev([r.get(f) for r in records]),
            "first": lambda r, f: records[0].get(f) if records else None,
            "last": lambda r, f: records[-1].get(f) if records else None,
            "list": lambda r, f: [r.get(f) for r in records if f in r],
        }
        # Handle both "field" and "field, field2" formats
        if "," in agg_func:
            agg_func, field = agg_func.split(",", 1)
            agg_func = agg_func.strip()
            field = field.strip()
        else:
            field = None  # Will be determined by context
        return func_map.get(agg_func, lambda r, f: None)(records, None)
```

#### Aggregation Functions

| Function | Description | Input Type |
|----------|-------------|------------|
| **sum** | Sum of values | numeric |
| **count** | Number of records | any |
| **mean** | Average value | numeric |
| **avg** | Alias for mean | numeric |
| **min** | Minimum value | numeric |
| **max** | Maximum value | numeric |
| **std** | Standard deviation | numeric |
| **first** | First value | any |
| **last** | Last value | any |
| **list** | List of all values | any |
| **median** | Median value | numeric |
| **mode** | Most common value | any |

#### Aggregation Usage Example

```python
from aggregator import DataAggregator

agg = DataAggregator()

# Simple aggregation
sales_by_region = agg.aggregate(sales_records,
    group_by=["region"],
    aggregations={
        "total_sales": "sum,amount",
        "order_count": "count",
        "avg_order_value": "mean,amount"
    }
)

# Multi-level grouping
sales_by_region_product = agg.aggregate(sales_records,
    group_by=["region", "product_category"],
    aggregations={
        "total_sales": "sum,amount",
        "unique_customers": "count",
        "avg_discount": "mean,discount"
    }
)

# Time-based aggregation
monthly_sales = agg.aggregate(sales_records,
    group_by=["year", "month"],
    aggregations={
        "daily_avg": "mean,daily_sales",
        "peak_day": "max,daily_sales",
        "total_revenue": "sum,amount"
    }
)
```

---

## Value Add Pipeline

Combines enrichment, transformation, validation, and aggregation into a single pipeline.

```python
class ValueAddPipeline:
    """Complete value-add processing pipeline"""

    def __init__(self):
        self.enricher = DataEnricher()
        self.transformer = DataTransformer()
        self.validator = DataValidator()
        self.aggregator = DataAggregator()

    def process(
        self,
        records: list[dict],
        enrichment_rules: list[EnrichmentRule] = None,
        transformations: list[tuple[str, dict]] = None,
        validation_rules: list[ValidationRule] = None,
        aggregation_config: dict = None
    ) -> ProcessingResult:
        """
        Run records through the full value-add pipeline.

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
            validation_result = self.validator.validate(result.records)
            result.validation = validation_result
            if not validation_result.valid:
                result.errors.extend(validation_result.errors)
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

@dataclass
class ProcessingResult:
    records: list[dict]
    steps_completed: list[str] = field(default_factory=list)
    validation: ValidationResult = None
    errors: list[ValidationError] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0
```

#### Pipeline Usage Example

```python
from pipeline import ValueAddPipeline

pipeline = ValueAddPipeline()

# Configure pipeline
enrichment_rules = [
    CalculateRule("total_value", "quantity * unit_price"),
    CategoryMapRule("age_group", "age", [(0, 18), (18, 35), (35, 55), (55, 100)],
                    ["minor", "young_adult", "adult", "senior"]),
]

transformations = [
    ("normalize", {"fields": ["price", "quantity"], "method": "min_max"}),
    ("encode", {"field": "status", "method": "label"})
]

validation_rules = [
    RequiredRule("id"),
    TypeRule("total_value", (int, float)),
    RangeRule("total_value", min_val=0),
]

# Process data
result = pipeline.process(
    records=input_records,
    enrichment_rules=enrichment_rules,
    transformations=transformations,
    validation_rules=validation_rules
)

if result.success:
    print(f"Successfully processed {len(result.records)} records")
    print(f"Steps: {' -> '.join(result.steps_completed)}")
else:
    print(f"Processing completed with {len(result.errors)} errors")
```

---

## Error Handling

```python
class ValueAddError(Exception):
    """Base exception for value-add layer errors"""
    pass

class EnrichmentError(ValueAddError):
    """Failed during enrichment"""
    pass

class TransformationError(ValueAddError):
    """Failed during transformation"""
    pass

class ValidationError(ValueAddError):
    """Data validation failed"""
    pass

class AggregationError(ValueAddError):
    """Failed during aggregation"""
    pass

# Error handling in pipeline
try:
    result = pipeline.process(records, rules, transforms, validators)
except EnrichmentError as e:
    logger.error(f"Enrichment failed: {e}")
    # Handle enrichment failure
except TransformationError as e:
    logger.error(f"Transformation failed: {e}")
    # Handle transformation failure
except ValidationError as e:
    logger.error(f"Validation failed: {e}")
    # Handle validation failure (may be non-fatal)
except AggregationError as e:
    logger.error(f"Aggregation failed: {e}")
    # Handle aggregation failure
```

---

## Configuration

```yaml
# config/value_add.yaml
enrichment:
  rules:
    - type: calculate
      target: total_value
      expression: "quantity * unit_price"
    - type: category_map
      target: age_group
      source: age
      ranges:
        - [0, 18]
        - [18, 35]
        - [35, 55]
        - [55, 150]
      labels:
        - minor
        - young_adult
        - adult
        - senior

transformation:
  normalize:
    fields:
      - price
      - quantity
    method: min_max

  encode:
    - field: status
      method: label
    - field: category
      method: one_hot

validation:
  rules:
    - field: id
      type: required
    - field: price
      type: range
      min: 0
      max: 100000
    - field: email
      type: pattern
      pattern: "^[\w.-]+@[\w.-]+\.\w+$"

aggregation:
  group_by:
    - region
    - product_category
  aggregations:
    total_sales: sum,amount
    order_count: count
    avg_value: mean,amount
```

---

## Project Structure

```
value_add_layer/
├── __init__.py
├── enricher/
│   ├── __init__.py
│   ├── enricher.py        # Main enricher class
│   └── rules.py            # Enrichment rule implementations
├── transformer/
│   ├── __init__.py
│   ├── transformer.py      # Main transformer class
│   ├── normalizer.py       # Normalization strategies
│   └── encoder.py          # Categorical encoding
├── validator/
│   ├── __init__.py
│   ├── validator.py        # Main validator class
│   └── rules.py            # Validation rule implementations
├── aggregator/
│   ├── __init__.py
│   └── aggregator.py       # Aggregation functions
├── pipeline/
│   ├── __init__.py
│   └── pipeline.py         # Value-add pipeline orchestration
├── main.py
└── config.yaml
```