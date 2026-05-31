# Multi-File Type Input System

## Overview

A flexible data ingestion layer that reads from multiple sources, normalizing everything to a single JSON format. Data is categorized as **flatten** (single-table) or **complex** (multi-level/hierarchical) — both output as one standardized JSON.

---

## Architecture

```
Input Channel (1 method) → File Adapter (1 method) → Normalizer → JSON Output
```

**5 Input Channels, each with: `read()` in, `export()` out**

| Channel | Source | Output |
|---------|--------|--------|
| FileChannel | Local/remote files | JSON records |
| APIChannel | HTTP endpoints | JSON records |
| StreamChannel | Message queues/streams | JSON records |
| DatabaseChannel | DB polling/CDC | JSON records |
| IoTChannel | IoT platforms | JSON records |

**2 Data Categories**

| Category | Description | Example |
|----------|-------------|---------|
| Flatten | Single table structure | CSV, simple JSON, Excel sheet |
| Complex | Multi-level, needs flattening | Nested JSON, XML hierarchy, multi-sheet Excel |

---

## Output Schema

All inputs normalize to this single JSON format:

```json
{
  "metadata": {
    "source_type": "csv | json | xml | ...",
    "source_channel": "file | api | stream | database | iot",
    "source_path": "path or URL",
    "record_count": 100,
    "columns": ["col1", "col2"],
    "parsed_at": "2024-01-01T00:00:00Z",
    "data_category": "flatten | complex"
  },
  "records": [
    {
      "_id": "record-unique-id",
      "_source": { "normalized": "data" }
    }
  ]
}
```

---

## Channel Interfaces

Each channel has exactly 2 methods: `read()` for input, `export()` for output.

### FileChannel

```python
class FileChannel:
    def read(self, path: str) -> bytes
    def export(self, path: str) -> dict:  # Returns normalized JSON
```

### APIChannel

```python
class APIChannel:
    def read(self, url: str, **kwargs) -> dict
    def export(self, url: str, data: dict) -> dict:  # Returns normalized JSON
```

### StreamChannel

```python
class StreamChannel:
    def read(self, endpoint: str) -> bytes
    def export(self, topic: str, data: dict) -> None:  # Writes to stream
```

### DatabaseChannel

```python
class DatabaseChannel:
    def read(self, query: str) -> list[dict]
    def export(self, table: str, data: dict) -> None:  # Writes to table
```

### IoTChannel

```python
class IoTChannel:
    def read(self, device_ids: list[str]) -> dict
    def export(self, device_id: str, data: dict) -> None:  # Sends to device
```

---

## File Adapters

Each adapter has exactly 2 methods: `parse()` for input, `serialize()` for output.

| Adapter | Extensions | Parse Output |
|---------|------------|--------------|
| CSVAdapter | .csv | Flatten |
| JSONAdapter | .json, .jsonl | Flatten or Complex |
| XMLAdapter | .xml | Complex |
| ExcelAdapter | .xlsx, .xls | Flatten (per sheet) |
| YAMLAdapter | .yaml, .yml | Flatten or Complex |

### Adapter Interface

```python
class FileTypeAdapter:
    def parse(self, source: str | bytes) -> list[dict]
    def serialize(self, data: list[dict], dest: str) -> None

    def normalize(self, data: list[dict]) -> dict:
        """Convert parsed data to standard JSON"""
        return {
            "metadata": { ... },
            "records": [{ "_id": "...", "_source": ... }]
        }
```

---

## Data Category Handling

### Flatten Data

Single-table data parsed directly to records:

```python
# CSV → Flatten
csv_data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
# Output: 2 records with flat structure
```

### Complex Data

Hierarchical/nested data flattened into multiple records:

```python
# Nested JSON → Flatten
nested = {
    "company": "Acme",
    "departments": [
        {"name": "Engineering", "employees": [
            {"name": "Alice", "role": "Engineer"},
            {"name": "Bob", "role": "Engineer"}
        ]},
        {"name": "Sales", "employees": [...]}
    ]
}
# Output: 4 employee records with company + dept context
```

