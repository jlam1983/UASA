# Data Processing System Design

## Overview

A modular data processing system that ingests multiple file types, samples content, stores data in various containers, and provides data renewal capabilities with value-add transformations.

---

## System Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                        Data Sources                           │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│ │   CSV   │ │ JSON    │ │   XML   │ │   TXT   │ │ Excel   │   │
│ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘   │
└───────┼──────────┼──────────┼──────────┼──────────┼───────────┘
        │          │          │          │          │
        ▼          ▼          ▼          ▼          ▼
┌────────────────────────────────────────────────────────────────┐
│                     File Type Adapters                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │ CSV Adapter │ │JSON Adapter │ │ XML Adapter │  ...          │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘               │
└─────────┼───────────────┼───────────────┼──────────────────────┘
          │               │               │
          ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Content Sampler                              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Random Sampling │ Stratified │ Time-based │ Custom     │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Value Add Layer                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │ Enrich   │ │ Transform│ │  Validate│ │ Aggregate│            │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘            │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Data Storage Containers                                         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                │
│  │ SQLite  │ │ Postgre │ │  Mongo  │ │  Redis  │                │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘                │
└───────┼───────────┼───────────┼───────────┼─────────────────────┘
        │           │           │           │
        ▼           ▼           ▼           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Data Source Manager                          │
│              (Renew, Sync, Update, Versioning)                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. Multi-File Type Data Input

### Supported File Types

| File Type | Extension | Parser | Description |
|-----------|-----------|--------|-------------|
| CSV | `.csv` | `csv-parser` | Delimiter-separated values |
| JSON | `.json` | `json-parser` | Structured JSON objects |
| XML | `.xml` | `xml-parser` | Markup format |
| Text | `.txt` | `text-parser` | Plain text lines |
| Excel | `.xlsx`, `.xls` | `excel-parser` | Spreadsheet data |
| Parquet | `.parquet` | `parquet-parser` | Columnar format |
| Avro | `.avro` | `avro-parser` | Binary serialization |

### File Adapter Interface

```python
class FileAdapter(Protocol):
    def parse(self, file_path: str) -> list[dict]:
        """Parse file and return list of records"""

    def validate(self, data: list[dict]) -> bool:
        """Validate data structure"""

    def get_schema(self) -> dict:
        """Return expected schema for this file type"""
```

### Usage Example

```python
from adapters import CSVAdapter, JSONAdapter, XMLAdapter

# Auto-detect file type
adapter = get_adapter("sales_data.csv")
records = adapter.parse("path/to/sales_data.csv")
```

---

## 2. Data Content Sampling

### Sampling Strategies

| Strategy | Description | Use Case |
|----------|-------------|----------|
| **Random** | Random record selection | General exploration |
| **Stratified** | Proportional by category | Balanced datasets |
| **Time-based** | Interval or window sampling | Time series data |
| **Systematic** | Every Nth record | Large dataset reduction |
| **Cluster** | K-means cluster centers | Representative sampling |
| **Custom** | User-defined filter | Specific requirements |

### Sampling Configuration

```python
sampler_config = {
    "strategy": "stratified",
    "sample_size": 1000,
    "stratify_by": "category",
    "random_seed": 42,
    "allow_duplicates": False
}
```

### Implementation

```python
class DataSampler:
    def sample(self, data: list[dict], config: dict) -> list[dict]:
        strategy = config.get("strategy", "random")
        return self.strategies[strategy](data, config)

    def random_sample(self, data: list[dict], config: dict) -> list[dict]:
        size = config.get("sample_size", len(data))
        return random.sample(data, min(size, len(data)))
```

---

## 3. Data Storage Containers

### Container Types

#### SQLite
- **Use Case**: Local development, small datasets, single-user
- **Setup**: File-based, zero configuration
- **Example**:
  ```python
  from storage import SQLiteContainer

  db = SQLiteContainer("data.db")
  db.store("sales", records)
  ```

#### PostgreSQL
- **Use Case**: Production, multi-user, complex queries
- **Setup**: External server required
- **Example**:
  ```python
  from storage import PostgreSQLContainer

  db = PostgreSQLContainer(host="localhost", database="mydb")
  db.store("sales", records, if_exists="replace")
  ```

#### MongoDB
- **Use Case**: Document storage, flexible schema
- **Setup**: External server or Atlas cluster
- **Example**:
  ```python
  from storage import MongoContainer

  db = MongoContainer(connection_string="mongodb://...")
  db.store("sales", records)
  ```

#### Redis
- **Use Case**: Caching, real-time access, pub/sub
- **Setup**: External server required
- **Example**:
  ```python
  from storage import RedisContainer

  cache = RedisContainer(host="localhost")
  cache.store("recent_sales", records, ttl=3600)
  ```

