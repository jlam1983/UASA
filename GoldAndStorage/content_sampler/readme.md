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
│   ├── optimizer.py        # Schema optimization
│   └── type_mapping.py     # Cross-database type mapping
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
