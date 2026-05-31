# Multi-File Type Input System

## Overview

A flexible data ingestion layer that reads from multiple file types and channels, normalizing everything to a common JSON format for downstream processing.

---

## Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                           Input Channels                               │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌───────┐ │
│  │  File   │ │   API   │ │ Stream  │ │   IoT   │ │ Upload  │ │ DB    │ │
│  │ Upload  │ │ Fetch   │ │  Data   │ │  Cloud  │ │  Form   │ │ Poll  │ │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └───┬───┘ │
└───────┼───────────┼───────────┼───────────┼───────────┼──────────┼─────┘
        │           │           │           │           │          │
        ▼           ▼           ▼           ▼           ▼          ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         Channel Adapters                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │
│  │FileChannel  │ │ APIChannel  │ │StreamChannel│ │ IoTChannel  │ ...   │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘       │
└─────────┼───────────────┼───────────────┼───────────────┼──────────────┘
          │               │               │               │
          ▼               ▼               ▼               ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          File Type Adapters                            │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────┐  │
│  │   CSV   │ │  JSON   │ │   XML   │ │  Excel  │ │  Parquet│ │ YAML │  │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └──┬───┘  │
│       │           │           │           │           │         │      │
│  ┌────┴───────────┴───────────┴───────────┴───────────┴─────────┴────┐ │
│  │                    Unified Type Adapter Interface                 │ │
│  └───────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────┬───────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Common JSON Normalizer                                                  │
│           (Transforms all formats to standard JSON structure)           │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Normalized JSON Output                           │
│                   { records: [...], metadata: {...} }                   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Input Channels

### 1. File Upload Channel

```python
class FileChannel:
    """Handles file uploads from web forms, API multipart, or local files"""

    def read(self, file_path: str) -> bytes:
        """Read file content as bytes"""

    def detect_type(self, file_path: str) -> str:
        """Detect file type from extension and magic bytes"""

    def watch(self, directory: str) -> Generator[FileEvent]:
        """Watch directory for new files"""
```

**Supported Operations:**
- Single file read
- Batch directory processing
- File watching (hot reload)
- Drag-and-drop upload handling

### 2. API Channel

```python
class APIChannel:
    """Fetches data from REST/GraphQL APIs"""

    def fetch(self, url: str, method: str = "GET", **kwargs) -> dict:
        """Make HTTP request and return JSON"""

    def paginate(self, url: str, page_param: str = "page") -> Generator[dict]:
        """Handle paginated API responses"""

    def authenticate(self, credentials: dict) -> str:
        """Get auth token for protected endpoints"""
```

**Supported Operations:**
- GET/POST/PUT/DELETE requests
- OAuth2.0 authentication
- API key authentication
- Basic auth
- Pagination handling
- Rate limiting
- Response caching

### 3. Stream Data Channel

```python
class StreamChannel:
    """Handles streaming data sources (Kafka, Kinesis, WebSocket)"""

    def connect(self, endpoint: str) -> None:
        """Establish connection to stream"""

    def consume(self, topic: str) -> Generator[dict]:
        """Consume messages from stream"""

    def acknowledge(self, message_id: str) -> None:
        """Acknowledge message processing"""
```

**Supported Operations:**
- Apache Kafka consumer
- AWS Kinesis consumer
- WebSocket streaming
- SSE (Server-Sent Events)
- AMQP (RabbitMQ)

### 4. IoT Cloud Channel

```python
class IoTChannel:
    """Connects to IoT cloud platforms"""

    def connect(self, platform: str, credentials: dict) -> None:
        """Connect to IoT platform"""

    def subscribe(self, device_ids: list[str]) -> Generator[dict]:
        """Subscribe to device telemetry"""

    def get_shadow(self, device_id: str) -> dict:
        """Get device shadow state"""
```

**Supported Platforms:**
- AWS IoT Core
- Azure IoT Hub
- Google Cloud IoT
- MQTT brokers
- Custom MQTT endpoints

### 5. Database Channel

```python
class DatabaseChannel:
    """Polls or listens to database changes"""

    def connect(self, connection_string: str) -> None:
        """Establish database connection"""

    def poll(self, query: str, interval: int) -> Generator[dict]:
        """Poll database at intervals"""

    def listen(self, table: str) -> Generator[dict]:
        """Listen to database changes (CDC)"""
```

**Supported Databases:**
- PostgreSQL (with LISTEN/NOTIFY)
- MySQL (with binlog)
- SQL Server (with change tracking)
- Oracle (with CDC)

---

## File Type Adapters