### Container Interface

```python
class StorageContainer(Protocol):
    def store(self, table: str, data: list[dict]) -> None:
        """Store records in container"""

    def load(self, table: str, query: dict) -> list[dict]:
        """Load records with optional query"""

    def update(self, table: str, query: dict, data: dict) -> int:
        """Update matching records"""

    def delete(self, table: str, query: dict) -> int:
        """Delete matching records"""

    def exists(self, table: str) -> bool:
        """Check if table/collection exists"""
```

---

## 4. Data Source Renewal

### Renewal Strategies

| Strategy | Description | Frequency |
|----------|-------------|-----------|
| **Full Refresh** | Replace all data | Daily/Weekly |
| **Incremental** | Add new records only | Hourly |
| **Timestamp-based** | Fetch records newer than last sync | Real-time |
| **CDC (Change Data Capture)** | Track and apply changes | Near real-time |
| **Versioned** | Keep historical versions | On change |

### Renewal Manager

```python
class DataSourceRenewer:
    def __init__(self, container: StorageContainer):
        self.container = container
        self.last_sync = None

    def renew(self, source: DataSource, strategy: str = "incremental"):
        if strategy == "incremental":
            return self._incremental_sync(source)
        elif strategy == "full":
            return self._full_refresh(source)
        elif strategy == "timestamp":
            return self._timestamp_sync(source)

    def _incremental_sync(self, source: DataSource) -> SyncResult:
        last_id = self.container.get_last_id(source.table)
        new_records = source.fetch(after_id=last_id)
        self.container.store(source.table, new_records)
        return SyncResult(added=len(new_records))
```

---

## 5. Value Adding

### Enrichment

```python
class DataEnricher:
    def enrich(self, records: list[dict], rules: list[EnrichmentRule]) -> list[dict]:
        for record in records:
            for rule in rules:
                record[rule.target_field] = rule.compute(record)
        return records

# Example: Add calculated field
rule = EnrichmentRule(
    target_field="total_value",
    compute=lambda r: r["quantity"] * r["unit_price"]
)
```

### Transformations

| Transform | Description |
|-----------|-------------|
| Normalize | Scale numeric values to 0-1 |
| Encode | Convert categorical to numeric |
| Derive | Create new fields from existing |
| Aggregate | Group and summarize |
| Pivot | Reshape data structure |
| Filter | Remove records by condition |

### Validation

```python
class DataValidator:
    rules = [
        Required("id"),
        Type("quantity", int),
        Range("price", min=0, max=10000),
        Pattern("email", r"^[\w.-]+@[\w.-]+\.\w+$"),
    ]

    def validate(self, records: list[dict]) -> ValidationResult:
        errors = []
        for record in records:
            for rule in self.rules:
                if not rule.check(record):
                    errors.append(ValidationError(record, rule))
        return ValidationResult(valid=len(errors) == 0, errors=errors)
```

---

## Project Structure

```
project/
├── adapters/
│   ├── __init__.py
│   ├── base.py          # Base adapter interface
│   ├── csv_adapter.py
│   ├── json_adapter.py
│   ├── xml_adapter.py
│   └── excel_adapter.py
├── storage/
│   ├── __init__.py
│   ├── base.py          # Base container interface
│   ├── sqlite_container.py
│   ├── postgres_container.py
│   ├── mongo_container.py
│   └── redis_container.py
├── sampler/
│   ├── __init__.py
│   ├── sampler.py       # Main sampler class
│   └── strategies/
│       ├── random.py
│       ├── stratified.py
│       └── time_based.py
├── enricher/
│   ├── __init__.py
│   ├── enricher.py
│   └── rules.py
├── renewer/
│   ├── __init__.py
│   └── renewer.py
├── main.py
└── config.yaml
```

---

## Configuration Example

```yaml
# config.yaml
data_sources:
  - name: sales_data
    type: csv
    path: ./data/sales.csv
    adapter: csv

 - name: customer_data
    type: json
    path: ./data/customers.json
    adapter: json

storage:
  default: sqlite
  containers:
    sqlite:
      path: ./data/store.db
    postgres:
      host: localhost
      database: mydb
      user: admin

sampler:
  default_strategy: stratified
  sample_size: 1000

renewal:
  schedule: "0 */6 * * *"  # Every 6 hours
  strategy: incremental
```

---

## Quick Start

```python
from main import DataProcessingSystem

# Initialize system
system = DataProcessingSystem(config="config.yaml")

# Add data source
system.add_source("sales", "data/sales.csv")

# Process and store
system.process("sales")

# Renew data
system.renew("sales", strategy="incremental")

# Query stored data
results = system.query("sales", where={"region": "APAC"})
```
