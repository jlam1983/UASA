# Data Storage Containers

## Overview

Modular storage layer supporting multiple database technologies for persistent data storage, designed as part of the GoldenMountain Data Processing System.

---

## Supported Containers

| Container | Type | Use Case |
|-----------|------|----------|
| SQLite | File-based RDBMS | Local development, small datasets, single-user |
| PostgreSQL | Server RDBMS | Production, multi-user, complex queries |
| MongoDB | Document Store | Flexible schema, document storage |
| Redis | In-memory KV | Caching, real-time access, pub/sub |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Storage Container Layer                     │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│  │ SQLite  │ │PostgreSQL│ │ MongoDB │ │  Redis  │          │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘          │
└───────┼───────────┼───────────┼───────────┼────────────────┘
        │           │           │           │
        ▼           ▼           ▼           ▼
┌─────────────────────────────────────────────────────────────┐
│                  Base Container Interface                    │
│           (store, load, update, delete, exists)             │
└─────────────────────────────────────────────────────────────┘
```

---

## Container Interface

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

## Usage Examples

### SQLite

```python
from storage import SQLiteContainer

db = SQLiteContainer("data.db")
db.store("sales", records)
```

### PostgreSQL

```python
from storage import PostgreSQLContainer

db = PostgreSQLContainer(host="localhost", database="mydb")
db.store("sales", records, if_exists="replace")
```

### MongoDB

```python
from storage import MongoContainer

db = MongoContainer(connection_string="mongodb://...")
db.store("sales", records)
```

### Redis

```python
from storage import RedisContainer

cache = RedisContainer(host="localhost")
cache.store("recent_sales", records, ttl=3600)
```

---

## Configuration

```yaml
storage:
  default: sqlite
  containers:
    sqlite:
      path: ./data/store.db
    postgres:
      host: localhost
      database: mydb
      user: admin
      password: secret
    mongodb:
      connection_string: mongodb://localhost:27017
    redis:
      host: localhost
      port: 6379
```

---

## Project Structure

```
data_storage_containers/
├── __init__.py
├── base.py              # Base container interface
├── sqlite_container.py
├── postgres_container.py
├── mongo_container.py
└── redis_container.py
```
