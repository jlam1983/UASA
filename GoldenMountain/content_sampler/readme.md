# Content Sampler

## Overview

A module for sampling data content with capabilities for schema analysis, standardization, and noise labeling. Designed to help users understand data structure and prepare clean datasets for analysis.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                           Input Data                                 │
│              (JSON, CSV, XML, Database Tables, API Response)         │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│                        Content Sampler                               │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  User Input: Sample Size, Strategy, Schema Analysis Options    │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                 │                                    │
│  ┌─────────────────────────────┼─────────────────────────────┐       │
│  │         Sampling Strategies │                             │       │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │       │
│  │  │ Random  │ │Stratified││Systematic││ Cluster │ ...      │       │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘          │       │
│  └─────────────────────────────┼─────────────────────────────┘       │
└────────────────────────────────┼─────────────────────────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────────┐
        ▼                        ▼                            ▼
┌───────────────┐    ┌───────────────────────┐    ┌───────────────────┐
│  Schema       │    │  Standardized Schema  │    │  Noise Labeling   │
│  Analyzer     │    │  Generator            │    │  Interface        │
└───────┬───────┘    └───────────┬───────────┘    └───────┬───────────┘
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────┐    ┌───────────────────────┐    ┌───────────────────┐
│ Field Types   │    │ Optimized JSON Schema │    │ Labeled Noise     │
│ Distribution  │    │ (SQL Type Mapping)    │    │ Records/Fields    │
│ Cardinality   │    │ Constraints           │    │ Confidence Score  │
└───────────────┘    └───────────────────────┘    └───────────────────┘
```

---

## Features

### 1. Configurable Sample Size

```python
# User specifies exact number of records to sample
sample_size = 1000

# Or percentage-based sampling
sample_percentage = 0.1  # 10% of total records