### Supported File Types

| Format | Extensions | Parser | Notes |
|--------|------------|--------|-------|
| **CSV** | `.csv` | `csv-parser` | Configurable delimiter |
| **JSON** | `.json` | `json-parser` | JSON Lines supported |
| **XML** | `.xml` | `xml-parser` | XPath queries |
| **Excel** | `.xlsx`, `.xls` | `openpyxl` | Multi-sheet support |
| **YAML** | `.yaml`, `.yml` | `pyyaml` | Alias support |
| **Parquet** | `.parquet` | `pyarrow` | Columnar format |
| **Avro** | `.avro` | `fastavro` | Binary format |
| **ORC** | `.orc` | `pyarrow` | Columnar format |
| **Feather** | `.feather` | `pyarrow` | Fast reading |
| **HDF5** | `.h5`, `.hdf5` | `h5py` | Scientific data |
| **HTML** | `.html` | `beautifulsoup` | Table extraction |
| **INI** | `.ini` | `configparser` | Config files |
| **TOML** | `.toml` | `toml` | Config files |

### File Adapter Interface

```python
from abc import ABC, abstractmethod
from typing import Any, Generator

class FileTypeAdapter(ABC):
    """Base interface for all file type adapters"""

    @abstractmethod
    def parse(self, source: str | bytes) -> list[dict]:
        """Parse source and return list of records"""
        pass

    @abstractmethod
    def serialize(self, data: list[dict], destination: str) -> None:
        """Serialize records to destination"""
        pass

    @abstractmethod
    def get_schema(self) -> dict:
        """Return schema of parsed data"""
        pass

    @abstractmethod
    def validate(self, data: list[dict]) -> bool:
        """Validate data structure"""
        pass
```

### CSV Adapter

```python
class CSVAdapter(FileTypeAdapter):
    """Adapter for CSV files"""

    def __init__(
        self,
        delimiter: str = ",",
        encoding: str = "utf-8",
        has_header: bool = True,
        skip_rows: int = 0,
        columns: list[str] = None
    ):
        self.delimiter = delimiter
        self.encoding = encoding
        self.has_header = has_header
        self.skip_rows = skip_rows
        self.columns = columns

    def parse(self, source: str | bytes) -> list[dict]:
        if isinstance(source, str):
            source = source.encode(self.encoding)

        reader = csv.reader(
            source.decode(self.encoding).splitlines(),
            delimiter=self.delimiter
        )

        rows = list(reader)
        header = rows[self.skip_rows] if self.has_header else [f"col_{i}" for i in range(len(rows[0]))]
        data_rows = rows[self.skip_rows + (1 if self.has_header else 0):]

        return [dict(zip(header, row)) for row in data_rows]

    def serialize(self, data: list[dict], destination: str) -> None:
        if not data:
            return

        with open(destination, 'w', newline='', encoding=self.encoding) as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys(), delimiter=self.delimiter)
            writer.writeheader()
            writer.writerows(data)
```

### JSON Adapter

```python
class JSONAdapter(FileTypeAdapter):
    """Adapter for JSON files"""

    def __init__(self, encoding: str = "utf-8", lines: bool = False):
        self.encoding = encoding
        self.lines = lines  # JSON Lines format

    def parse(self, source: str | bytes) -> list[dict]:
        if isinstance(source, str):
            source = source.encode(self.encoding)

        text = source.decode(self.encoding)

        if self.lines:
            # JSON Lines format: one JSON object per line
            return [json.loads(line) for line in text.strip().splitlines() if line.strip()]
        else:
            data = json.loads(text)
            # Handle both array and object with records inside
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                # Look for common array keys
                for key in ['data', 'records', 'items', 'results', 'rows']:
                    if key in data and isinstance(data[key], list):
                        return data[key]
                return [data]
            return []

    def serialize(self, data: list[dict], destination: str) -> None:
        with open(destination, 'w', encoding=self.encoding) as f:
            if self.lines:
                for record in data:
                    f.write(json.dumps(record) + '\n')
            else:
                json.dump({"records": data}, f, indent=2, ensure_ascii=False)
```

### XML Adapter

