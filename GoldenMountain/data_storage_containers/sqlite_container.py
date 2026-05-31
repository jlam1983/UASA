"""SQLite storage container."""

import json
import sqlite3
from pathlib import Path
from typing import Any


class SQLiteContainer:
    """SQLite-based storage container."""

    def __init__(self, path: str = ":memory:"):
        self.path = path
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row

    def store(self, table: str, data: list[dict]) -> None:
        if not data:
            return
        cols = list(data[0].keys())
        placeholders = ", ".join(["?"] * len(cols))
        col_names = ", ".join(cols)
        self._conn.execute(f"CREATE TABLE IF NOT EXISTS {table} ({col_names})")
        for row in data:
            values = [row.get(c) for c in cols]
            self._conn.execute(f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})", values)
        self._conn.commit()

    def load(self, table: str, query: dict | None = None) -> list[dict]:
        if query:
            conditions = " AND ".join([f"{k} = ?" for k in query.keys()])
            values = list(query.values())
            cursor = self._conn.execute(f"SELECT * FROM {table} WHERE {conditions}", values)
        else:
            cursor = self._conn.execute(f"SELECT * FROM {table}")
        return [dict(row) for row in cursor.fetchall()]

    def update(self, table: str, query: dict, data: dict) -> int:
        if not data or not query:
            return 0
        set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
        where_clause = " AND ".join([f"{k} = ?" for k in query.keys()])
        values = list(data.values()) + list(query.values())
        cursor = self._conn.execute(f"UPDATE {table} SET {set_clause} WHERE {where_clause}", values)
        self._conn.commit()
        return cursor.rowcount

    def delete(self, table: str, query: dict) -> int:
        if not query:
            return 0
        where_clause = " AND ".join([f"{k} = ?" for k in query.keys()])
        cursor = self._conn.execute(f"DELETE FROM {table} WHERE {where_clause}", list(query.values()))
        self._conn.commit()
        return cursor.rowcount

    def exists(self, table: str) -> bool:
        cursor = self._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
        )
        return cursor.fetchone() is not None

    def close(self) -> None:
        self._conn.close()
