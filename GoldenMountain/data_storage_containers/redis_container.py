"""Redis storage container."""

import json
from typing import Any


class RedisContainer:
    """Redis-based storage container."""

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        self.host = host
        self.port = port
        self.db = db
        self._client = None

    def _connect(self):
        try:
            import redis
        except ImportError:
            raise ImportError("redis is required: pip install redis")
        if self._client is None:
            self._client = redis.Redis(host=self.host, port=self.port, db=self.db, decode_responses=True)

    def _key(self, table: str) -> str:
        return f"dsc:{table}"

    def store(self, table: str, data: list[dict], ttl: int | None = None) -> None:
        if not data:
            return
        if self._client is None:
            self._connect()
        key = self._key(table)
        self._client.delete(key)
        for i, record in enumerate(data):
            self._client.hset(key, f"row:{i}", json.dumps(record))
        if ttl:
            self._client.expire(key, ttl)

    def load(self, table: str, query: dict | None = None) -> list[dict]:
        if self._client is None:
            self._connect()
        key = self._key(table)
        raw = self._client.hgetall(key)
        results = [json.loads(v) for v in raw.values()]
        if query:
            results = [r for r in results if all(r.get(k) == v for k, v in query.items())]
        return results

    def update(self, table: str, query: dict, data: dict) -> int:
        if not data or not query:
            return 0
        if self._client is None:
            self._connect()
        records = self.load(table, query)
        count = 0
        for record in records:
            if all(record.get(k) == v for k, v in query.items()):
                merged = {**record, **data}
                self.store(table, [merged])
                count += 1
        return count

    def delete(self, table: str, query: dict) -> int:
        if not query:
            return 0
        if self._client is None:
            self._connect()
        records = self.load(table, query)
        if not records:
            return 0
        key = self._key(table)
        for i, record in enumerate(records):
            self._client.hdel(key, f"row:{i}")
        return len(records)

    def exists(self, table: str) -> bool:
        if self._client is None:
            self._connect()
        return self._client.exists(self._key(table)) > 0

    def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None