```python
class XMLAdapter(FileTypeAdapter):
    """Adapter for XML files"""

    def __init__(self, encoding: str = "utf-8", record_path: str = ".//record"):
        self.encoding = encoding
        self.record_path = record_path  # XPath to record elements

    def parse(self, source: str | bytes) -> list[dict]:
        if isinstance(source, str):
            source = source.encode(self.encoding)

        tree = ET.parse(BytesIO(source))
        root = tree.getroot()

        records = []
        for elem in root.findall(self.record_path):
            records.append(self._element_to_dict(elem))

        return records

    def _element_to_dict(self, element: ET.Element) -> dict:
        """Convert XML element to dictionary"""
        result = {}
        # Attributes
        for attr, value in element.attrib.items():
            result[f"@{attr}"] = value
        # Child elements
        for child in element:
            if len(child) > 0:
                # Has children - recurse
                if child.tag in result:
                    # Multiple children with same tag - make array
                    if not isinstance(result[child.tag], list):
                        result[child.tag] = [result[child.tag]]
                    result[child.tag].append(self._element_to_dict(child))
                else:
                    result[child.tag] = self._element_to_dict(child)
            else:
                result[child.tag] = child.text
        # Text content
        if element.text and element.text.strip():
            result["_text"] = element.text.strip()
        return result

    def serialize(self, data: list[dict], destination: str) -> None:
        root = ET.Element("root")
        for record in data:
            record_elem = ET.SubElement(root, "record")
            self._dict_to_element(record, record_elem)

        tree = ET.ElementTree(root)
        tree.write(destination, encoding=self.encoding, xml_declaration=True)
```

### Excel Adapter

```python
class ExcelAdapter(FileTypeAdapter):
    """Adapter for Excel files (.xlsx, .xls)"""

    def __init__(
        self,
        sheet: int | str = 0,
        has_header: bool = True,
        skip_rows: int = 0,
        columns: list[str] = None
    ):
        self.sheet = sheet
        self.has_header = has_header
        self.skip_rows = skip_rows
        self.columns = columns

    def parse(self, source: str | bytes) -> list[dict]:
        import openpyxl

        wb = openpyxl.load_workbook(BytesIO(source) if isinstance(source, bytes) else source)
        ws = wb[self.sheet] if isinstance(self.sheet, str) else wb.worksheets[self.sheet]

        rows = list(ws.iter_rows(values_only=True))
        header = rows[self.skip_rows] if self.has_header else [f"col_{i}" for i in range(len(rows[0]))]
        data_rows = rows[self.skip_rows + (1 if self.has_header else 0):]

        return [dict(zip(header, row)) for row in data_rows]

    def get_sheets(self, source: str | bytes) -> list[str]:
        """Get all sheet names"""
        import openpyxl
        wb = openpyxl.load_workbook(BytesIO(source) if isinstance(source, bytes) else source)
        return wb.sheetnames

    def serialize(self, data: list[dict], destination: str) -> None:
        import openpyxl

        wb = Workbook()
        ws = wb.active

        if data:
            # Header
            ws.append(list(data[0].keys()))
            # Data
            for record in data:
                ws.append(list(record.values()))

        wb.save(destination)
```

### YAML Adapter

```python
class YAMLAdapter(FileTypeAdapter):
    """Adapter for YAML files"""

    def __init__(self, encoding: str = "utf-8"):
        self.encoding = encoding

    def parse(self, source: str | bytes) -> list[dict]:
        if isinstance(source, str):
            source = source.encode(self.encoding)

        data = yaml.safe_load(source)

        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            for key in ['data', 'records', 'items', 'results']:
                if key in data and isinstance(data[key], list):
                    return data[key]
            return [data]
        return []

    def serialize(self, data: list[dict], destination: str) -> None:
        with open(destination, 'w', encoding=self.encoding) as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
```

### Parquet Adapter

```python
class ParquetAdapter(FileTypeAdapter):
    """Adapter for Parquet files"""

    def __init__(self):
        pass

    def parse(self, source: str | bytes) -> list[dict]:
        import pyarrow.parquet as pq

        if isinstance(source, bytes):
            source = BytesIO(source)

        table = pq.read_table(source)
        df = table.to_pandas()
        return df.to_dict(orient='records')

    def serialize(self, data: list[dict], destination: str) -> None:
        import pyarrow.parquet as pq
        import pandas as pd

        df = pd.DataFrame(data)
        table = pyarrow.Table.from_pandas(df)
        pq.write_table(table, destination)
```

---

## Common JSON Normalizer

### Purpose

Transforms all parsed data into a standardized JSON structure regardless of original format.

### Normalized Schema

```json
{
  "metadata": {
    "source_type": "csv | json | xml | excel | ...",
    "source_channel": "file | api | stream | iot | database",
    "source_path": "original path or URL",
    "record_count": 100,
    "columns": ["col1", "col2", ...],
    "parsed_at": "2026-05-31T10:00:00Z",
    "schema_hash": "abc123..."
  },
  "records": [
    {
      "_id": "unique-record-id",
      "_source": "original data with normalized keys",
      "_raw": "original raw record (optional)"
    }
  ]
}
```