# Or automatic sizing based on confidence interval
auto_sample = {
    "confidence_level": 0.95,
    "margin_of_error": 0.05,
    "population_size": "auto"
}
```

### 2. Sampling Strategies

| Strategy | Description | Use Case |
|----------|-------------|----------|
| **Random** | Pure random selection | General exploration |
| **Stratified** | Proportional by category | Balanced representation |
| **Systematic** | Every Nth record | Time-series data |
| **Cluster** | K-means cluster centers | Representative sampling |
| **Time-based** | Interval/window sampling | Temporal data |
| **Custom** | User-defined filter | Specific requirements |

### 3. Schema Analysis

```python
schema_analysis = {
    "fields": [
        {
            "name": "user_id",
            "type": "integer",
            "nullable": False,
            "unique": True,
            "sample_values": [1, 2, 3, ...],
            "cardinality": 5000,
            "cardinality_ratio": 0.5
        },
        {
            "name": "email",
            "type": "string",
            "nullable": False,
            "unique": True,
            "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
            "sample_values": ["user@example.com", ...]
        },
        {
            "name": "created_at",
            "type": "datetime",
            "nullable": False,
            "format": "ISO8601",
            "range": {"min": "2024-01-01", "max": "2024-12-31"}
        }
    ],
    "statistics": {
        "total_fields": 15,
        "total_records": 10000,
        "missing_values": {"field1": 5, "field2": 10},
        "duplicate_records": 3
    }
}
```

### 4. Schema Standardization & Optimization

#### Supported Output Schema Types

| Target | Type Mapping |
|--------|-------------|
| **SQLite** | `INTEGER`, `REAL`, `TEXT`, `BLOB` |
| **PostgreSQL** | `SERIAL`, `BIGINT`, `VARCHAR`, `TIMESTAMP`, `JSONB` |
| **MySQL** | `INT`, `BIGINT`, `VARCHAR`, `DATETIME`, `JSON` |
| **SQL Server** | `INT`, `BIGINT`, `NVARCHAR`, `DATETIME2`, `JSON` |
| **MongoDB** | Type inference based on content |

#### Optimization Rules

```python
optimization_rules = {
    # Integer optimization
    "integer": {
        "tiny": (0, 255)      -> "TINYINT",
        "small": (-32768, 32767) -> "SMALLINT",
        "medium": (-8388608, 8388607) -> "MEDIUMINT",
        "standard": (-2147483648, 2147483647) -> "INT",
        "big": beyond_32bit  -> "BIGINT"
    },

    # String optimization
    "string": {
        "fixed_length": pattern_detected -> "CHAR(n)",
        "variable_length": -> "VARCHAR(n)",
        "long_text": exceeds_threshold -> "TEXT",
        "json_content": pattern_detected -> "JSON/JSONB"
    },

    # Null handling
    "nullable": {
        "all_filled": 0% null -> "NOT NULL",
        "has_nulls": X% null -> "NULL",
        "mostly_null": >90% null -> "Consider dropping"
    }
}
```

#### Optimized Schema Output

```json
{
  "optimized_schema": {
    "table_name": "users",
    "fields": [
      {
        "name": "id",
        "source_type": "integer",
        "target_type": "BIGINT",
        "constraints": ["PRIMARY KEY", "AUTO_INCREMENT"],
        "nullable": false
      },
      {
        "name": "email",
        "source_type": "string",
        "target_type": "VARCHAR(255)",
        "constraints": ["UNIQUE", "NOT NULL"],
        "nullable": false,
        "validation": "email_format"
      },
      {
        "name": "status",
        "source_type": "string",
        "target_type": "VARCHAR(20)",
        "constraints": ["CHECK (status IN ('active','inactive','pending'))"],
        "nullable": true
      },
      {
        "name": "metadata",
        "source_type": "object",
        "target_type": "JSONB",
        "constraints": [],
        "nullable": true
      }
    ],
    "indexes": [
      {"name": "idx_email", "fields": ["email"], "unique": true},
      {"name": "idx_status", "fields": ["status"], "unique": false}
    ],
    "foreign_keys": []
  }
}
```

---

## Data Classification

The content sampler classifies input data into three categories. **JSON is the universal input/output format** throughout the system.

### Classification Categories

| Category | Description | Action |
|----------|-------------|--------|
| **Certain** | Data with a known, fixed, and firm structure. All records share the same schema with consistent field types, formats, and constraints. | Pass through — no processing needed |
| **Mixed** | Data belonging to one category or class, but with schema variations between records. The schemas are similar enough to suggest they come from the same parent class, but differ in some fields or types. | Normalize and transform |
| **Ambiguous** | Data that does not fit the "Certain" or "Mixed" categories. The structure is uncertain, inconsistent, or fundamentally incompatible with defined schemas. | Reject — return error JSON |

### Classification Rules

```python
data_classification = {
    "certain": {
        "description": "Uniform schema across all records",
        "criteria": [
            "All records have identical field names",
            "Field types are consistent (no type mismatches)",
            "Same format/pattern for string fields",
            "No missing or extra fields per record",
            "Constraint rules (nullable, unique, etc.) are uniform"
        ],
        "action": "pass_through"
    },
    "mixed": {
        "description": "Similar but not identical schemas",
        "criteria": [
            "Records share most field names",
            "Minor type variations (e.g., string vs number in same position)",
            "Some optional fields present in some records but not others",
            "Format variations (e.g., date as 'YYYY-MM-DD' vs 'MM/DD/YYYY')",
            "Schema differences are reconcilable through normalization"
        ],
        "action": "normalize_transform"
    },
    "ambiguous": {
        "description": "Incompatible or unpredictable structure",
        "criteria": [
            "Field names change completely between records",
            "Type mismatches that cannot be reconciled",
            "Deeply nested structures with varying depths",
            "No discernible pattern in field arrangement",
            "Corrupted or malformed data that cannot be parsed"
        ],
        "action": "reject"
    }
}
```

### Classification Output

```json
{
  "classification_report": {
    "category": "mixed",
    "confidence": 0.75,
    "details": {
      "total_records_analyzed": 1000,
      "schema_variants": 3,
      "dominant_schema_fields": ["id", "name", "email", "created_at"],
      "variant_schemas": [
        {"fields": ["id", "name", "email", "created_at"], "count": 850},
        {"fields": ["id", "name", "email", "phone", "created_at"], "count": 120},
        {"fields": ["id", "name", "email", "dob"], "count": 30}
      ]
    },
    "recommendation": "Normalize schemas and merge variants"
  }
}
```

### Processing by Category

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Input: JSON Data                              │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     DataClassificationFactory                        │
│         Detects type: certain → mixed → ambiguous                   │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
           ┌──────────────────┼──────────────────┐
           ▼                  ▼                  ▼
    ┌────────────┐     ┌───────────┐      ┌────────────┐
    │  CERTAIN   │     │   MIXED   │      │ AMBIGUOUS  │
    │            │     │           │      │            │
    │  → Pass    │     │ → Normalize│      │  → Reject  │
    │    through │     │ → Transform│     │  → Error   │
    │    No op   │     │ → Merge   │      │    JSON    │
    └────────────┘     └───────────┘      └────────────┘
                              │
                              ▼
                    Output: JSON Data
```

### Ambiguous Data Handling

When data is classified as **Ambiguous**, the system returns an error JSON:

