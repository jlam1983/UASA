"""MongoDB storage container."""

from typing import Any


class MongoContainer:
    """MongoDB-based storage container."""

    def __init__(self, connection_string: str = "mongodb://localhost:27017", database: str = "default"):
        self.connection_string = connection_string
        self.database_name = database
        self._client = None
        self._db = None

    def _connect(self):
        try:
            from pymongo import MongoClient
        except ImportError:
            raise ImportError("pymongo is required: pip install pymongo")
        if self._client is None:
            self._client = MongoClient(self.connection_string)
            self._db = self._client[self.database_name]

    def store(self, table: str, data: list[dict]) -> None:
        if not data:
            return
        self._connect()
        collection = self._db[table]
        collection.insert_many(data)

    def load(self, table: str, query: dict | None = None) -> list[dict]:
        self._connect()
        collection = self._db[table]
        cursor = collection.find(query or {})
        return [doc | {"_id": str(doc["_id"])} for doc in cursor]

    def update(self, table: str, query: dict, data: dict) -> int:
        if not data or not query:
            return 0
        self._connect()
        collection = self._db[table]
        result = collection.update_many(query, {"$set": data})
        return result.modified_count

    def delete(self, table: str, query: dict) -> int:
        if not query:
            return 0
        self._connect()
        collection = self._db[table]
        result = collection.delete_many(query)
        return result.deleted_count

    def exists(self, table: str) -> bool:
        self._connect()
        return table in self._db.list_collection_names()

    def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