### Normalizer Implementation

```python
class JSONNormalizer:
    """Normalizes all data formats to standard JSON structure"""

    def __init__(self, include_raw: bool = False, generate_ids: bool = True):
        self.include_raw = include_raw
        self.generate_ids = generate_ids

    def normalize(
        self,
        data: list[dict],
        source_type: str,
        source_channel: str,
        source_path: str = None
    ) -> dict:
        """Convert parsed data to normalized JSON"""

        columns = list(data[0].keys()) if data else []

        normalized = {
            "metadata": {
                "source_type": source_type,
                "source_channel": source_channel,
                "source_path": source_path,
                "record_count": len(data),
                "columns": columns,
                "parsed_at": datetime.utcnow().isoformat() + "Z",
                "schema_hash": self._hash_columns(columns)
            },
            "records": []
        }

        for i, record in enumerate(data):
            normalized_record = {
                "_id": self._generate_id(source_path, i) if self.generate_ids else str(i),
                "_source": self._normalize_keys(record)
            }

            if self.include_raw:
                normalized_record["_raw"] = record

            normalized["records"].append(normalized_record)

        return normalized

    def _normalize_keys(self, record: dict) -> dict:
        """Normalize dictionary keys (snake_case, remove special chars)"""
        result = {}
        for key, value in record.items():
            # Convert to snake_case
            normalized_key = re.sub(r'[\W]+', '_', key.lower().strip())
            # Handle nested dicts/lists recursively
            if isinstance(value, dict):
                result[normalized_key] = self._normalize_keys(value)
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                result[normalized_key] = [self._normalize_keys(v) for v in value]
            else:
                result[normalized_key] = value
        return result

    def _generate_id(self, source: str, index: int) -> str:
        """Generate unique record ID"""
        prefix = hashlib.md5(str(source).encode()).hexdigest()[:8]
        return f"{prefix}_{index}"

    def _hash_columns(self, columns: list[str]) -> str:
        """Generate schema hash for change detection"""
        col_str = ",".join(sorted(columns))
        return hashlib.md5(col_str.encode()).hexdigest()[:12]
```

---

## Channel Adapter Factory

```python
class ChannelAdapterFactory:
    """Factory for creating channel adapters"""

    _channels = {
        "file": FileChannel,
        "api": APIChannel,
        "stream": StreamChannel,
        "iot": IoTChannel,
        "database": DatabaseChannel,
    }

    _file_types = {
        "csv": CSVAdapter,
        "json": JSONAdapter,
        "xml": XMLAdapter,
        "xlsx": ExcelAdapter,
        "xls": ExcelAdapter,
        "yaml": YAMLAdapter,
        "yml": YAMLAdapter,
        "parquet": ParquetAdapter,
    }

    @classmethod
    def create_channel(cls, channel_type: str) -> ChannelAdapter:
        """Create channel adapter by type"""
        if channel_type not in cls._channels:
            raise ValueError(f"Unknown channel type: {channel_type}")
        return cls._channels[channel_type]()

    @classmethod
    def create_file_adapter(cls, file_type: str) -> FileTypeAdapter:
        """Create file type adapter by extension"""
        if file_type not in cls._file_types:
            raise ValueError(f"Unknown file type: {file_type}")
        return cls._file_types[file_type]()

    @classmethod
    def detect_file_type(cls, file_path: str) -> str:
        """Detect file type from path"""
        ext = os.path.splitext(file_path)[1].lower().lstrip('.')
        return ext
```

---

## Data Ingestion Pipeline

