"""Database channel adapter."""

from __future__ import annotations

import json
import time
from typing import Generator, Any
from dataclasses import dataclass

from ..exceptions import ChannelReadError


@dataclass
class DatabaseChange:
    operation: str
    table: str
    data: dict
    timestamp: float


class DatabaseChannel:
    """Polls or listens to database changes."""

    def __init__(self, connection_string: str | None = None):
        self.connection_string = connection_string
        self._connection = None
        self._cursor = None

    def connect_postgres(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "postgres",
        user: str | None = None,
        password: str | None = None,
    ) -> None:
        """Connect to PostgreSQL database."""
        try:
            import psycopg2

            self._connection = psycopg2.connect(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password,
            )
            self._connection.autocommit = True
        except ImportError:
            raise ChannelReadError("psycopg2 not installed. Run: pip install psycopg2-binary")

    def connect_mysql(
        self,
        host: str = "localhost",
        port: int = 3306,
        database: str = "mysql",
        user: str | None = None,
        password: str | None = None,
    ) -> None:
        """Connect to MySQL database."""
        try:
            import pymysql

            self._connection = pymysql.connect(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password,
                charset="utf8mb4",
            )
        except ImportError:
            raise ChannelReadError("pymysql not installed. Run: pip install pymysql")

    def connect_sqlserver(
        self,
        host: str = "localhost",
        port: int = 1433,
        database: str = "master",
        user: str | None = None,
        password: str | None = None,
    ) -> None:
        """Connect to SQL Server database."""
        try:
            import pyodbc

            driver = "{ODBC Driver17 for SQL Server}"
            conn_str = f"DRIVER={driver};SERVER={host},{port};DATABASE={database};"
            if user and password:
                conn_str += f"UID={user};PWD={password}"
            else:
                conn_str += "Trusted_Connection=yes"
            self._connection = pyodbc.connect(conn_str)
        except ImportError:
            raise ChannelReadError("pyodbc not installed. Run: pip install pyodbc")

    def connect_sqlite(self, database_path: str) -> None:
        """Connect to SQLite database."""
        try:
            import sqlite3
            self._connection = sqlite3.connect(database_path)
        except ImportError:
            raise ChannelReadError("sqlite3 not available")

    def execute(self, query: str, params: tuple | None = None) -> list[dict]:
        """Execute query and return results as list of dicts."""
        if self._connection is None:
            raise ChannelReadError("No database connection. Call connect_* first.")

        cursor = self._connection.cursor()
        cursor.execute(query, params or ())

        if query.strip().upper().startswith(("INSERT", "UPDATE", "DELETE")):
            self._connection.commit()
            return [{"rows_affected": cursor.rowcount}]

        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def poll(self, query: str, interval: int = 60) -> Generator[dict, None, None]:
        """Poll database at intervals."""
        last_result = None
        while True:
            current_result = self.execute(query)
            if current_result != last_result:
                yield from current_result
                last_result = current_result
            time.sleep(interval)

    def listen(self, table: str) -> Generator[DatabaseChange, None, None]:
        """Listen to database changes (CDC)."""
        if hasattr(self._connection, "cursor") and hasattr(self._connection, "commit"):
            if hasattr(self._connection, "autocommit"):
                try:
                    import psycopg2
                    cursor = self._connection.cursor()
                    cursor.execute(f"LISTEN {table}_changes")
                    self._connection.commit()
                    while True:
                        self._connection.poll()
                        for notification in self._connection.notifies():
                            yield DatabaseChange(
                                operation="UPDATE",
                                table=table,
                                data={"payload": notification.payload},
                                timestamp=time.time(),
                            )
                except Exception:
                    pass

        raise ChannelReadError(f"listen not supported for this database type")

    def close(self) -> None:
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