```python
# XML → Flatten
xml_data = """
<company>
  <dept name="Engineering">
    <employee><name>Alice</name></employee>
  </dept>
</company>
"""
# Output: 2 records with parent context embedded
```

### Flatten Rules

1. **Array fields** expand to multiple records
2. **Parent fields** propagate to each child record
3. **Nested objects** become prefixed keys (e.g., `company_dept_employee_name`)

---

## Normalizer

```python
class JSONNormalizer:
    """Single output format for all inputs"""

    def normalize(
        self,
        data: list[dict],
        source_type: str,
        source_channel: str,
        source_path: str = None
    ) -> dict:
        return {
            "metadata": {
                "source_type": source_type,
                "source_channel": source_channel,
                "source_path": source_path,
                "record_count": len(data),
                "columns": list(data[0].keys()) if data else [],
                "parsed_at": datetime.utcnow().isoformat() + "Z",
                "data_category": self._detect_category(data)
            },
            "records": [
                {"_id": f"rec_{i}", "_source": row}
                for i, row in enumerate(data)
            ]
        }

    def _detect_category(self, data: list[dict]) -> str:
        """Detect if data is flatten or complex"""
        if not data:
            return "flatten"
        first = data[0]
        # Complex if any value is a list of dicts or nested dict
        for v in first.values():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                return "complex"
            if isinstance(v, dict):
                return "complex"
        return "flatten"
```

---

## Usage Examples

### Example 1: Read CSV File

```python
from multi_file_input import FileChannel, CSVAdapter, JSONNormalizer

channel = FileChannel()
adapter = CSVAdapter()
normalizer = JSONNormalizer()

# Read → Parse → Normalize
raw = channel.read("./data/sales.csv")
parsed = adapter.parse(raw)
result = normalizer.normalize(parsed, "csv", "file", "./data/sales.csv")

print(result["metadata"]["record_count"], "records")
```

### Example 2: Fetch API Data

```python
from multi_file_input import APIChannel, JSONAdapter, JSONNormalizer

channel = APIChannel()
adapter = JSONAdapter()
normalizer = JSONNormalizer()

raw = channel.read("https://api.example.com/users")
parsed = adapter.parse(raw)
result = normalizer.normalize(parsed, "json", "api", "https://api.example.com/users")

print(result["metadata"]["record_count"], "users")
```

### Example 3: Complex Nested JSON

```python
from multi_file_input import JSONAdapter, JSONNormalizer

adapter = JSONAdapter()
normalizer = JSONNormalizer()

nested = {
    "company": "Acme",
    "departments": [
        {"name": "Eng", "staff": [
            {"name": "Alice", "skills": ["Python", "Go"]},
            {"name": "Bob", "skills": ["JS", "Python"]}
        ]}
    ]
}

parsed = adapter.parse(json.dumps([nested]))
# parsed = [{company: "Acme", departments: [...]}]

result = normalizer.normalize(parsed, "json", "file", "company.json")
# data_category = "complex"
# Records expand: Alice(Acme, Eng), Bob(Acme, Eng)
```

---

## Error Handling

```python
class IngestionError(Exception): pass
class ChannelReadError(IngestionError): pass
class ParseError(IngestionError): pass
class NormalizationError(IngestionError): pass

# Usage
try:
    raw = channel.read(source)
    parsed = adapter.parse(raw)
    result = normalizer.normalize(parsed, source_type, channel_type)
except ChannelReadError:
    print("Failed to read source")
except ParseError:
    print("Failed to parse data")
except NormalizationError:
    print("Failed to normalize")
```

---

## Configuration

```yaml
# config/multi_file_input.yaml
channels:
  file:
    watch_directories:
      - ./data/incoming
  api:
    timeout: 30
    retry_count: 3
  stream:
    type: kafka
    bootstrap_servers:
      - localhost:9092
  database:
    poll_interval: 60
  iot:
    platform: aws_iot
    region: us-east-1

file_types:
  csv:
    delimiter: ","
    has_header: true
  excel:
    sheet: 0
    has_header: true

normalizer:
  generate_ids: true
  snake_case_keys: true
```