```python
class DataIngestionPipeline:
    """Complete pipeline for multi-source data ingestion"""

    def __init__(self, normalizer: JSONNormalizer = None):
        self.normalizer = normalizer or JSONNormalizer()
        self.channel_factory = ChannelAdapterFactory()
        self.file_adapter_factory = ChannelAdapterFactory()

    def ingest(
        self,
        source: str,
        channel_type: str,
        file_type: str = None,
        **kwargs
    ) -> dict:
        """Ingest data from any source and return normalized JSON"""

        # Create channel adapter
        channel = self.channel_factory.create_channel(channel_type)

        # Read raw data from channel
        raw_data = self._read_from_channel(channel, source, **kwargs)

        # Detect file type if not provided
        if file_type is None and channel_type == "file":
            file_type = self.channel_factory.detect_file_type(source)

        # Parse with appropriate adapter
        if file_type:
            adapter = self.file_adapter_factory.create_file_adapter(file_type)
            parsed_data = adapter.parse(raw_data)
        else:
            # Assume raw JSON if no file type
            parsed_data = self._parse_raw_json(raw_data)

        # Normalize to common JSON format
        normalized = self.normalizer.normalize(
            data=parsed_data,
            source_type=file_type or "json",
            source_channel=channel_type,
            source_path=source
        )

        return normalized

    def _read_from_channel(self, channel, source: str, **kwargs) -> bytes | dict:
        """Read data from specified channel"""
        if isinstance(channel, FileChannel):
            return channel.read(source)
        elif isinstance(channel, APIChannel):
            return channel.fetch(source, **kwargs)
        elif isinstance(channel, StreamChannel):
            return channel.consume(source, **kwargs)
        elif isinstance(channel, IoTChannel):
            return channel.subscribe(source, **kwargs)
        else:
            raise ValueError(f"Unsupported channel type: {type(channel)}")
```

---

## Usage Examples

### Example 1: Read CSV File

```python
pipeline = DataIngestionPipeline()

result = pipeline.ingest(
    source="./data/sales.csv",
    channel_type="file",
    file_type="csv"
)

print(f"Loaded {result['metadata']['record_count']} records")
print(result['records'][0])
```

**Output:**
```json
{
  "metadata": {
    "source_type": "csv",
    "source_channel": "file",
    "source_path": "./data/sales.csv",
    "record_count": 1000,
    "columns": ["date", "product", "quantity", "price"],
    "parsed_at": "2026-05-31T10:00:00Z",
    "schema_hash": "a1b2c3d4e5f6"
  },
  "records": [
    {
      "_id": "abc123_0",
      "_source": {
        "date": "2026-01-01",
        "product": "Widget A",
        "quantity": 10,
        "price": 29.99
      }
    }
  ]
}
```

### Example 2: Fetch API Data

```python
result = pipeline.ingest(
    source="https://api.example.com/users",
    channel_type="api",
    file_type="json"
)

print(result['metadata']['record_count'], "users loaded")
```

### Example 3: IoT Telemetry

```python
iot_channel = IoTChannel()
iot_channel.connect(
    platform="aws_iot",
    credentials={"endpoint": "xxx.iot.us-east-1.amazonaws.com", ...}
)

for device_id in ["sensor-001", "sensor-002"]:
    for telemetry in iot_channel.subscribe([device_id]):
        normalized = pipeline.normalizer.normalize(
            data=[telemetry],
            source_type="json",
            source_channel="iot",
            source_path=device_id
        )
        # Process normalized data...
```

### Example 4: Batch Directory Processing

```python
for event in FileChannel().watch("./data/incoming"):
    if event.type == "created":
        result = pipeline.ingest(
            source=event.path,
            channel_type="file"
        )
        print(f"Processed {result['metadata']['record_count']} records from {event.path}")
```

---

## Error Handling

```python
class IngestionError(Exception):
    """Base exception for ingestion errors"""
    pass

class ChannelReadError(IngestionError):
    """Failed to read from channel"""
    pass

class ParseError(IngestionError):
    """Failed to parse data"""
    pass

class NormalizationError(IngestionError):
    """Failed to normalize data"""
    pass

# Error handling in pipeline
try:
    result = pipeline.ingest(source, channel_type, file_type)
except ChannelReadError as e:
    print(f"Failed to read source: {e}")
except ParseError as e:
    print(f"Failed to parse data: {e}")
except NormalizationError as e:
    print(f"Failed to normalize data: {e}")
```

---

## Configuration

```yaml
# config/multi_file_input.yaml
channels:
  file:
    watch_directories:
      - ./data/incoming
      - ./data/uploads
    auto_detect_type: true

 api:
    base_url: "https://api.example.com"
    timeout: 30
    retry_count: 3
    auth:
      type: oauth2
      token_url: "https://auth.example.com/token"

  stream:
    type: kafka
    bootstrap_servers:
      - localhost:9092
    consumer_group: data_processor

 iot:
    platform: aws_iot
    region: us-east-1
    edge_compute: false

  database:
    poll_interval: 60
    change_detection: true

file_types:
  csv:
    delimiter: ","
    encoding: utf-8
    has_header: true

  excel:
    sheet: 0
    has_header: true

normalizer:
  include_raw: false
  generate_ids: true
  snake_case_keys: true
```
