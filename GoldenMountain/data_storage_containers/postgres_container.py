"""PostgreSQL storage container."""

from typing import Any


class PostgreSQLContainer:
    """PostgreSQL-based storage container."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "postgres",
        user: str = "postgres",
        password: str = "",
    ):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self._conn = None

    def _connect(self):
        try:
            import psycopg2
        except ImportError:
            raise ImportError("psycopg2 is required: pip install psycopg2-binary")
        if self._conn is None:
            self._conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
            )

    def store(self, table: str, data: list[dict]) -> None:
        if not data:
            return
        self._connect()
        cols = list(data[0].keys())
        col_names = ", ".join(cols)
        placeholders = ", ".join([f"%({c})s" for c in cols])
        with self._conn.cursor() as cur:
            cur.execute(f"CREATE TABLE IF NOT EXISTS {table} ({col_names})")
            cur.executemany(
                f"INSERT INTO {table} ({col_names}) VALUES ({placeholders}) ON CONFLICT DO NOTHING",
                data,
            )
        self._conn.commit()

    def load(self, table: str, query: dict | None = None) -> list[dict]:
        self._connect()
        if query:
            conditions = " AND ".join([f"{k} = %({k})s" for k in query.keys()])
            sql = f"SELECT * FROM {table} WHERE {conditions}"
            with self._conn.cursor() as cur:
                cur.execute(sql, query)
                return [dict(row) for row in cur.fetchall()]
        else:
            with self._conn.cursor() as cur:
                cur.execute(f"SELECT * FROM {table}")
                return [dict(row) for row in cur.fetchall()]

    def update(self, table: str, query: dict, data: dict) -> int:
        if not data or not query:
            return 0
        self._connect()
        set_clause = ", ".join([f"{k} = %({k})s" for k in data.keys()])
        where_clause = " AND ".join([f"{k} = %({k})s" for k in query.keys()])
        combined = {**data, **query}
        sql = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        with self._conn.cursor() as cur:
            cur.execute(sql, combined)
        self._conn.commit()
        return cur.rowcount if hasattr(cur, "rowcount") else 0

    def delete(self, table: str, query: dict) -> int:
        if not query:
            return 0
        self._connect()
        where_clause = " AND ".join([f"{k} = %({k})s" for k in query.keys()])
        sql = f"DELETE FROM {table} WHERE {where_clause}"
        with self._conn.cursor() as cur:
            cur.execute(sql, query)
        self._conn.commit()
        return cur.rowcount if hasattr(cur, "rowcount") else 0

    def exists(self, table: str) -> bool:
        self._connect()
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s)",
                (table,),
            )
            return cur.fetchone()[0]

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