```json
{
  "status": "rejected",
  "category": "ambiguous",
  "reason": "Incompatible schema structure",
  "details": {
    "fields_unexpected": ["unknown_field_xyz"],
    "type_conflicts": [{"field": "amount", "types": ["string", "object"]}],
    "parsing_errors": 45
  },
  "recommendation": "Review source data quality before resubmitting"
}
```

---

## DataClassificationFactory

A factory pattern that manages all classification operations. Input and output are always JSON.

```python
class DataClassificationFactory:
    """
    Central factory for data classification.
    Routes JSON data through detection → processing → output.
    """

    def __init__(self):
        self.classifier = SchemaClassifier()
        self.handlers = {
            "certain": CertainHandler(),
            "mixed": MixedHandler(),
            "ambiguous": AmbiguousHandler()
        }

    def process(self, json_data: dict) -> dict:
        """
        Main entry point. Takes JSON, returns JSON.
        1. Classify the data type
        2. Route to appropriate handler
        3. Return result as JSON
        """
        category = self.classifier.detect(json_data)

        if category == "certain":
            return self.handlers["certain"].handle(json_data)
        elif category == "mixed":
            return self.handlers["mixed"].handle(json_data)
        else:
            return self.handlers["ambiguous"].handle(json_data)
```

### Factory Architecture

```
Input: JSON ──────┬──────────────────────────────────────┐
                  │                                      │
                  ▼                                      │
        ┌─────────────────────┐                         │
        │ DataClassificationFactory │                    │
        │  ┌─────────────────┐ │                         │
        │  │ Classifier     │ │                         │
        │  │ .detect(json)  │ │                         │
        │  └────────┬────────┘ │                         │
        │           │           │                         │
        │  ┌────────▼────────┐ │                         │
        │  │ Handler Router  │ │                         │
        │  └────────┬────────┘ │                         │
        └───────────┼───────────┘                         │
                    │                                      │
        ┌───────────┼───────────┐                          │
        ▼           ▼           ▼                          │
   ┌──────────┐ ┌──────────┐ ┌──────────────┐            │
   │ Certain   │ │  Mixed   │ │  Ambiguous   │            │
   │ Handler   │ │ Handler  │ │  Handler     │            │
   │           │ │          │ │              │            │
   │ No-op     │ │ Normalize│ │ Return error │            │
   │ Pass JSON │ │ Transform│ │ JSON         │            │
   │ through   │ │ Merge    │ │              │            │
   └─────┬─────┘ └────┬─────┘ └──────┬───────┘            │
         │            │              │                    │
         └────────────┼──────────────┘                    │
                      │                                   │
                      ▼                                   │
              Output: JSON ───────────────────────────────┘
```

### Handler Interfaces

```python
class BaseHandler:
    """Base handler interface — all handlers must implement this."""

    def handle(self, json_data: dict) -> dict:
        """Process JSON data and return result as JSON."""
        raise NotImplementedError


class CertainHandler(BaseHandler):
    """Certain data — no transformation needed."""

    def handle(self, json_data: dict) -> dict:
        return {
            "status": "success",
            "category": "certain",
            "data": json_data  # Pass through unchanged
        }


class MixedHandler(BaseHandler):
    """Mixed data — normalize and transform."""

    def __init__(self):
        self.normalizers = [
            SchemaNormalizer(),
            TypeConverter(),
            FieldMerger(),
            FormatStandardizer()
        ]

    def handle(self, json_data: dict) -> dict:
        result = json_data
        for normalizer in self.normalizers:
            result = normalizer.normalize(result)
        return {
            "status": "success",
            "category": "mixed",
            "data": result
        }


class AmbiguousHandler(BaseHandler):
    """Ambiguous data — reject and return error JSON."""

    def handle(self, json_data: dict) -> dict:
        return {
            "status": "rejected",
            "category": "ambiguous",
            "reason": "Data structure is incompatible",
            "data": None
        }
```

### Usage Example

```python
from content_sampler import DataClassificationFactory

# Initialize factory
factory = DataClassificationFactory()

# Input JSON data
input_json = {
    "records": [
        {"id": 1, "name": "Alice", "email": "alice@example.com"},
        {"id": 2, "name": "Bob", "email": "bob@example.com", "phone": "1234"}
    ]
}

# Process — always returns JSON
result = factory.process(input_json)
print(result)
# {
#   "status": "success",
#   "category": "mixed",
#   "data": { ... normalized output ... }
# }
```

---

## Noise Labeling

### What is Noise?

