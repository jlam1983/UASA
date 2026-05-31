"""Type mapping for different database targets."""

from typing import Any


class TypeMapping:
    """Maps inferred types to target database types."""

    MAPPINGS = {
        "sqlite": {
            "null": "TEXT",
            "boolean": "INTEGER",
            "integer": "INTEGER",
            "float": "REAL",
            "string": "TEXT",
            "array": "TEXT",
            "object": "TEXT",
            "datetime": "TEXT",
 "date": "TEXT",
            "time": "TEXT",
            "uuid": "TEXT",
 "email": "TEXT",
            "url": "TEXT",
            "phone": "TEXT",
            "ipv4": "TEXT",
            "json": "TEXT",
        },
        "postgresql": {
            "null": "TEXT",
            "boolean": "BOOLEAN",
            "integer": "INTEGER",
            "float": "DOUBLE PRECISION",
            "string": "VARCHAR",
            "array": "JSONB",
            "object": "JSONB",
            "datetime": "TIMESTAMP",
            "date": "DATE",
            "time": "TIME",
            "uuid": "UUID",
            "email": "VARCHAR(255)",
            "url": "VARCHAR(500)",
            "phone": "VARCHAR(20)",
            "ipv4": "INET",
            "json": "JSONB",
        },
        "mysql": {
            "null": "TEXT",
            "boolean": "TINYINT(1)",
            "integer": "INT",
            "float": "DOUBLE",
            "string": "VARCHAR",
            "array": "JSON",
            "object": "JSON",
            "datetime": "DATETIME",
            "date": "DATE",
            "time": "TIME",
            "uuid": "CHAR(36)",
            "email": "VARCHAR(255)",
            "url": "VARCHAR(500)",
            "phone": "VARCHAR(20)",
            "ipv4": "VARCHAR(45)",
            "json": "JSON",
        },
        "sqlserver": {
            "null": "NVARCHAR(MAX)",
            "boolean": "BIT",
            "integer": "INT",
            "float": "FLOAT",
            "string": "NVARCHAR",
            "array": "NVARCHAR(MAX)",
            "object": "NVARCHAR(MAX)",
            "datetime": "DATETIME2",
            "date": "DATE",
            "time": "TIME",
            "uuid": "UNIQUEIDENTIFIER",
            "email": "NVARCHAR(255)",
            "url": "NVARCHAR(500)",
            "phone": "NVARCHAR(20)",
            "ipv4": "NVARCHAR(45)",
            "json": "NVARCHAR(MAX)",
        },
        "mongodb": {
            "null": "null",
            "boolean": "bool",
            "integer": "int",
            "float": "double",
            "string": "string",
            "array": "array",
            "object": "object",
            "datetime": "date",
            "date": "date",
            "time": "string",
            "uuid": "string",
            "email": "string",
            "url": "string",
            "phone": "string",
            "ipv4": "string",
            "json": "object",
        },
    }

    @classmethod
    def get_mapping(cls, target: str) -> dict:
        """Get type mapping for target database."""
        if target not in cls.MAPPINGS:
            raise ValueError(f"Unknown target: {target}. Available: {list(cls.MAPPINGS.keys())}")
        return cls.MAPPINGS[target]

    @classmethod
    def map_type(cls, inferred_type: str, target: str, max_length: int = 255) -> str:
        """Map inferred type to target database type."""
        mapping = cls.get_mapping(target)
        base_type = mapping.get(inferred_type, "TEXT")

        if base_type == "VARCHAR" and max_length > 0:
            return f"VARCHAR({max_length})"

        return base_type

    @classmethod
    def optimize_integer_range(cls, min_val: int, max_val: int, target: str) -> str:
        """Optimize integer type based on range for target database."""
        if target == "postgresql":
            if 0 <= max_val <= 255:
                return "SMALLINT"
            elif -32768 <= min_val <= 32767 and -8388608 <= max_val <= 8388607:
                return "INTEGER"
            elif -2147483648 <= min_val <= 2147483647:
                return "INTEGER"
            else:
                return "BIGINT"
        elif target == "mysql":
            if 0 <= max_val <= 255:
                return "TINYINT UNSIGNED"
            elif -128 <= min_val <= 127:
                return "TINYINT"
            elif -32768 <= min_val <= 32767:
                return "SMALLINT"
            elif -8388608 <= min_val <= 8388607:
                return "MEDIUMINT"
            elif -2147483648 <= min_val <= 2147483647:
                return "INT"
            else:
                return "BIGINT"
        elif target == "sqlserver":
            if 0 <= max_val <= 255:
                return "TINYINT"
            elif -32768 <= min_val <= 32767:
                return "SMALLINT"
            elif -2147483648 <= min_val <= 2147483647:
                return "INT"
            else:
                return "BIGINT"
        elif target == "sqlite":
            return "INTEGER"

        return "INTEGER"