| Noise Type | Description | Example |
|------------|-------------|---------|
| **Missing Values** | Empty/null fields | `{"name": "", "age": null}` |
| **Outliers** | Values far from distribution | `{"age": 999}` |
| **Inconsistent Format** | Varying date formats | `"2024-01-01"` vs `"01/01/2024"` |
| **Duplicate Records** | Exact or near duplicates | Same user id twice |
| **Invalid Characters** | Special chars in fields | `Name: "John\x00Doe"` |
| **Type Mismatch** | Wrong type for field | `age: "thirty"` instead of `30` |
| **Encoding Issues** | garbled text | `"Ã©" instead of "é"` |
| **Truncation** | Cut-off values | `"This is a very long..."` |

### Noise Labeling Interface

```python
class NoiseLabeler:
    """Label noise in data records."""

    def __init__(self):
        self.labels = []

    def label_record(self, record: dict, noise_type: str, field: str = None, severity: str = "low"):
        """Label a specific record or field as noise."""
        self.labels.append({
            "record_id": record.get("_id"),
            "field": field,
            "noise_type": noise_type,
            "severity": severity,  # low, medium, high
            "original_value": record.get(field) if field else None,
            "suggested_action": self._get_action(noise_type)
        })

    def label_field(self, field_name: str, noise_type: str, confidence: float):
        """Label entire field as noisy."""
        self.labels.append({
            "field": field_name,
            "noise_type": noise_type,
            "confidence": confidence,
            "affected_records": "all"
        })

    def _get_action(self, noise_type: str) -> str:
        actions = {
            "missing_value": "impute or remove",
            "outlier": "investigate or cap",
            "inconsistent_format": "standardize",
            "duplicate": "deduplicate",
            "invalid_char": "sanitize or remove",
            "type_mismatch": "convert or coerce",
            "encoding_issue": "re-encode",
            "truncation": "expand field or truncate"
        }
        return actions.get(noise_type, "review manually")
```

### Noise Detection Rules

```python
noise_detection_rules = {
    "missing_value": {
        "detect": lambda v: v is None or v == "" or v == [],
        "severity": "medium"
    },
    "outlier": {
        "detect": "statistical",  # z-score > 3 or IQR method
        "severity": "high"
    },
    "future_date": {
        "detect": lambda v: v > datetime.now(),
        "severity": "high"
    },
    "negative_age": {
        "detect": lambda v: v < 0,
        "severity": "high"
    },
    "invalid_email": {
        "detect": "regex",  # pattern validation
        "severity": "medium"
    },
    "phone_format_inconsistent": {
        "detect": "multiple_formats_detected",
        "severity": "low"
    }
}
```

### Noise Report Output

```json
{
  "noise_report": {
    "total_records_analyzed": 10000,
    "records_with_noise": 523,
    "noise_rate": 0.0523,
    "by_type": {
      "missing_value": {
        "count": 300,
        "affected_fields": ["phone", "address"],
        "severity": "medium"
      },
      "outlier": {
        "count": 45,
        "affected_fields": ["age", "amount"],
        "severity": "high"
      },
      "duplicate": {
        "count": 150,
        "affected_fields": ["id"],
        "severity": "high"
      },
      "format_inconsistent": {
        "count": 28,
        "affected_fields": ["date_created"],
        "severity": "low"
      }
    },
    "by_field": {
      "phone": {"noise_count": 200, "noise_rate": 0.02},
      "address": {"noise_count": 100, "noise_rate": 0.01},
      "age": {"noise_count": 45, "noise_rate": 0.0045}
    },
    "labeled_records": [
      {
        "_id": "abc123_0",
        "field": "age",
        "noise_type": "outlier",
        "original_value": 999,
        "severity": "high",
        "suggested_action": "investigate or cap"
      }
    ]
  }
}
```

---

## User Interface

### CLI Usage

```bash
# Basic sampling
python content_sampler.py data.json --sample-size 1000

# With schema analysis
python content_sampler.py data.json --sample-size 1000 --analyze-schema --output-schema.sql

# With noise labeling
python content_sampler.py data.json --sample-size 1000 --detect-noise --noise-report.json

# Full pipeline
python content_sampler.py data.json \
    --sample-size 1000 \
    --strategy stratified --stratify-by category \
    --analyze-schema \
    --optimize-for sqlite \
    --detect-noise \
    --label-noise \
    --output cleaned_data.json
```

### Python API

```python
from content_sampler import ContentSampler, SchemaAnalyzer, NoiseLabeler

# Initialize
sampler = ContentSampler()

# Sample data
sampled = sampler.sample(
    data=records,
    sample_size=1000,
    strategy="stratified",
    stratify_by="category"
)

# Analyze schema
analyzer = SchemaAnalyzer()
schema_info = analyzer.analyze(sampled)

# Generate optimized schema for target database
optimized = analyzer.optimize(
    schema=schema_info,
    target="postgresql"
)

# Detect and label noise
labeler = NoiseLabeler()
noise_report = labeler.detect_and_label(sampled)

# Export cleaned data
cleaned = labeler.clean(sampled, remove_labeled=True)
```

---

## Project Structure

```
content_sampler/
├── __init__.py
├── sampler.py              # Main sampler class
├── strategies/
│   ├── __init__.py
│   ├── base.py             # Base strategy interface
│   ├── random.py
│   ├── stratified.py
│   ├── systematic.py
│   ├── time_based.py
│   ├── cluster.py
│   └── custom.py
├── schema_analyzer/
│   ├── __init__.py
│   ├── analyzer.py         # Schema analysis
│   ├── type_detector.py    # Type inference
│   ├── type_mapping.py     # Cross-database type mapping
│   ├── optimizer.py        # Schema optimization
│   ├── classifier.py       # Data classification (certain/mixed/ambiguous)
│   ├── handlers.py         # Handler interfaces for each category
│   └── factory.py          # DataClassificationFactory
├── noise_labeler/
│   ├── __init__.py
│   ├── labeler.py          # Main labeler
│   ├── detectors/          # Noise detection rules
│   │   ├── __init__.py
│   │   ├── missing.py
│   │   ├── outlier.py
│   │   ├── format.py
│   │   └── duplicate.py
│   └── cleaners.py         # Data cleaning utilities
├── cli.py                  # Command line interface
└── config.yaml            # Configuration
```

---

## Configuration

```yaml
# content_sampler/config.yaml
sampling:
  default_strategy: random
  default_sample_size: 1000
  allow_duplicates: false
  random_seed: 42

schema_analysis:
  detect_types: true
  calculate_cardinality: true
  sample_values_limit: 10
  detect_patterns: true

optimization:
  target_database: sqlite  # sqlite, postgresql, mysql, sqlserver, mongodb
  infer_constraints: true
  suggest_indexes: true
  max_varchar_length: 255

noise_detection:
  enabled: true
  rules:
    missing_value: true
    outlier: true
    future_date: true
    negative_number: true
    invalid_email: true
    duplicate: true
  severity_thresholds:
    outlier_zscore: 3
    missing_rate_warning: 0.1
    duplicate_rate_warning: 0.05

output:
  format: json
  pretty_print: true
  include_metadata: true
```

---

## Output Examples

### Sample Output

```json
{
  "metadata": {
    "original_count": 50000,
    "sample_size": 1000,
    "strategy": "stratified",
    "stratify_by": "category",
    "sampled_at": "2026-05-31T10:00:00Z"
  },
  "records": [
    {
      "_id": "sample_0",
      "_source": {
        "id": 1,
        "name": "Alice",
        "email": "alice@example.com",
        "category": "A"
      }
    }
  ]
}
```

### Schema Analysis Output

```json
{
  "schema_analysis": {
    "fields": [
      {
        "name": "id",
        "detected_type": "integer",
        "nullable": false,
        "unique": true,
        "min": 1,
        "max": 50000,
        "cardinality": 50000,
        "cardinality_ratio": 1.0
      },
      {
        "name": "email",
        "detected_type": "string",
        "nullable": false,
        "unique": true,
        "pattern": "email",
        "min_length": 10,
        "max_length": 100,
        "cardinality": 49500,
        "cardinality_ratio": 0.99
      }
    ],
    "statistics": {
      "total_records": 50000,
      "total_fields": 8,
      "memory_estimate_mb": 45.2
    }
  },
  "optimized_schema": {
    "target": "postgresql",
    "table": "users",
    "create_sql": "CREATE TABLE users (\n  id BIGSERIAL PRIMARY KEY,\n  email VARCHAR(255) UNIQUE NOT NULL,\n  ...\n);"
  }
}
```

### Noise Report Output

```json
{
  "noise_report": {
    "summary": {
      "total_analyzed": 1000,
      "clean_records": 920,
      "noisy_records": 80,
      "noise_rate": 0.08
    },
    "by_type": {
      "missing_value": {"count": 45, "severity": "medium"},
      "outlier": {"count": 12, "severity": "high"},
      "duplicate": {"count": 23, "severity": "high"}
    },
    "labeled": [
      {
        "record_id": "sample_5",
        "field": "age",
        "noise_type": "outlier",
        "value": 999,
        "severity": "high",
        "action": "investigate"
      }
    ]
  }
}
```
